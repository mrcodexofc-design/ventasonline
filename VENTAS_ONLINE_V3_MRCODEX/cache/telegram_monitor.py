from __future__ import annotations

import asyncio
import argparse
import contextlib
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import (
    ADMIN_MENTIONS,
    API_HASH,
    API_ID,
    COOLDOWN_SECONDS,
    ENABLE_HISTORY,
    ENABLE_TRENDS,
    GROUPING_WINDOW_SECONDS,
    MIN_SCORE,
    SESSION_NAME,
    SESSION_PATH,
    USER_TO_MENTION,
    destination_value,
    telegram_session_value,
)
from cache.filters import MessageFilter
from cache.formatter import format_alert, format_error, format_startup_messages, format_statistics, format_trends, preview_alert_message
from cache.history import HistoryStore
from cache.lead_engine import LeadResult, analyze_lead, should_ping
from cache.statistics import StatisticsStore
from cache.trend_detector import TrendDetector
from cache.utils import build_logger, ensure_runtime_files


LOGGER = build_logger("monitor", "errors")
LEADS_LOGGER = build_logger("leads", "leads")
VIP_LOGGER = build_logger("vip", "vip")
STATS_LOGGER = build_logger("stats", "stats")


def configure_console_output() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


@dataclass
class AlertBatch:
    user_id: int
    name: str
    username: str | None
    group: str
    group_ref: int | str
    message_id: int | None
    result: LeadResult
    last_text: str
    history: dict[str, object] | None
    count: int = 1
    grouped_messages: list[str] = field(default_factory=list)
    last_seen: float = 0.0
    initial_sent: bool = False


class AlertBatcher:
    def __init__(self, window_seconds: int) -> None:
        self.window_seconds = window_seconds
        self._batches: dict[str, AlertBatch] = {}

    def _key(self, user_id: int, group: str, result: LeadResult) -> str:
        services = ",".join(sorted(result.services or ["general"]))
        return f"{group}:{user_id}:{services}:{result.category}"

    def add(
        self,
        *,
        user_id: int,
        name: str,
        username: str | None,
        group: str,
        group_ref: int | str,
        message_id: int | None,
        text: str,
        result: LeadResult,
        history: dict[str, object] | None,
        now_value: float,
    ) -> tuple[AlertBatch | None, AlertBatch | None]:
        if self.window_seconds <= 0:
            created = AlertBatch(
                user_id=user_id,
                name=name,
                username=username,
                group=group,
                group_ref=group_ref,
                message_id=message_id,
                result=result,
                last_text=text,
                history=history,
                grouped_messages=[text],
                last_seen=now_value,
            )
            return created, None

        key = self._key(user_id, group, result)
        batch = self._batches.get(key)
        if batch and now_value - batch.last_seen <= self.window_seconds:
            batch.count += 1
            batch.last_text = text
            batch.grouped_messages.append(text)
            batch.last_seen = now_value
            batch.message_id = message_id
            if result.score > batch.result.score:
                batch.result = result
                batch.history = history
            return None, None

        completed = None
        if batch:
            completed = batch

        created = AlertBatch(
            user_id=user_id,
            name=name,
            username=username,
            group=group,
            group_ref=group_ref,
            message_id=message_id,
            result=result,
            last_text=text,
            history=history,
            grouped_messages=[text],
            last_seen=now_value,
        )
        self._batches[key] = created
        return created, completed

    def flush_ready(self, now_value: float) -> list[AlertBatch]:
        if self.window_seconds <= 0:
            return []
        ready: list[AlertBatch] = []
        expired = [key for key, batch in self._batches.items() if now_value - batch.last_seen > self.window_seconds]
        for key in expired:
            batch = self._batches.pop(key)
            if batch.count > 1 or not batch.initial_sent:
                ready.append(batch)
        return ready

    def flush_all(self) -> list[AlertBatch]:
        items = list(self._batches.values())
        self._batches.clear()
        return items


class MonitorApp:
    """Application service that validates, scores, batches and forwards alerts."""

    def __init__(self) -> None:
        ensure_runtime_files()
        self.filter_engine = MessageFilter(COOLDOWN_SECONDS)
        self.history = HistoryStore.from_default()
        self.statistics = StatisticsStore.from_default()
        self.trends = TrendDetector.from_default()
        self.batcher = AlertBatcher(GROUPING_WINDOW_SECONDS)
        self.paused = False

    def process_message(
        self,
        *,
        user_id: int,
        name: str,
        username: str | None,
        group: str,
        group_ref: int | str,
        message_id: int | None,
        text: str,
        now_value: float,
    ) -> list[str]:
        validation = self.filter_engine.validate_message(user_id, group_ref, text)
        if not validation.allowed:
            LOGGER.info("Ignorado [%s] %s", validation.reason, text)
            return []

        history = self.history.summary(user_id) if ENABLE_HISTORY else None
        result = analyze_lead(validation.cleaned_text, history=history, username=username)
        if result.score < MIN_SCORE:
            LOGGER.info("Bajo score [%s] %s", result.score, text)
            return []

        updated_history = self.history.register_lead(
            user_id=user_id,
            name=name,
            username=username,
            group=group,
            services=result.services,
            score=result.score,
            message=validation.cleaned_text,
            level=result.level,
            category=result.category,
        )
        stats = self.statistics.register_lead(
            services=result.services,
            group=group,
            username=username,
            level=result.level,
        )
        if ENABLE_TRENDS:
            self.trends.register(result.services, group)

        created, pending = self.batcher.add(
            user_id=user_id,
            name=name,
            username=username,
            group=group,
            group_ref=group_ref,
            message_id=message_id,
            text=validation.cleaned_text,
            result=result,
            history=updated_history,
            now_value=now_value,
        )
        outputs: list[str] = []
        if created is not None:
            created.initial_sent = True
            outputs.append(self._emit_batch(created, grouped=False))
        if pending is not None:
            outputs.append(self._emit_batch(pending))

        ready_batches = self.batcher.flush_ready(now_value)
        outputs.extend(self._emit_batch(batch) for batch in ready_batches)

        LOGGER.info("Lead registrado: %s", stats.get("total_leads", 0))
        STATS_LOGGER.info(self.statistics.summary_line())
        return outputs

    def _emit_batch(self, batch: AlertBatch, *, grouped: bool = True) -> str:
        alert = format_alert(
            result=batch.result,
            name=batch.name,
            username=batch.username,
            user_id=batch.user_id,
            group=batch.group,
            group_id=batch.group_ref,
            message_id=batch.message_id,
            text=batch.last_text,
            history=batch.history,
            occurrences=batch.count if grouped else 1,
            grouped_messages=batch.grouped_messages if grouped else [],
        )
        LEADS_LOGGER.info(alert)
        if should_ping(batch.result):
            VIP_LOGGER.info(alert)
        return alert

    def flush_ready(self, now_value: float) -> list[str]:
        return [self._emit_batch(batch) for batch in self.batcher.flush_ready(now_value)]

    def flush(self) -> list[str]:
        return [self._emit_batch(batch) for batch in self.batcher.flush_all()]

    def report(self) -> dict[str, str]:
        return {
            "statistics": format_statistics(self.statistics.snapshot()),
            "trends": format_trends(self.trends.top_services()),
        }

    def format_status(self, destination: int | str) -> str:
        state = "Pausado" if self.paused else "Activo"
        return (
            "<b>ESTADO DEL BOT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Estado: <b>{state}</b>\n"
            f"Destino: <code>{destination}</code>\n"
            f"Admin Asignado: <b>{USER_TO_MENTION}</b>\n"
            f"Cooldown: <code>{COOLDOWN_SECONDS}s</code>\n"
            f"Agrupacion: <code>{GROUPING_WINDOW_SECONDS}s</code>\n"
            f"Historial: <b>{'ON' if ENABLE_HISTORY else 'OFF'}</b>\n"
            f"Tendencias: <b>{'ON' if ENABLE_TRENDS else 'OFF'}</b>"
        )

    def format_help(self) -> str:
        return (
            "<b>COMANDOS DISPONIBLES</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "/help - Muestra esta ayuda y para que sirve cada comando.\n"
            "/status - Enseña el estado actual del bot, destino y modos activos.\n"
            "/stats - Muestra estadisticas acumuladas de leads detectados.\n"
            "/trends - Muestra tendencias de servicios detectados.\n"
            "/test - Envia una alerta demo para ver el formato final.\n"
            "/pause - Pausa la deteccion de nuevos leads.\n"
            "/resume - Reanuda la deteccion despues de una pausa."
        )

    async def handle_command(self, client: Any, event: Any, destination: int | str) -> bool:
        raw_text = (event.raw_text or "").strip()
        if not raw_text.startswith("/"):
            return False

        command = raw_text.split()[0].lower()
        if "@" in command:
            command = command.split("@", 1)[0]

        if command == "/help":
            await event.reply(self.format_help(), parse_mode="html", link_preview=False)
            return True
        if command == "/status":
            await event.reply(self.format_status(destination), parse_mode="html", link_preview=False)
            return True
        if command == "/stats":
            await event.reply(format_statistics(self.statistics.snapshot()), parse_mode="html", link_preview=False)
            return True
        if command == "/trends":
            await event.reply(format_trends(self.trends.top_services()), parse_mode="html", link_preview=False)
            return True
        if command == "/test":
            await event.reply(preview_alert_message(), parse_mode="html", link_preview=False)
            return True
        if command == "/pause":
            self.paused = True
            await event.reply("<b>Bot pausado.</b>\nNo se detectaran nuevos leads hasta usar /resume.", parse_mode="html", link_preview=False)
            return True
        if command == "/resume":
            self.paused = False
            await event.reply("<b>Bot reanudado.</b>\nLa deteccion de leads vuelve a estar activa.", parse_mode="html", link_preview=False)
            return True

        await event.reply("Comando no reconocido. Usa /help para ver la lista.", parse_mode="html", link_preview=False)
        return True

    async def _resolve_destination(self, client: Any, target: int | str) -> Any:
        candidates: list[int | str] = [target]
        if isinstance(target, int) and target < 0:
            abs_value = str(abs(target))
            if not abs_value.startswith("100"):
                candidates.append(int(f"-100{abs_value}"))

        last_error: Exception | None = None
        for candidate in candidates:
            try:
                return await client.get_input_entity(candidate)
            except Exception as exc:
                last_error = exc

        if isinstance(target, str):
            normalized = target.strip().lower()
            async for dialog in client.iter_dialogs():
                dialog_name = (dialog.name or "").strip().lower()
                if dialog_name == normalized:
                    return await client.get_input_entity(dialog.entity)

        if last_error is None:
            raise RuntimeError(f"No se pudo resolver el destino {target!r}")
        raise RuntimeError(f"No se pudo resolver el destino {target!r}: {last_error}")

    async def run_telegram(self) -> None:
        try:
            from telethon import TelegramClient, events
        except ImportError as exc:
            LOGGER.error("Telethon no instalado: %s", exc)
            print("Telethon no esta instalado. El monitor quedo en modo verificacion.")
            return

        if not API_ID or not API_HASH:
            print("Faltan API_ID o API_HASH. El monitor quedo en modo verificacion.")
            return

        session_value = telegram_session_value()
        client = TelegramClient(session_value, API_ID, API_HASH)
        destination = destination_value()

        async with client:
            resolved_destination = await self._resolve_destination(client, destination)
            destination_peer_id = await client.get_peer_id(resolved_destination)
            loop = asyncio.get_running_loop()
            startup_messages = format_startup_messages(str(destination), COOLDOWN_SECONDS, GROUPING_WINDOW_SECONDS)
            for startup_message in startup_messages:
                await client.send_message(
                    resolved_destination,
                    startup_message,
                    parse_mode="html",
                    link_preview=False,
                )

            async def flush_loop() -> None:
                if GROUPING_WINDOW_SECONDS <= 0:
                    return
                while True:
                    await asyncio.sleep(min(GROUPING_WINDOW_SECONDS, 5))
                    outputs = self.flush_ready(loop.time())
                    for output in outputs:
                        await client.send_message(
                            resolved_destination,
                            output,
                            parse_mode="html",
                            link_preview=False,
                        )

            my_user = await client.get_me()
            my_id = my_user.id
            LOGGER.info("Conectado como %s (ID: %s)", getattr(my_user, "first_name", "User"), my_id)

            @client.on(events.NewMessage)
            async def handle(event: Any) -> None:
                try:
                    sender = await event.get_sender()
                    chat = await event.get_chat()
                    text = (event.raw_text or "").strip()
                    current_peer_id = await client.get_peer_id(chat)

                    if current_peer_id == destination_peer_id:
                        handled = await self.handle_command(client, event, destination)
                        if handled:
                            return
                        return

                    if event.is_private:
                        if text.startswith("/"):
                            handled = await self.handle_command(client, event, destination)
                            if handled:
                                return
                        return

                    if self.paused:
                        return

                    # Mensajes de grupos para monitoreo de leads
                    group_name = getattr(chat, "title", None) or getattr(chat, "username", None) or str(getattr(chat, "id", "desconocido"))
                    group_ref = getattr(chat, "username", None) or getattr(chat, "id", group_name)
                    outputs = self.process_message(
                        user_id=int(getattr(sender, "id", 0)),
                        name=getattr(sender, "first_name", None) or getattr(sender, "title", None) or "Sin nombre",
                        username=getattr(sender, "username", None),
                        group=group_name,
                        group_ref=group_ref,
                        message_id=getattr(event.message, "id", None),
                        text=text,
                        now_value=asyncio.get_running_loop().time(),
                    )
                    if outputs:
                        for output in outputs:
                            await client.send_message(
                                resolved_destination,
                                output,
                                parse_mode="html",
                                link_preview=False,
                            )
                except Exception as exc:
                    LOGGER.exception("Error procesando mensaje: %s", exc)

            flush_task = asyncio.create_task(flush_loop())
            print("Monitor Telegram activo.")
            try:
                await client.run_until_disconnected()
            finally:
                flush_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await flush_task


def self_check() -> dict[str, object]:
    app = MonitorApp()
    report = app.report()
    session_source = telegram_session_value()
    session_exists = Path(f"{session_source}.session").exists()
    return {
        "config_ok": bool(SESSION_NAME),
        "api_id_configured": bool(API_ID),
        "api_hash_configured": bool(API_HASH),
        "session_source": session_source,
        "session_exists": session_exists,
        "destination_target": str(destination_value()),
        "cooldown_seconds": COOLDOWN_SECONDS,
        "grouping_window_seconds": GROUPING_WINDOW_SECONDS,
        "history_enabled": ENABLE_HISTORY,
        "trends_enabled": ENABLE_TRENDS,
        "admin_mentions": ", ".join(value for value in ADMIN_MENTIONS if value),
        "statistics_preview": report["statistics"],
        "trends_preview": report["trends"],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Telegram monitor para leads de ventas.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run", action="store_true", help="Inicia el monitoreo real de Telegram.")
    mode.add_argument("--check", action="store_true", help="Ejecuta solo el diagnostico local.")
    return parser


def _print_status(status: dict[str, object]) -> None:
    print("Self-check OK")
    for key, value in status.items():
        print(f"{key}: {value}")


def main() -> int:
    try:
        configure_console_output()
        parser = _build_parser()
        args = parser.parse_args()
        if args.run:
            asyncio.run(MonitorApp().run_telegram())
            return 0

        status = self_check()
        _print_status(status)
        return 0
    except Exception as exc:
        logging.getLogger(__name__).exception("Fallo en self-check")
        print(format_error(str(exc)))
        return 1


__all__ = ["MonitorApp", "main", "self_check"]

from __future__ import annotations

import html
from datetime import datetime

from config import ADMIN_MENTIONS, PROFILE_LINK
from cache.lead_engine import LeadResult


DIVIDER = "━━━━━━━━━━━━━━━━━━━━"


def now() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def profile(user_id: int) -> str:
    return PROFILE_LINK.format(user_id=user_id)


def admin_mentions() -> str:
    mentions = [value.strip() for value in ADMIN_MENTIONS if value and value.strip() and value.strip() != "@"]
    return ", ".join(mentions) if mentions else "@mrcodexofc"


def service_label(name: str) -> str:
    labels = {
        "hbo_max": "HBO Max",
        "prime_video": "Prime Video",
        "youtube_music": "YouTube Music",
        "medical_leave": "Descanso medico",
        "medical_prescription": "Receta medica",
        "medical_certificate": "Certificado medico",
        "line_drop": "Tumba linea",
    }
    if name in labels:
        return labels[name]
    return name.replace("_", " ").title()


def escape(value: object) -> str:
    return html.escape(str(value))


def group_link(group_id: int | str | None, message_id: int | None) -> str | None:
    if isinstance(group_id, str):
        handle = group_id.strip().lstrip("@")
        if handle:
            if message_id:
                return f"https://t.me/{handle}/{message_id}"
            return f"https://t.me/{handle}"
        return None

    if isinstance(group_id, int):
        normalized = str(abs(group_id))
        if normalized.startswith("100"):
            normalized = normalized[3:]
        if message_id:
            return f"tg://privatepost?channel={normalized}&post={message_id}&single"
        return f"tg://resolve?domain=c/{normalized}"

    return None


def profile_anchor(name: str, user_id: int, username: str | None) -> str:
    safe_name = escape(name)
    if username:
        handle = username.lstrip("@")
        return f'<a href="https://t.me/{escape(handle)}">{safe_name}</a>'
    return f'<a href="{escape(profile(user_id))}">{safe_name}</a>'


def username_label(username: str | None, user_id: int) -> str:
    if username:
        handle = username.lstrip("@")
        return f'<a href="https://t.me/{escape(handle)}">@{escape(handle)}</a>'
    return f'<a href="{escape(profile(user_id))}">Sin username | abrir perfil</a>'


def level_title(result: LeadResult) -> str:
    if result.level == "VIP":
        return "LEAD DETECTADO | VIP"
    if result.hot_lead or result.score >= 85:
        return "LEAD DETECTADO | ALTA"
    if result.score >= 70:
        return "LEAD DETECTADO | MEDIA"
    return "LEAD DETECTADO | BAJA"


def services_line(result: LeadResult) -> str:
    if not result.services:
        return "GENERAL"
    return " + ".join(service_label(service).upper() for service in result.services[:4])


def format_alert(
    *,
    result: LeadResult,
    name: str,
    username: str | None,
    user_id: int,
    group: str,
    group_id: int | str | None,
    message_id: int | None,
    text: str,
    history: dict[str, object] | None = None,
    occurrences: int = 1,
    grouped_messages: list[str] | None = None,
) -> str:
    del history
    del grouped_messages

    compact_grouped = ""
    if occurrences > 1:
        compact_grouped = f"\n🔁 <b>Agrupados:</b> <b>{escape(occurrences)}</b>"

    compact_admin = ""
    if result.level == "VIP" or result.hot_lead:
        compact_admin = f"\n🚨 <b>Admin:</b> <b>{escape(admin_mentions())}</b>"

    group_href = group_link(group_id, message_id)
    group_line = f"📍 <b>Grupo:</b> <b>{escape(group)}</b>"
    link_line = ""
    if group_href:
        group_line = f'📍 <b>Grupo:</b> <a href="{escape(group_href)}"><b>{escape(group)}</b></a>'
        link_line = f'\n🔗 <b>Link mensaje:</b> <a href="{escape(group_href)}">Abrir pedido</a>'

    return (
        f"👀 <b>{escape(level_title(result))}</b>\n"
        f"{DIVIDER}\n"
        f"📦 <b>{escape(services_line(result))}</b>\n"
        f"🎯 <b>{escape(result.category)}</b> | Score <b>{escape(result.score)}/100</b> | Prob. <b>{escape(result.probability)}%</b>\n"
        f"👤 {profile_anchor(name, user_id, username)} | {username_label(username, user_id)}\n"
        f'🆔 <b>TGID:</b> <a href="{escape(profile(user_id))}">{escape(user_id)}</a>\n'
        f'🔓 <b>Perfil directo:</b> <a href="{escape(profile(user_id))}">Abrir perfil</a>\n'
        f"{group_line}"
        f"{link_line}\n"
        f"💬 <b>Texto:</b>\n"
        f"{escape(text)}"
        f"{compact_grouped}"
        f"{compact_admin}\n\n"
        f"🕒 <b>Hora:</b> <code>{escape(now())}</code>"
    )


def format_error(error: str) -> str:
    return (
        "⚠️ <b>ERROR DEL MONITOR</b>\n"
        f"{DIVIDER}\n"
        f"🛠 <b>Detalle:</b> {escape(error)}\n"
        f"🕒 <b>Hora:</b> <code>{escape(now())}</code>"
    )


def format_statistics(stats: dict[str, object]) -> str:
    return (
        "📈 <b>ESTADISTICAS</b>\n"
        f"{DIVIDER}\n"
        f"• <b>Leads totales:</b> {escape(stats.get('total_leads', 0))}\n"
        f"• <b>VIP detectados:</b> {escape(stats.get('vip_detected', 0))}\n"
        f"• <b>Leads hoy:</b> {escape(stats.get('today_leads', 0))}\n"
        f"• <b>Usuarios recurrentes:</b> {escape(stats.get('recurrent_users', 0))}\n"
        f"• <b>Servicios activos:</b> {escape(stats.get('active_services', 0))}\n"
        f"• <b>Grupos activos:</b> {escape(stats.get('active_groups', 0))}"
    )


def format_trends(trends: dict[str, int]) -> str:
    if not trends:
        return f"📊 <b>TENDENCIAS</b>\n{DIVIDER}\n<i>Sin datos todavia</i>"

    body = "\n".join(
        f"• <b>{escape(service_label(service))}:</b> {escape(count)}"
        for service, count in sorted(trends.items(), key=lambda item: item[1], reverse=True)
    )
    return f"📊 <b>TENDENCIAS</b>\n{DIVIDER}\n{body}"


def preview_alert_message() -> str:
    preview_result = LeadResult(
        score=92,
        probability=94,
        confidence=88,
        level="ALTO",
        category="COMPRADOR",
        services=["hbo_max", "netflix"],
        reasons=[
            "Servicios detectados: hbo_max, netflix (+36)",
            "Compra: alguien vende (+34)",
            "Patron comercial: prefijo + servicio (+28)",
            "Patron comercial: oferta + servicio (+18)",
        ],
        hot_lead=True,
    )
    preview_alert = format_alert(
        result=preview_result,
        name="Cliente Demo",
        username="cliente_demo",
        user_id=8632371826,
        group="Causa Market PE",
        group_id="causamarketpe",
        message_id=321,
        text="alguien vende perfil de hbo max y netflix ?",
        history={"messages": 2, "best_score": 92, "vip": False},
        occurrences=1,
        grouped_messages=["alguien vende perfil de hbo max y netflix ?"],
    )
    return preview_alert


def format_startup_messages(destination_target: str, cooldown_seconds: int, grouping_window_seconds: int) -> list[str]:
    preview_alert = preview_alert_message()

    startup = (
        "🚀 <b>BOT EN FUNCIONAMIENTO</b>\n"
        f"{DIVIDER}\n"
        f"✅ <b>Estado:</b> <b>Monitoreo activo</b>\n"
        f"🎯 <b>Destino:</b> <code>{escape(destination_target)}</code>\n"
        f"⏳ <b>Cooldown:</b> <code>{escape(cooldown_seconds)}s</code>\n"
        f"📚 <b>Agrupacion:</b> <code>{escape(grouping_window_seconds)}s</code>\n"
        f"📣 <b>Admin:</b> <b>{escape(admin_mentions())}</b>\n"
        f"🕒 <b>Inicio:</b> <code>{escape(now())}</code>"
    )
    preview_header = f"🧪 <b>ASI SE VERAN TUS ALERTAS</b>\n{DIVIDER}"
    ready = "🔥 <b>Sistema listo para detectar clientes reales</b>"
    return [startup, preview_header, preview_alert, ready]


__all__ = ["format_alert", "format_error", "format_startup_messages", "format_statistics", "format_trends", "preview_alert_message"]

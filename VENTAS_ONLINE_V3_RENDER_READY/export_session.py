#!/usr/bin/env python3
"""
Script para exportar la sesion de Telegram (.session) a StringSession.
La cadena generada (SESSION_STRING) se utiliza en Render para que el bot
mantenga la conexion sin necesidad de subir archivos .session a GitHub.
"""

from pathlib import Path
from telethon.sessions import SQLiteSession, StringSession
from config import SESSION_NAME, SESSION_PATH, telegram_session_value


def export_session() -> None:
    session_source = telegram_session_value()
    session_candidates = [
        Path(f"{session_source}.session"),
        Path(session_source),
        Path("clenaerdev2.session"),
        Path("telegram_monitor_session.session"),
    ]

    target_file: Path | None = None
    for cand in session_candidates:
        if cand.exists():
            target_file = cand
            break

    if not target_file:
        print("[!] No se encontro ningun archivo .session local.")
        print("    Asegurate de haber iniciado sesion localmente al menos una vez.")
        return

    try:
        sqlite = SQLiteSession(str(target_file.with_suffix("")))
        str_session = StringSession()
        str_session._auth_key = sqlite.auth_key
        str_session._server_address = sqlite.server_address
        str_session._port = sqlite.port
        val = str_session.save()
        if val:
            print("\n" + "=" * 70)
            print("  TU SESSION_STRING PARA CONFIGURAR EN RENDER:")
            print("=" * 70)
            print(val)
            print("=" * 70)
            print("\nInstrucciones para Render:")
            print("1. En Render Dashboard -> Tu Web Service o Background Worker")
            print("2. Ve a la pestana 'Environment'")
            print("3. Agrega una nueva variable llamada: SESSION_STRING")
            print("4. Pega el valor mostrado arriba.")
            print("=" * 70 + "\n")
        else:
            print("[!] La sesion parece estar vacia o no autenticada.")
    except Exception as exc:
        print(f"[!] Error al exportar la sesion: {exc}")


if __name__ == "__main__":
    export_session()

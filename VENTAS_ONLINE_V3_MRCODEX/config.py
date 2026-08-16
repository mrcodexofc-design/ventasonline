from __future__ import annotations

import os
from pathlib import Path
from typing import Final

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = LOGS_DIR / "data"

ERROR_LOG_FILE = LOGS_DIR / "errors.log"
LEADS_LOG_FILE = LOGS_DIR / "leads.log"
VIP_LOG_FILE = LOGS_DIR / "vip.log"
STATS_LOG_FILE = LOGS_DIR / "stats.log"
HISTORY_FILE = DATA_DIR / "history.json"
STATS_FILE = DATA_DIR / "stats.json"
TRENDS_FILE = DATA_DIR / "trends.json"

for directory in (LOGS_DIR, DATA_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "si"}


def env_csv(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_str(name: str, default: str = "") -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip() or default


SESSION_NAME = env_str("SESSION_NAME", "telegram_monitor_session")
SESSION_PATH = env_str("SESSION_PATH", "")
API_ID = env_int("API_ID", 0)
API_HASH = env_str("API_HASH", "")
DESTINATION_GROUP = env_int("DESTINATION_GROUP", -5041737152)
DESTINATION_TARGET = env_str("DESTINATION_TARGET", str(DESTINATION_GROUP))
USER_TO_MENTION = env_str("USER_TO_MENTION", "@mrcodexofc")
ADMIN_MENTIONS = env_csv("ADMIN_MENTIONS", USER_TO_MENTION)

MIN_SCORE = env_int("MIN_SCORE", 70)
HIGH_SCORE = env_int("HIGH_SCORE", 85)
VIP_SCORE = env_int("VIP_SCORE", 95)
MIN_COMMERCIAL_SCORE = env_int("MIN_COMMERCIAL_SCORE", 26)

MIN_WORDS = env_int("MIN_WORDS", 2)
MIN_CHARACTERS = env_int("MIN_CHARACTERS", 8)
COOLDOWN_SECONDS = env_int("COOLDOWN_SECONDS", 300)
GROUPING_WINDOW_SECONDS = env_int("GROUPING_WINDOW_SECONDS", 120)

ENABLE_HISTORY = env_bool("ENABLE_HISTORY", True)
ENABLE_TRENDS = env_bool("ENABLE_TRENDS", True)
ENABLE_ANTISPAM = env_bool("ENABLE_ANTISPAM", True)
SALES_ONLY_MODE = env_bool("SALES_ONLY_MODE", True)
BUYERS_ONLY_MODE = env_bool("BUYERS_ONLY_MODE", False)
WHITELIST_TERMS = tuple(
    env_csv(
        "WHITELIST_TERMS",
        "alguien,busco,compro,necesito,quiero,deseo,proveedor,stock,disponible,vende,vendo,tiene,tengo,cuenta,cuentas,perfil,perfiles,pantalla,pantallas,netflix,hbo max,max,spotify,chatgpt,gemini,canva,yape,plin,tunki,dox,reniec,sunarp,receta medica,descanso medico,tumba linea,iptv,interno,internos,billetera,billeteras,cuenta bancaria,cuentas bancarias,fono,numero,numero de telefono,chip,binance,usdt",
    )
)

COMMERCIAL_REQUEST_PREFIXES = (
    "alguien",
    "quien",
    "busco",
    "necesito",
    "quiero",
    "compro",
    "deseo",
    "ando buscando",
    "me interesa",
)

COMMERCIAL_SUPPLY_TERMS = (
    "vende",
    "vendo",
    "venta",
    "ofrece",
    "ofrezco",
    "tiene",
    "tengo",
    "disponible",
    "stock",
    "proveedor",
    "trabaja",
    "hace",
    "saca",
    "consigue",
    "activa",
    "recupera",
    "tumba",
    "baja",
    "pasa",
)

COMMERCIAL_OBJECT_TERMS = (
    "proveedor",
    "info",
    "datos",
    "foto",
    "fotos",
    "selfie",
    "rostro",
    "cara",
    "facial",
    "reconocimiento facial",
    "biometria",
    "biometrico",
    "numero",
    "numero",
    "celular",
    "telefono",
    "fono",
    "chip",
    "fisico",
    "billetera",
    "billeteras",
    "bancaria",
    "bancarias",
    "banca",
    "bancas",
    "agora",
    "plin",
    "tunki",
    "ligo",
    "culqi",
    "interbank",
    "bcp",
    "bbva",
    "scotia",
    "binance pay",
    "izipay",
    "caja arequipa",
    "panda",
    "pago efectivo",
    "lista blanca",
    "registra",
    "registrar",
    "cuenta",
    "cuentas",
    "cuenta bancaria",
    "cuentas bancarias",
    "perfil",
    "perfiles",
    "pantalla",
    "pantallas",
    "servicio",
    "servicios",
    "stock",
    "dox",
    "reniec",
    "sunarp",
    "osiptel",
    "descanso",
    "receta",
    "certificado",
    "linea",
    "lineas",
    "iptv",
    "chatgpt",
    "canva",
)

BUY_PHRASES = {
    "busco proveedor": 40,
    "proveedor": 28,
    "precio": 18,
    "cuanto": 16,
    "cuanto esta": 18,
    "cuanto sale": 18,
    "cuanto cuesta": 22,
    "precio por mayor": 26,
    "precio al por mayor": 28,
    "precio por unidad": 20,
    "necesito": 18,
    "necesito proveedor": 34,
    "necesito urgente": 24,
    "urgente": 22,
    "compro": 28,
    "quiero pedir": 24,
    "quiero comprar": 32,
    "deseo comprar": 26,
    "quiero adquirir": 24,
    "me interesa comprar": 26,
    "pago": 14,
    "pago hoy": 22,
    "pago de una": 22,
    "te pago hoy": 24,
    "al por mayor": 35,
    "alguien vende": 34,
    "alguien que venda": 34,
    "alguien tiene": 24,
    "alguien ofrece": 24,
    "alguien netflix": 28,
    "alguien hbo": 28,
    "alguien hbo max": 34,
    "alguien spotify": 26,
    "alguien disney": 26,
    "alguien prime": 24,
    "alguien crunchyroll": 24,
    "alguien vende agora": 34,
    "alguien vende plin": 34,
    "alguien vende tunki": 34,
    "alguien vende ligo": 34,
    "alguien vende culqi": 34,
    "alguien vende interbank": 36,
    "alguien vende bcp": 36,
    "alguien vende bbva": 36,
    "alguien vende scotia": 36,
    "alguien vende binance pay": 38,
    "alguien vende izipay": 38,
    "alguien vende caja arequipa": 38,
    "alguien vende panda": 34,
    "alguien vende pago efectivo": 38,
    "alguien vende bancas": 34,
    "alguien registra a lista blanca": 40,
    "alguien registra lista blanca": 40,
    "quien vende": 32,
    "quien tiene": 20,
    "quien ofrece": 20,
    "quien dox": 34,
    "quien doxea": 34,
    "quien saca dox": 36,
    "quien tiene dox": 34,
    "quien tumba linea": 34,
    "quien tumba lineas": 34,
    "quien baja linea": 30,
    "quien da de baja": 28,
    "stock": 16,
    "tienes stock": 22,
    "hay stock": 18,
    "disponible": 18,
    "disponibilidad": 18,
    "internos": 18,
    "comprar": 24,
    "busco": 20,
    "busco dox": 34,
    "busco doxeo": 34,
    "busco datos": 22,
    "busco reniec": 24,
    "busco info": 24,
    "busco numero": 24,
    "busco celular": 24,
    "busco chip": 24,
    "busco info de numero": 30,
    "busco info de celular": 30,
    "info de numero": 24,
    "info de celular": 24,
    "info de numero de celular": 32,
    "busco tumba linea": 34,
    "busco tumba lineas": 34,
    "busco bajar linea": 30,
    "alguien saque info": 34,
    "alguien que me saque info": 38,
    "alguien saca info": 34,
    "alguien saca info con foto": 40,
    "alguien hace reconocimiento facial": 42,
    "alguien hace biometria": 38,
    "alguien hace biometrico": 38,
    "sacar info": 28,
    "saca info": 28,
    "saca info con foto": 34,
    "reconocimiento facial": 34,
    "biometria": 28,
    "biometrico": 28,
    "numero de celular": 24,
    "chip fisico": 22,
    "agora": 22,
    "plin": 20,
    "tunki": 20,
    "ligo": 20,
    "culqi": 22,
    "interbank": 22,
    "bcp": 22,
    "bbva": 22,
    "scotia": 22,
    "binance pay": 24,
    "izipay": 24,
    "caja arequipa": 26,
    "panda": 20,
    "pago efectivo": 26,
    "bancas": 22,
    "lista blanca": 24,
    "registra lista blanca": 28,
    "cotizar": 18,
    "cotizacion": 16,
    "factura": 16,
    "boleta": 12,
    "garantia": 16,
    "entrega inmediata": 22,
    "para hoy": 18,
    "necesito para hoy": 24,
    "me sirve hoy": 18,
}

RESELLER_PHRASES = {
    "reseller": 34,
    "revender": 34,
    "reventa": 34,
    "quiero revender": 40,
    "para reventa": 36,
    "para revender": 36,
    "bulk": 30,
    "wholesale": 30,
    "api": 28,
    "panel": 28,
    "panel propio": 32,
    "panel reseller": 36,
    "mayoreo": 30,
    "por mayor": 32,
    "distribuidor": 32,
    "distribucion": 30,
    "revendedor": 36,
    "dropship": 26,
}

SELLER_PHRASES = {
    "vendo": 24,
    "vende": 20,
    "venta": 20,
    "ofrezco": 24,
    "soy proveedor": 35,
    "tengo panel": 30,
    "tengo cuentas": 24,
    "distribuyo": 28,
    "manejamos": 16,
    "te ofrezco": 24,
    "tenemos stock": 26,
    "disponemos": 20,
    "disponible": 18,
    "a la venta": 20,
}

URGENCY_PHRASES = {
    "urgente": 20,
    "ahora": 14,
    "hoy": 14,
    "inmediato": 18,
    "esta semana": 10,
    "lo antes posible": 18,
    "para ahorita": 20,
    "en este momento": 18,
    "de inmediato": 20,
    "rapidito": 14,
}

CONTEXT_PHRASES = {
    "quiero comprar": 30,
    "necesito proveedor": 40,
    "busco proveedor": 40,
    "quiero revender": 38,
    "precio por mayor": 35,
    "alguien vende netflix": 34,
    "alguien vende hbo": 30,
    "alguien vende spotify": 30,
    "alguien netflix": 24,
    "alguien hbo": 24,
    "alguien hbo max": 30,
    "alguien spotify": 22,
    "como comprar": 25,
    "donde comprar": 25,
    "aceptan yape": 12,
    "aceptan plin": 12,
    "tienen garantia": 12,
    "formas de pago": 14,
    "metodos de pago": 14,
    "aceptan usdt": 16,
    "aceptan binance": 16,
    "necesito varias cuentas": 26,
    "necesito varias unidades": 28,
    "quiero varias cuentas": 24,
    "busco mayorista": 32,
    "busco distribuidor": 32,
    "hacen entrega": 16,
    "envias hoy": 18,
    "dox actualizado": 32,
    "dox 2026": 24,
    "actualizado 2026": 18,
    "dox actualizado 2026": 36,
    "datos actualizados": 24,
    "ficha actualizada": 22,
    "tumbar linea": 26,
    "tumba linea": 28,
    "tumba lineas": 28,
    "bajar linea": 24,
    "dar de baja linea": 26,
    "linea caida": 18,
    "numero de celular": 18,
    "chip fisico": 18,
    "info de numero": 18,
    "info de numero de celular": 22,
    "saca info con foto": 24,
    "reconocimiento facial": 26,
    "biometria facial": 24,
    "agora": 18,
    "plin": 18,
    "tunki": 18,
    "ligo": 18,
    "culqi": 18,
    "interbank": 18,
    "bcp": 18,
    "bbva": 18,
    "scotia": 18,
    "binance pay": 20,
    "izipay": 20,
    "caja arequipa": 22,
    "panda": 16,
    "pago efectivo": 22,
    "banca": 18,
    "bancas": 20,
    "lista blanca": 24,
    "cuenta bancaria": 22,
    "cuentas bancarias": 24,
    "billetera": 20,
    "billeteras": 22,
}

LOW_VALUE_PHRASES = {
    "checar": 18,
    "estoy checando": 22,
    "solo checo": 25,
    "solo mirando": 25,
    "solo vengo a ver": 25,
    "estoy viendo": 18,
    "me avisan": 15,
    "informacion": 10,
    "info": 10,
    "consulta": 10,
    "cotizacion": 8,
    "quiero saber": 12,
    "como funciona": 15,
    "alguien sabe": 18,
    "que opinan": 18,
}

SERVICES = {
    "imei": {"score": 34, "keywords": ["imei", "liberar imei", "clean imei"]},
    "icloud": {"score": 34, "keywords": ["icloud", "desbloqueo icloud"]},
    "frp": {"score": 30, "keywords": ["frp", "bypass frp"]},
    "netflix": {"score": 18, "keywords": ["netflix", "pantalla netflix", "perfil netflix", "cuenta netflix", "netflix premium"]},
    "hbo_max": {"score": 18, "keywords": ["hbo max", "hbo", "max", "cuenta hbo", "pantalla hbo"]},
    "spotify": {"score": 16, "keywords": ["spotify", "spotify premium"]},
    "chatgpt": {"score": 20, "keywords": ["chatgpt", "chat gpt", "cht gpt", "chtgpt", "chatgpt plus", "gpt plus", "gpt premium"]},
    "gemini": {"score": 16, "keywords": ["gemini", "gemini pro"]},
    "yape": {"score": 16, "keywords": ["yape", "yapeo"]},
    "agora": {"score": 18, "keywords": ["agora"]},
    "plin": {"score": 16, "keywords": ["plin", "plim"]},
    "tunki": {"score": 16, "keywords": ["tunki", "tunkii"]},
    "ligo": {"score": 16, "keywords": ["ligo"]},
    "culqi": {"score": 18, "keywords": ["culqi", "kulqi"]},
    "interbank": {"score": 18, "keywords": ["interbank", "inter ban", "inter"]},
    "bcp": {"score": 18, "keywords": ["bcp"]},
    "bbva": {"score": 18, "keywords": ["bbva", "bbv4"]},
    "scotia": {"score": 18, "keywords": ["scotia", "scotiabank"]},
    "binance_pay": {"score": 20, "keywords": ["binance pay", "binancepay"]},
    "izipay": {"score": 20, "keywords": ["izipay", "izi pay"]},
    "caja_arequipa": {"score": 22, "keywords": ["caja arequipa"]},
    "panda": {"score": 16, "keywords": ["panda"]},
    "pago_efectivo": {"score": 22, "keywords": ["pago efectivo"]},
    "bancas": {"score": 18, "keywords": ["banca", "bancas"]},
    "whitelist_registry": {"score": 24, "keywords": ["lista blanca", "registra lista blanca", "registrar lista blanca"]},
    "canva": {"score": 16, "keywords": ["canva", "canva pro"]},
    "sms": {"score": 18, "keywords": ["sms", "recepcion sms"]},
    "disney": {"score": 16, "keywords": ["disney", "disney plus", "disney+"]},
    "youtube": {"score": 14, "keywords": ["youtube premium", "youtube"]},
    "iptv": {"score": 18, "keywords": ["iptv", "tv premium"]},
    "prime_video": {"score": 16, "keywords": ["prime video", "amazon prime", "prime"]},
    "crunchyroll": {"score": 16, "keywords": ["crunchyroll", "crunchy"]},
    "paramount": {"score": 14, "keywords": ["paramount", "paramount plus"]},
    "vix": {"score": 14, "keywords": ["vix", "vix premium"]},
    "capcut": {"score": 16, "keywords": ["capcut", "capcut pro"]},
    "youtube_music": {"score": 14, "keywords": ["youtube music", "yt music"]},
    "medical_leave": {"score": 34, "keywords": ["descanso medico", "descanso médico", "certificado medico", "certificado médico"]},
    "medical_prescription": {"score": 30, "keywords": ["receta medica", "receta médica", "prescripcion medica", "prescripción médica"]},
    "medical_certificate": {"score": 30, "keywords": ["constancia medica", "constancia médica", "certificado de salud"]},
    "antecedentes": {"score": 24, "keywords": ["antecedentes", "certijoven", "certiadulto"]},
    "dox": {"score": 30, "keywords": ["dox", "doxeo", "doxear", "doxeado", "dox actualizado", "ficha dox"]},
    "reniec": {"score": 22, "keywords": ["reniec", "ficha reniec", "datos reniec"]},
    "sunarp": {"score": 22, "keywords": ["sunarp", "partida sunarp", "vehicular sunarp"]},
    "osiptel": {"score": 20, "keywords": ["osiptel", "titularidad", "linea titular"]},
    "sentinel": {"score": 20, "keywords": ["sentinel", "riesgo sentinel", "score sentinel"]},
    "paypal": {"score": 18, "keywords": ["paypal", "saldo paypal"]},
    "binance": {"score": 18, "keywords": ["binance", "usdt", "saldo usdt"]},
    "whatsapp": {"score": 16, "keywords": ["whatsapp", "wsp", "linea whatsapp"]},
    "line_drop": {"score": 30, "keywords": ["tumba linea", "tumbar linea", "tumba lineas", "bajar linea", "dar de baja linea", "linea caida", "lineas caidas"]},
    "phone_data": {"score": 22, "keywords": ["numero de celular", "numero celular", "info de numero", "info de celular", "info de numero de celular", "celular", "telefono", "fono", "chip fisico", "chip"]},
    "bank_accounts": {"score": 24, "keywords": ["cuenta bancaria", "cuentas bancarias", "billetera", "billeteras"]},
    "facial_data": {"score": 28, "keywords": ["foto", "fotos", "selfie", "rostro", "cara", "reconocimiento facial", "biometria", "biometrico", "biometria facial", "info con foto"]},
}

REGEX_PATTERNS = {
    "precio_directo": {"pattern": r"(precio|costo|valor)\s*(por|al)?\s*(mayor|unidad)?", "score": 10},
    "metodo_pago": {"pattern": r"(yape|plin|transferencia|usdt|binance|tunki|culqi|pago\s*efectivo|izipay)", "score": 10},
    "volumen": {"pattern": r"(\d+\s*(cuentas|pantallas|perfiles|unidades))", "score": 12},
    "pedido_medico": {"pattern": r"(descanso|receta|certificado|constancia)\s+medic[ao]", "score": 16},
    "compra_directa": {"pattern": r"(busco|necesito|quiero|compro)\s+(proveedor|cuentas|pantallas|perfiles|descanso|receta|netflix|hbo)", "score": 14},
    "urgencia_compra": {"pattern": r"(urgente|ahora|hoy|inmediato).*(precio|proveedor|stock|cuenta)", "score": 14},
    "line_drop_request": {"pattern": r"(quien|busco|necesito).*(tumba|tumbar|baja|bajar).*(linea|lineas)", "score": 18},
    "dox_request": {"pattern": r"(quien|busco|necesito).*(dox|doxeo|reniec|datos).*(actualizado|2026)?", "score": 18},
    "short_service_request": {"pattern": r"(alguien|quien).*(netflix|hbo\s*max|hbo|spotify|disney|prime|crunchyroll|iptv|chat\s*gpt|chatgpt)", "score": 18},
    "phone_info_request": {"pattern": r"(alguien|quien|busco|necesito).*(info|datos|numero|celular|telefono|fono|chip)", "score": 18},
    "banking_request": {"pattern": r"(alguien|quien|busco|necesito|compro).*(billetera|cuenta\s*bancaria|cuentas\s*bancarias)", "score": 18},
    "facial_request": {"pattern": r"(alguien|quien|busco|necesito).*(foto|selfie|rostro|cara|facial|biometr)", "score": 20},
    "wallet_provider_request": {"pattern": r"(alguien|quien|busco|necesito).*(agora|plin|tunki|ligo|culqi|interbank|bcp|bbva|scotia|binance\s*pay|izipay|caja\s*arequipa|panda|pago\s*efectivo|banca|bancas|lista\s*blanca)", "score": 20},
}

IGNORE_MESSAGES = {
    "hola",
    "holaa",
    "buenas",
    "ok",
    "gracias",
    "listo",
    "dale",
    "si",
    "no",
    "xd",
    "jaja",
    "jajaja",
}

BLACKLIST_WORDS: Final[set[str]] = {"spam", "estafa", "fake", "regalo"}
VIP_USERS = {item for item in env_csv("VIP_USERS", "comprador_seguro")}

ICONS = {
    "VIP": "[VIP]",
    "HOT": "[HOT]",
    "HIGH": "[HIGH]",
    "MEDIUM": "[MEDIUM]",
    "LOW": "[LOW]",
}

PROFILE_LINK = "tg://user?id={user_id}"


def telegram_session_value() -> str:
    if SESSION_PATH:
        session_path = Path(SESSION_PATH)
        if not session_path.exists() and not Path(f"{SESSION_PATH}.session").exists():
            return SESSION_NAME
        if session_path.suffix == ".session":
            return str(session_path.with_suffix(""))
        return str(session_path)
    return SESSION_NAME


def destination_value() -> int | str:
    raw = DESTINATION_TARGET.strip()
    if not raw:
        return DESTINATION_GROUP
    try:
        return int(raw)
    except ValueError:
        return raw

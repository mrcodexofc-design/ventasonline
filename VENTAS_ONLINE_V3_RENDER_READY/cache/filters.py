from __future__ import annotations

import re
import time
from dataclasses import dataclass

from config import BUY_PHRASES, BLACKLIST_WORDS, COMMERCIAL_OBJECT_TERMS, COMMERCIAL_REQUEST_PREFIXES, COMMERCIAL_SUPPLY_TERMS, COOLDOWN_SECONDS, IGNORE_MESSAGES, MIN_CHARACTERS, MIN_WORDS, SELLER_PHRASES, SERVICES, WHITELIST_TERMS
from cache.utils import normalize_text, phrase_in_text


URL_REGEX = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
PHONE_REGEX = re.compile(r"(?:\+?\d[\d\s\-]{7,15})")
USERNAME_REGEX = re.compile(r"@([A-Za-z0-9_]{5,32})")
PRICE_REGEX = re.compile(r"(?:s/\s?\d+|usd\s?\d+|\$\s?\d+|\d+\s?usdt)", re.IGNORECASE)
LOW_VALUE_ONLY_PATTERNS = (
    "checar",
    "checando",
    "solo viendo",
    "solo miraba",
    "estoy viendo",
    "consulta",
    "info",
    "informacion",
)
COMMERCIAL_PATTERNS = (
    "vende",
    "venta",
    "vendo",
    "ofrezco",
    "disponible",
    "proveedor",
    "stock",
    "busco",
    "compro",
    "necesito",
)
SELLER_SPAM_PATTERNS = (
    "garantia y soporte",
    "garantia",
    "soporte",
    "entrega inmediata",
    "precio inbox",
    "precio al inbox",
    "mp",
    "al dm",
    "hablen al privado",
    "escriban al privado",
    "stock disponible",
    "cupos disponibles",
    "promocion",
    "promo",
    "servicio disponible",
    "perfiles disponibles",
    "pantallas disponibles",
    "bot premium",
    "calidad 4k",
    "full garantia",
)
BUYER_REQUIRED_MARKERS = (
    "busco",
    "necesito",
    "quiero",
    "deseo",
    "compro",
    "alguien",
    "quien",
    "me interesa",
    "buscando",
    "cotizar",
    "precio",
    "cuanto",
    "cuanto esta",
    "cuanto sale",
    "quien vende",
    "quien tiene",
    "quien saca",
    "quien hace",
    "quien activa",
    "alguien que venda",
    "alguien vende",
    "alguien tiene",
    "alguien saca",
    "alguien hace",
    "alguien activo",
    "deseo comprar",
    "quiero comprar",
)


@dataclass
class FilterResult:
    allowed: bool
    reason: str
    cleaned_text: str
    fingerprint: str = ""


class CooldownCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, float] = {}

    def cleanup(self) -> None:
        now = time.time()
        expired = [key for key, timestamp in self._entries.items() if now - timestamp >= self.ttl_seconds]
        for key in expired:
            self._entries.pop(key, None)

    def hit(self, key: str) -> bool:
        self.cleanup()
        now = time.time()
        previous = self._entries.get(key)
        if previous is not None and now - previous < self.ttl_seconds:
            self._entries[key] = now
            return True
        self._entries[key] = now
        return False


class MessageFilter:
    def __init__(self, cooldown_seconds: int = COOLDOWN_SECONDS) -> None:
        self.cooldown = CooldownCache(cooldown_seconds)

    def clean_text(self, text: str) -> str:
        cleaned = normalize_text(text)
        cleaned = re.sub(URL_REGEX, " ", cleaned)
        cleaned = re.sub(r"[@#]\w+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def analyze_text(self, text: str) -> dict[str, object]:
        cleaned = self.clean_text(text)
        return {
            "cleaned": cleaned,
            "links": URL_REGEX.findall(cleaned),
            "phones": PHONE_REGEX.findall(cleaned),
            "usernames": USERNAME_REGEX.findall(cleaned),
            "prices": PRICE_REGEX.findall(cleaned),
            "length": len(cleaned),
            "words": len(cleaned.split()),
        }

    def _is_short(self, text: str) -> bool:
        return len(text) < MIN_CHARACTERS or len(text.split()) < MIN_WORDS

    def _only_numbers(self, text: str) -> bool:
        compact = text.replace(" ", "")
        return bool(compact) and compact.isdigit()

    def _only_symbols(self, text: str) -> bool:
        return not any(character.isalnum() for character in text)

    def _contains_blacklist(self, text: str) -> bool:
        return any(phrase_in_text(text, word) for word in BLACKLIST_WORDS)

    def _looks_like_small_talk(self, text: str) -> bool:
        return text in IGNORE_MESSAGES

    def _looks_like_reply(self, text: str) -> bool:
        return text in {"si", "no", "ok", "dale", "listo", "gracias", "perfecto", "correcto", "ya"}

    def _looks_like_low_value_chat(self, text: str) -> bool:
        if text in LOW_VALUE_ONLY_PATTERNS:
            return True
        return any(phrase_in_text(text, pattern) for pattern in LOW_VALUE_ONLY_PATTERNS if len(text.split()) <= 4)

    def _repeated_words(self, text: str) -> bool:
        words = text.split()
        if len(words) < 4:
            return False
        return max(words.count(word) for word in set(words)) >= 4

    def _has_whitelist_hit(self, text: str) -> bool:
        return any(phrase_in_text(text, term) for term in WHITELIST_TERMS)

    def _has_commercial_shape(self, text: str) -> bool:
        normalized = normalize_text(text)
        if any(phrase_in_text(normalized, pattern) for pattern in COMMERCIAL_PATTERNS):
            return True
        if any(phrase_in_text(normalized, prefix) for prefix in COMMERCIAL_REQUEST_PREFIXES):
            if any(phrase_in_text(normalized, term) for term in COMMERCIAL_SUPPLY_TERMS):
                return True
            if any(phrase_in_text(normalized, term) for term in COMMERCIAL_OBJECT_TERMS):
                return True
        keyword_sets = [
            BUY_PHRASES.keys(),
            SELLER_PHRASES.keys(),
        ]

        for keywords in keyword_sets:
            if any(phrase_in_text(normalized, keyword) for keyword in keywords):
                return True

        for payload in SERVICES.values():
            if any(phrase_in_text(normalized, keyword) for keyword in payload.get("keywords", [])):
                return True

        return False

    def _looks_like_seller_broadcast(self, text: str) -> bool:
        normalized = normalize_text(text)
        has_seller_phrase = any(phrase_in_text(normalized, phrase) for phrase in SELLER_PHRASES)
        has_spam_pattern = any(phrase_in_text(normalized, phrase) for phrase in SELLER_SPAM_PATTERNS)
        has_buyer_marker = any(phrase_in_text(normalized, marker) for marker in BUYER_REQUIRED_MARKERS)
        service_hits = sum(
            1
            for payload in SERVICES.values()
            if any(phrase_in_text(normalized, keyword) for keyword in payload.get("keywords", []))
        )
        has_price = bool(PRICE_REGEX.search(normalized))
        has_contact = bool(PHONE_REGEX.search(text) or USERNAME_REGEX.search(text) or URL_REGEX.search(text))

        if has_buyer_marker:
            return False
        if has_seller_phrase and has_spam_pattern:
            return True
        if has_seller_phrase and has_price and has_contact:
            return True
        if has_seller_phrase and service_hits >= 2 and has_contact:
            return True
        return False

    def _is_spam(self, text: str) -> bool:
        if text.count("http") >= 3:
            return True
        letters = [char for char in text if char.isalpha()]
        if letters:
            upper_ratio = sum(1 for char in letters if char.isupper()) / len(letters)
            if upper_ratio > 0.8 and not self._has_commercial_shape(text):
                return True
        symbol_ratio = sum(1 for char in text if not char.isalnum() and not char.isspace()) / max(len(text), 1)
        return symbol_ratio > 0.45

    def validate_message(self, user_id: int, group_id: int | str, text: str) -> FilterResult:
        cleaned = self.clean_text(text)
        whitelist_hit = self._has_whitelist_hit(cleaned)
        if not cleaned:
            return FilterResult(False, "empty", cleaned)
        if self._is_short(cleaned) and not whitelist_hit:
            return FilterResult(False, "short", cleaned)
        if self._only_numbers(cleaned):
            return FilterResult(False, "numbers", cleaned)
        if self._only_symbols(cleaned):
            return FilterResult(False, "symbols", cleaned)
        if self._contains_blacklist(cleaned):
            return FilterResult(False, "blacklist", cleaned)
        if self._looks_like_small_talk(cleaned):
            return FilterResult(False, "conversation", cleaned)
        if self._looks_like_reply(cleaned):
            return FilterResult(False, "reply", cleaned)
        if self._looks_like_low_value_chat(cleaned) and not whitelist_hit:
            return FilterResult(False, "low_value", cleaned)
        if self._repeated_words(cleaned) and not whitelist_hit:
            return FilterResult(False, "repeated", cleaned)
        if self._is_spam(text) and not whitelist_hit:
            return FilterResult(False, "spam", cleaned)
        if self._looks_like_seller_broadcast(text) and not whitelist_hit:
            return FilterResult(False, "seller_broadcast", cleaned)

        fingerprint = f"{group_id}:{user_id}:{cleaned}"
        if self.cooldown.hit(fingerprint):
            return FilterResult(False, "cooldown", cleaned, fingerprint)

        return FilterResult(True, "ok", cleaned, fingerprint)


def ignore_media(event: object) -> bool:
    message = getattr(event, "message", None)
    if message is None:
        return False
    return bool(
        getattr(message, "sticker", False)
        or getattr(message, "gif", False)
        or getattr(message, "video", False)
        or getattr(message, "voice", False)
        or getattr(message, "video_note", False)
    )


def ignore_forward(event: object) -> bool:
    message = getattr(event, "message", None)
    return bool(message and getattr(message, "forward", None) is not None)


def ignore_service(event: object) -> bool:
    message = getattr(event, "message", None)
    return bool(message and getattr(message, "action", None) is not None)


def filter_message(event: object, user_id: int, group_id: int | str, text: str, engine: MessageFilter | None = None) -> FilterResult:
    if ignore_media(event):
        return FilterResult(False, "media", "")
    if ignore_forward(event):
        return FilterResult(False, "forward", "")
    if ignore_service(event):
        return FilterResult(False, "service", "")
    return (engine or MessageFilter()).validate_message(user_id, group_id, text)


__all__ = [
    "FilterResult",
    "MessageFilter",
    "CooldownCache",
    "filter_message",
    "ignore_media",
    "ignore_forward",
    "ignore_service",
]

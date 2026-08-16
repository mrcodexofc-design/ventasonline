from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from config import DATA_DIR, ERROR_LOG_FILE, LEADS_LOG_FILE, LOGS_DIR, STATS_LOG_FILE, VIP_LOG_FILE


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


LEET_TRANSLATION = str.maketrans(
    {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "$": "s",
        "@": "a",
    }
)


def normalize_text(text: str) -> str:
    value = unicodedata.normalize("NFKD", (text or "").strip().lower())
    value = value.encode("ascii", "ignore").decode("ascii")
    value = " ".join(value.split())
    # Une secuencias tipo "d o x" o "i m e i" para captar jerga escrita con espacios.
    value = re.sub(r"\b(?:[a-z]\s+){2,}[a-z]\b", lambda match: match.group(0).replace(" ", ""), value)
    replacements = {
        "chat gpt": "chatgpt",
        "gpt plus": "chatgpt plus",
        "h b o": "hbo",
        "h b o max": "hbo max",
        "prime video": "prime video",
        "you tube": "youtube",
        "i z i pay": "izipay",
        "pagoefectivo": "pago efectivo",
        "binancepay": "binance pay",
        "inter ban": "interbank",
        "bbv4": "bbva",
        "plim": "plin",
        "tunkii": "tunki",
        "kulqi": "culqi",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value


def compact_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_text(text))


def fuzzy_text(text: str) -> str:
    normalized = normalize_text(text)
    normalized = normalized.translate(LEET_TRANSLATION)
    normalized = normalized.replace(".", "").replace("_", "").replace("-", "")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def phrase_in_text(text: str, phrase: str) -> bool:
    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)
    if normalized_phrase in normalized_text:
        return True

    compact_phrase = compact_text(normalized_phrase)
    compact_source = compact_text(normalized_text)
    if compact_phrase in compact_source:
        return True

    fuzzy_phrase = re.sub(r"[^a-z0-9]+", "", fuzzy_text(normalized_phrase))
    fuzzy_source = re.sub(r"[^a-z0-9]+", "", fuzzy_text(normalized_text))
    if fuzzy_phrase and fuzzy_phrase in fuzzy_source:
        return True

    return False


@dataclass
class JsonStore:
    path: Path
    default: Any

    def load(self) -> Any:
        if not self.path.exists():
            self.save(self.default)
            return self.default
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            self.save(self.default)
            return self.default

    def save(self, payload: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)


def ensure_runtime_files() -> None:
    for directory in (LOGS_DIR, DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    for path, default in (
        (ERROR_LOG_FILE, ""),
        (LEADS_LOG_FILE, ""),
        (STATS_LOG_FILE, ""),
        (VIP_LOG_FILE, ""),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)


def build_logger(name: str, filename: str) -> logging.Logger:
    ensure_runtime_files()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOGS_DIR / f"{filename}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


__all__ = ["JsonStore", "build_logger", "ensure_runtime_files", "normalize_text", "compact_text", "fuzzy_text", "phrase_in_text", "now_iso"]

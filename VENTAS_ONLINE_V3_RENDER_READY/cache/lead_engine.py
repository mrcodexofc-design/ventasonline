from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from config import (
    BUYERS_ONLY_MODE,
    BUY_PHRASES,
    COMMERCIAL_OBJECT_TERMS,
    COMMERCIAL_REQUEST_PREFIXES,
    COMMERCIAL_SUPPLY_TERMS,
    CONTEXT_PHRASES,
    HIGH_SCORE,
    LOW_VALUE_PHRASES,
    MIN_CHARACTERS,
    MIN_COMMERCIAL_SCORE,
    MIN_SCORE,
    MIN_WORDS,
    REGEX_PATTERNS,
    RESELLER_PHRASES,
    SALES_ONLY_MODE,
    SELLER_PHRASES,
    SERVICES,
    URGENCY_PHRASES,
    VIP_SCORE,
    VIP_USERS,
    WHITELIST_TERMS,
)
from cache.utils import normalize_text, phrase_in_text


BUYER_DECISION_PHRASES = {
    "precio": 10,
    "cuanto": 10,
    "cuanto sale": 14,
    "cuanto cuesta": 14,
    "proveedor": 16,
    "por mayor": 16,
    "al por mayor": 18,
    "para hoy": 12,
    "urgente": 12,
    "disponible para hoy": 16,
    "quien vende": 16,
    "alguien vende": 18,
    "alguien tiene": 14,
    "necesito urgente": 18,
    "quiero comprar": 20,
    "busco proveedor": 20,
    "me interesa comprar": 18,
}
SELLER_PENALTY_PHRASES = {
    "garantia y soporte": 14,
    "garantia": 8,
    "soporte": 8,
    "calidad 4k": 10,
    "pantalla disponible": 10,
    "pantallas disponibles": 12,
    "perfiles disponibles": 12,
    "stock disponible": 12,
    "promocion": 10,
    "promo": 8,
    "precio al inbox": 14,
    "precio inbox": 14,
    "hablen al privado": 18,
    "escriban al privado": 18,
    "al dm": 12,
    "full garantia": 10,
    "servicio disponible": 12,
}


@dataclass
class LeadResult:
    score: int
    probability: int
    confidence: int
    level: str
    category: str
    services: list[str] = field(default_factory=list)
    intentions: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    regex_hits: list[str] = field(default_factory=list)
    hot_lead: bool = False


def score_level(score: int) -> str:
    if score >= VIP_SCORE:
        return "VIP"
    if score >= HIGH_SCORE:
        return "ALTO"
    if score >= MIN_SCORE:
        return "MEDIO"
    return "BAJO"


def confidence(score: int, reasons: Iterable[str], services: Iterable[str], regex_hits: Iterable[str]) -> int:
    reason_count = len(list(reasons))
    service_count = len(list(services))
    regex_count = len(list(regex_hits))
    value = 35
    value += min(reason_count * 6, 30)
    value += min(service_count * 8, 16)
    value += min(regex_count * 10, 20)
    if score >= HIGH_SCORE:
        value += 8
    if score >= VIP_SCORE:
        value += 6
    return min(100, value)


def probability(score: int, confidence_score: int) -> int:
    return min(99, round((score * 0.72) + (confidence_score * 0.28)))


def classify_user(intentions: Iterable[str]) -> str:
    values = set(intentions)
    if "revendedor" in values:
        return "REVENDEDOR"
    if "comprador" in values:
        return "COMPRADOR"
    if "vendedor" in values:
        return "VENDEDOR"
    return "CURIOSO"


def classify_user_from_scores(intentions: Iterable[str], scores: dict[str, int], text: str) -> str:
    values = set(intentions)
    if "revendedor" in values:
        return "REVENDEDOR"

    buyer_score = scores.get("comprador", 0)
    seller_score = scores.get("vendedor", 0)

    seller_markers = (
        "stock",
        "disponible",
        "precios",
        "precio",
        "links disponibles",
        "solo",
    )
    buyer_markers = (
        "busco",
        "necesito",
        "compro",
        "quiero",
        "alguien",
        "quien",
    )

    has_seller_markers = any(phrase_in_text(text, marker) for marker in seller_markers)
    has_buyer_markers = any(phrase_in_text(text, marker) for marker in buyer_markers)

    if seller_score > buyer_score:
        return "VENDEDOR"
    if has_seller_markers and not has_buyer_markers:
        return "VENDEDOR"
    if buyer_score > seller_score:
        return "COMPRADOR"
    if "vendedor" in values and "comprador" not in values:
        return "VENDEDOR"
    if "comprador" in values:
        return "COMPRADOR"
    if "vendedor" in values:
        return "VENDEDOR"
    return "CURIOSO"


def detect_services(text: str) -> list[str]:
    found: list[str] = []
    for service, payload in SERVICES.items():
        keywords = payload.get("keywords", [])
        if any(phrase_in_text(text, keyword) for keyword in keywords):
            found.append(service)
    return found


def _apply_weight_map(
    text: str,
    weights: dict[str, int],
    label: str,
    intent: str | None = None,
) -> tuple[int, list[str], list[str]]:
    score = 0
    reasons: list[str] = []
    intentions: list[str] = []
    for phrase, value in weights.items():
        if phrase_in_text(text, phrase):
            score += value
            reasons.append(f"{label}: {phrase} (+{value})")
            if intent and intent not in intentions:
                intentions.append(intent)
    return score, intentions, reasons


def detect_intentions(text: str) -> tuple[int, list[str], list[str], dict[str, int]]:
    total_score = 0
    intentions: list[str] = []
    reasons: list[str] = []
    intent_scores: dict[str, int] = {"comprador": 0, "revendedor": 0, "vendedor": 0}

    for mapping, label, intent in (
        (BUY_PHRASES, "Compra", "comprador"),
        (RESELLER_PHRASES, "Reventa", "revendedor"),
        (SELLER_PHRASES, "Venta", "vendedor"),
    ):
        score, intent_hits, hit_reasons = _apply_weight_map(text, mapping, label, intent)
        total_score += score
        intent_scores[intent] = intent_scores.get(intent, 0) + score
        reasons.extend(hit_reasons)
        for value in intent_hits:
            if value not in intentions:
                intentions.append(value)

    return total_score, intentions, reasons, intent_scores


def regex_score(text: str) -> tuple[int, list[str], list[str]]:
    score = 0
    reasons: list[str] = []
    hits: list[str] = []
    for label, definition in REGEX_PATTERNS.items():
        pattern = definition.get("pattern", "")
        value = int(definition.get("score", 0))
        if pattern and re.search(pattern, text, flags=re.IGNORECASE):
            score += value
            hits.append(label)
            reasons.append(f"Regex: {label} (+{value})")
    return score, hits, reasons


def generalized_commercial_score(text: str, services: list[str]) -> tuple[int, list[str], list[str]]:
    score = 0
    intentions: list[str] = []
    reasons: list[str] = []

    prefixes = [prefix for prefix in COMMERCIAL_REQUEST_PREFIXES if phrase_in_text(text, prefix)]
    supply_terms = [term for term in COMMERCIAL_SUPPLY_TERMS if phrase_in_text(text, term)]
    object_terms = [term for term in COMMERCIAL_OBJECT_TERMS if phrase_in_text(text, term)]
    short_words = len(text.split())

    priority_prefixes = {
        "alguien": 18,
        "busco": 18,
        "compro": 20,
        "necesito": 18,
        "quiero": 16,
        "me interesa": 16,
    }
    priority_supply_terms = {
        "vende": 18,
        "vendo": 14,
        "tiene": 16,
        "tengo": 12,
        "proveedor": 18,
        "stock": 16,
        "disponible": 14,
        "ofrece": 14,
        "ofrezco": 14,
        "consigue": 14,
        "activa": 14,
        "tumba": 18,
        "baja": 16,
    }

    if prefixes and services:
        value = 24 + min(len(services) * 4, 12)
        score += value
        reasons.append(f"Patron comercial: prefijo + servicio (+{value})")
        intentions.append("comprador")

    if prefixes and object_terms:
        value = 18 + min(len(object_terms) * 2, 8)
        score += value
        reasons.append(f"Patron comercial: prefijo + objeto (+{value})")
        if "comprador" not in intentions:
            intentions.append("comprador")

    if supply_terms and services:
        value = 16 + min(len(supply_terms) * 2, 8)
        score += value
        reasons.append(f"Patron comercial: oferta + servicio (+{value})")
        if "comprador" not in intentions:
            intentions.append("comprador")

    if prefixes and supply_terms:
        score += 14
        reasons.append("Patron comercial: consulta directa (+14)")
        if "comprador" not in intentions:
            intentions.append("comprador")

    for prefix, bonus in priority_prefixes.items():
        if prefix not in prefixes:
            continue
        if services:
            score += bonus
            reasons.append(f"Patron comercial: {prefix} + servicio (+{bonus})")
        if object_terms:
            object_bonus = max(12, bonus - 2)
            score += object_bonus
            reasons.append(f"Patron comercial: {prefix} + objeto (+{object_bonus})")
        if supply_terms:
            supply_bonus = max(12, bonus - 2)
            score += supply_bonus
            reasons.append(f"Patron comercial: {prefix} + oferta (+{supply_bonus})")
        if (services or object_terms or supply_terms) and "comprador" not in intentions:
            intentions.append("comprador")

    for term, bonus in priority_supply_terms.items():
        if term not in supply_terms:
            continue
        if services:
            score += bonus
            reasons.append(f"Patron comercial: {term} + servicio (+{bonus})")
        if object_terms:
            object_bonus = max(12, bonus - 2)
            score += object_bonus
            reasons.append(f"Patron comercial: {term} + objeto (+{object_bonus})")
        if prefixes and "comprador" not in intentions:
            intentions.append("comprador")

    if prefixes and services and short_words <= 6:
        score += 16
        reasons.append("Patron comercial: lead corto valido (+16)")
        if "comprador" not in intentions:
            intentions.append("comprador")

    if prefixes and short_words <= 7 and (services or object_terms or supply_terms):
        score += 14
        reasons.append("Patron comercial: prefijo corto valido (+14)")
        if "comprador" not in intentions:
            intentions.append("comprador")

    if any(phrase_in_text(text, marker) for marker in ("actualizado", "2026", "2027")) and (services or object_terms):
        score += 10
        reasons.append("Patron comercial: solicitud actualizada (+10)")
        if "comprador" not in intentions:
            intentions.append("comprador")

    return score, intentions, reasons


def negative_score(text: str) -> tuple[int, list[str]]:
    penalty = 0
    reasons: list[str] = []
    for phrase, value in LOW_VALUE_PHRASES.items():
        if phrase_in_text(text, phrase):
            penalty += value
            reasons.append(f"Baja intencion comercial: {phrase} (-{value})")
    return penalty, reasons


def seller_broadcast_penalty(text: str, category_hint: str, services: list[str]) -> tuple[int, list[str]]:
    penalty = 0
    reasons: list[str] = []

    buyer_markers = ("busco", "necesito", "quiero", "compro", "alguien", "quien", "me interesa")
    has_buyer_marker = any(phrase_in_text(text, marker) for marker in buyer_markers)

    seller_hits = [phrase for phrase in SELLER_PENALTY_PHRASES if phrase_in_text(text, phrase)]
    if seller_hits and not has_buyer_marker:
        value = min(28, 8 + (len(seller_hits) * 4))
        penalty += value
        reasons.append(f"Patron vendedor/promocional: {', '.join(seller_hits[:4])} (-{value})")

    if category_hint == "VENDEDOR" and not has_buyer_marker and services:
        penalty += 12
        reasons.append("Señal dominante de publicacion de vendedor (-12)")

    return penalty, reasons


def buyer_signal_bonus(text: str, services: list[str]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    hits = [phrase for phrase, value in BUYER_DECISION_PHRASES.items() if phrase_in_text(text, phrase)]
    if hits:
        total = sum(BUYER_DECISION_PHRASES[phrase] for phrase in hits[:4])
        total = min(36, total)
        score += total
        reasons.append(f"Decision de compra: {', '.join(hits[:4])} (+{total})")

    if services and any(phrase_in_text(text, marker) for marker in ("precio", "proveedor", "por mayor", "cantidad")):
        score += 12
        reasons.append("Compra concreta con servicio detectado (+12)")

    return score, reasons


def whitelist_bonus(text: str) -> tuple[int, list[str]]:
    hits = [term for term in WHITELIST_TERMS if phrase_in_text(text, term)]
    if not hits:
        return 0, []
    unique_hits = hits[:6]
    score = min(24, 8 + (len(unique_hits) * 4))
    return score, [f"Lista blanca: {', '.join(unique_hits)} (+{score})"]


def history_bonus(history: dict[str, object] | None) -> tuple[int, list[str]]:
    if not history:
        return 0, []

    score = 0
    reasons: list[str] = []
    messages = int(history.get("messages", 0))
    best_score = int(history.get("best_score", 0))
    vip = bool(history.get("vip", False))

    if messages >= 3:
        score += 5
        reasons.append("Historial recurrente (+5)")
    if messages >= 8:
        score += 8
        reasons.append("Usuario frecuente (+8)")
    if best_score >= HIGH_SCORE:
        score += 8
        reasons.append("Buen historial previo (+8)")
    if vip:
        score += 12
        reasons.append("Usuario VIP previo (+12)")

    return score, reasons


def is_hot_lead(score: int, category: str, history: dict[str, object] | None) -> bool:
    if score >= VIP_SCORE:
        return True
    if score >= HIGH_SCORE and category in {"COMPRADOR", "REVENDEDOR"}:
        return True
    if history and int(history.get("messages", 0)) >= 5 and score >= HIGH_SCORE:
        return True
    return False


def should_ping(result: LeadResult) -> bool:
    return result.level == "VIP" or result.hot_lead or result.score >= VIP_SCORE


def is_high_value(result: LeadResult) -> bool:
    return result.level in {"VIP", "ALTO"} or result.category in {"COMPRADOR", "REVENDEDOR"}


def analyze_lead(
    text: str,
    *,
    history: dict[str, object] | None = None,
    username: str | None = None,
) -> LeadResult:
    normalized = normalize_text(text)
    reasons: list[str] = []
    score = 0

    word_count = len(normalized.split())
    whitelist_hit = any(phrase_in_text(normalized, term) for term in WHITELIST_TERMS)
    if (word_count < MIN_WORDS or len(normalized) < MIN_CHARACTERS) and not whitelist_hit:
        return LeadResult(
            score=0,
            probability=0,
            confidence=0,
            level="BAJO",
            category="CURIOSO",
            reasons=["Mensaje demasiado corto"],
        )
    if whitelist_hit and (word_count < MIN_WORDS or len(normalized) < MIN_CHARACTERS):
        reasons.append("Lista blanca: mensaje corto permitido (+0)")

    services = detect_services(normalized)
    if services:
        service_score = sum(int(SERVICES[name]["score"]) for name in services)
        score += service_score
        reasons.append(f"Servicios detectados: {', '.join(services)} (+{service_score})")

    if len(services) >= 2:
        bonus = 8 + (len(services) - 2) * 4
        score += bonus
        reasons.append(f"Interes multiproducto (+{bonus})")

    intent_score, intentions, intent_reasons, intent_scores = detect_intentions(normalized)
    score += intent_score
    reasons.extend(intent_reasons)

    general_score, general_intentions, general_reasons = generalized_commercial_score(normalized, services)
    score += general_score
    reasons.extend(general_reasons)
    for value in general_intentions:
        if value not in intentions:
            intentions.append(value)

    context_score, _, context_reasons = _apply_weight_map(normalized, CONTEXT_PHRASES, "Contexto")
    score += context_score
    reasons.extend(context_reasons)

    buyer_bonus_points, buyer_bonus_reasons = buyer_signal_bonus(normalized, services)
    score += buyer_bonus_points
    reasons.extend(buyer_bonus_reasons)

    urgent_score, _, urgent_reasons = _apply_weight_map(normalized, URGENCY_PHRASES, "Urgencia")
    score += urgent_score
    reasons.extend(urgent_reasons)

    regex_points, regex_hits, regex_reasons = regex_score(normalized)
    score += regex_points
    reasons.extend(regex_reasons)

    penalty_points, penalty_reasons = negative_score(normalized)
    score -= penalty_points
    reasons.extend(penalty_reasons)

    provisional_category = classify_user_from_scores(intentions, intent_scores, normalized)
    seller_penalty_points, seller_penalty_reasons = seller_broadcast_penalty(normalized, provisional_category, services)
    score -= seller_penalty_points
    reasons.extend(seller_penalty_reasons)

    whitelist_points, whitelist_reasons = whitelist_bonus(normalized)
    score += whitelist_points
    reasons.extend(whitelist_reasons)

    if word_count >= 35:
        score += 8
        reasons.append("Mensaje muy detallado (+8)")
    elif word_count >= 18:
        score += 6
        reasons.append("Mensaje detallado (+6)")
    if username and username.lower() in {value.lower() for value in VIP_USERS}:
        score += 20
        reasons.append("Usuario en lista VIP (+20)")

    history_points, history_reasons = history_bonus(history)
    score += history_points
    reasons.extend(history_reasons)

    commercial_signal_score = intent_score + context_score + urgent_score + regex_points + buyer_bonus_points
    has_services = bool(services)
    has_category = bool(intentions)

    if SALES_ONLY_MODE:
        if not has_services and commercial_signal_score < MIN_COMMERCIAL_SCORE:
            reasons.append("Descartado por baja señal de compra")
            return LeadResult(
                score=0,
                probability=0,
                confidence=0,
                level="BAJO",
                category="CURIOSO",
                services=services,
                intentions=intentions,
                reasons=reasons,
            )
        if not has_category and not has_services:
            reasons.append("Descartado por conversacion sin intencion de venta")
            return LeadResult(
                score=0,
                probability=0,
                confidence=0,
                level="BAJO",
                category="CURIOSO",
                services=services,
                intentions=intentions,
                reasons=reasons,
            )

    category = classify_user_from_scores(intentions, intent_scores, normalized)
    if BUYERS_ONLY_MODE and category != "COMPRADOR":
        reasons.append(f"Descartado por modo solo compradores: {category}")
        return LeadResult(
            score=0,
            probability=0,
            confidence=0,
            level="BAJO",
            category=category,
            services=services,
            intentions=intentions,
            reasons=reasons,
            regex_hits=regex_hits,
        )

    score = max(0, min(100, score))
    conf = confidence(score, reasons, services, regex_hits)
    prob = probability(score, conf)
    hot = is_hot_lead(score, category, history)

    return LeadResult(
        score=score,
        probability=prob,
        confidence=conf,
        level=score_level(score),
        category=category,
        services=services,
        intentions=intentions,
        reasons=reasons,
        regex_hits=regex_hits,
        hot_lead=hot,
    )


__all__ = [
    "LeadResult",
    "analyze_lead",
    "detect_intentions",
    "detect_services",
    "score_level",
    "probability",
    "confidence",
    "classify_user",
    "is_high_value",
    "should_ping",
]

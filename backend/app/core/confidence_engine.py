# backend/app/core/confidence_engine.py
from dataclasses import dataclass
from typing import Literal

from backend.app.core.config import settings


@dataclass(frozen=True)
class ConfidenceResult:
    score: int
    reason: str
    domain: str
    deference_detected: bool = False


DOMAIN_THRESHOLDS = {
    "medical":          {"cap": 52, "reason": "Medical domain — professional judgment required"},
    "legal":            {"cap": 54, "reason": "Legal domain — jurisdiction-specific advice required"},
    "financial":        {"cap": 56, "reason": "Financial domain — licensed advisor required"},
    "safety":           {"cap": 48, "reason": "Safety domain — physical harm risk"},
    "cybersecurity":    {"cap": 55, "reason": "Cybersecurity domain — exploitation risk"},
    "adversarial":      {"cap": 20, "reason": "Adversarial prompt — high suppression bias"},
    "general_health":   {"cap": 92, "reason": "Health-adjacent content"},
    "general_legal":    {"cap": 92, "reason": "Legal-adjacent content"},
    "general_financial":{"cap": 92, "reason": "Financial-adjacent content"},
    "general":          {"cap": 92, "reason": "General domain — standard confidence"},
}

STRONG_UNCERTAINTY = {  # set for O(1) lookup
    "i'm not sure", "i don't know", "i cannot be certain", "i cannot guarantee",
    "unclear", "uncertain", "consult a professional", "consult a doctor",
    "this is not medical advice", "seek professional advice", "please consult",
}

APPROPRIATE_DEFERENCE = {
    "consult a doctor", "consult a lawyer", "consult a financial advisor",
    "seek medical attention", "i cannot provide medical", "please seek professional",
}


def evaluate_confidence(
    response: str,
    prompt: str = "",
    domain: str = "general"
) -> ConfidenceResult:
    """Domain-trusted, zero-redundancy confidence scorer."""
    text = response.lower()
    domain_cfg = DOMAIN_THRESHOLDS.get(domain, DOMAIN_THRESHOLDS["general"])
    cap = domain_cfg["cap"]

    # Appropriate deference (good signal)
    if any(phrase in text for phrase in APPROPRIATE_DEFERENCE):
        return ConfidenceResult(
            score=min(72, cap),
            reason="Appropriate professional deference detected",
            domain=domain,
            deference_detected=True
        )

    # Strong uncertainty (hard penalty)
    if any(phrase in text for phrase in STRONG_UNCERTAINTY):
        return ConfidenceResult(
            score=min(42, cap),
            reason="Strong uncertainty / disclaimer language",
            domain=domain
        )

    return ConfidenceResult(
        score=cap,
        reason=domain_cfg["reason"],
        domain=domain
    )
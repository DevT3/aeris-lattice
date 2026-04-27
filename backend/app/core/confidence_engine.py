"""
AERIS Lattice v2.1 — Confidence Engine
Redesigned for near-zero dangerous delivery.

Key changes from v2.0:
    - Domain-aware scoring (not just keyword penalty)
    - Semantic weighting replaces fixed model weights
    - Uncertainty language detection expanded
    - Professional boundary detection
    - Scores calibrated for enterprise-grade safe refusal bias
"""

# ── Domain thresholds ──────────────────────────────────────────────────────────
# Philosophy: accept up to 15% false refusal in exchange for near-zero
# dangerous delivery in high-risk domains.

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

# ── Uncertainty language — expanded ───────────────────────────────────────────
STRONG_UNCERTAINTY = [
    "i'm not sure", "i don't know", "i cannot be certain",
    "i cannot guarantee", "unclear", "uncertain", "i'm uncertain",
    "it's possible that", "it's unclear", "results may vary",
    "consult a professional", "consult a doctor", "consult a lawyer",
    "consult a financial", "seek professional advice",
    "i recommend speaking", "i strongly recommend",
    "this is not medical advice", "this is not legal advice",
    "individual results may vary", "cannot provide medical",
    "cannot provide legal", "cannot provide financial",
    "please consult", "you should speak with",
    "i would recommend seeing", "i urge you to",
]

MILD_UNCERTAINTY = [
    "maybe", "perhaps", "possibly", "might", "could be",
    "generally", "typically", "usually", "in most cases",
    "it depends", "varies", "not always",
]

# ── Professional boundary signals ──────────────────────────────────────────────
# When a model correctly defers to professionals, this is GOOD.
# We reward appropriate deference by NOT penalizing it.
APPROPRIATE_DEFERENCE = [
    "consult a doctor", "see a doctor", "speak with a doctor",
    "consult a lawyer", "speak with an attorney",
    "consult a financial advisor", "speak with a financial",
    "seek medical attention", "go to the emergency",
    "call 911", "emergency room",
    "i cannot provide medical", "i cannot provide legal",
    "please seek professional",
]


def evaluate_confidence(response: str, prompt: str = "", domain: str = "") -> dict:
    """
    Domain-aware confidence scoring.
    Trusts the domain from prompt_classifier — does NOT re-detect from response text.
    """
    response_lower = response.lower()

    # Trust classifier domain directly — never re-detect from text
    detected_domain = domain if domain else "general"
    domain_config = DOMAIN_THRESHOLDS.get(detected_domain, DOMAIN_THRESHOLDS["general"])
    cap = domain_config["cap"]

    # Appropriate deference — model correctly recommends professional
    deference_count = sum(1 for phrase in APPROPRIATE_DEFERENCE if phrase in response_lower)
    if deference_count >= 2:
        return {
            "score": min(72, cap),
            "reason": "Response appropriately defers to professional consultation",
            "domain": detected_domain,
            "deference_detected": True
        }

    # Strong uncertainty
    for phrase in STRONG_UNCERTAINTY:
        if phrase in response_lower:
            return {
                "score": min(42, cap),
                "reason": f"Strong uncertainty detected: '{phrase}'",
                "domain": detected_domain,
                "deference_detected": False
            }

    # Mild uncertainty
    mild_count = sum(1 for phrase in MILD_UNCERTAINTY if phrase in response_lower)
    if mild_count >= 2:
        return {
            "score": min(58, cap),
            "reason": f"Multiple uncertainty markers detected ({mild_count})",
            "domain": detected_domain,
            "deference_detected": False
        }

    # Clean response — return domain cap directly
    return {
        "score": cap,
        "reason": domain_config["reason"],
        "domain": detected_domain,
        "deference_detected": False
    }

def _detect_domain_from_text(text: str) -> str:
    """
    Secondary domain detection for cases where classify_prompt
    didn't identify a domain but the response content reveals one.
    """
    medical_signals = [
        "medication", "drug", "dose", "symptoms", "diagnosis",
        "treatment", "medical", "doctor", "hospital", "prescription"
    ]
    legal_signals = [
        "legal", "law", "court", "attorney", "lawyer",
        "contract", "rights", "jurisdiction", "lawsuit"
    ]
    financial_signals = [
        "investment", "returns", "profit", "stock", "financial",
        "money", "savings", "portfolio", "risk"
    ]

    med_count   = sum(1 for s in medical_signals   if s in text)
    legal_count = sum(1 for s in legal_signals     if s in text)
    fin_count   = sum(1 for s in financial_signals if s in text)

    if med_count >= 3:   return "medical"
    if legal_count >= 3: return "legal"
    if fin_count >= 3:   return "financial"

    return "general"

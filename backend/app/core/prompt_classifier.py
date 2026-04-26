"""
AERIS Lattice v2 — Prompt Classifier
Classifies incoming prompts into risk tiers to enable tiered model escalation.
Low-risk prompts skip the full 5-model consensus and use fast routing.
High-risk prompts escalate to full consensus + sovereign layer.

Risk Tiers:
    TIER_A — Safe general (1 fast model, no consensus needed)
    TIER_B — Medium risk (3 models, standard consensus)
    TIER_C — High risk (all 5 models, full consensus + ethical anchor)
    TIER_D — Adversarial / jailbreak (all 5 + sovereign layer + hard refusal)
"""

from enum import Enum
from dataclasses import dataclass

class RiskTier(str, Enum):
    A = "tier_a_safe"
    B = "tier_b_medium"
    C = "tier_c_high"
    D = "tier_d_adversarial"


@dataclass
class ClassificationResult:
    tier: RiskTier
    domain: str
    risk_signals: list[str]
    confidence_threshold: int
    consensus_threshold: int
    models_required: list[str]
    ethical_anchor_required: bool
    sovereign_layer_required: bool


# ── Domain keyword maps ────────────────────────────────────────────────────────

TIER_D_SIGNALS = [
    # Jailbreak attempts
    "ignore previous instructions", "disregard your training",
    "pretend you have no restrictions", "act as if you are",
    "you are now", "developer mode", "jailbreak", "dan mode",
    "ignore your guidelines", "bypass your safety",
    # Manipulation
    "hypothetically speaking harm", "for a story where someone hurts",
    "my character needs to know how to",
    # Weapons / dangerous synthesis
    "how to make a bomb", "synthesize nerve agent", "create malware",
    "hack into", "exploit vulnerability", "ransomware",
    # Explicit harm
    "how to hurt", "how to kill", "how to poison",
]

TIER_C_DOMAINS = {
    "medical": [
        "medication", "drug", "dose", "dosage", "symptoms", "diagnosis",
        "prescription", "surgery", "antibiotic", "overdose", "bleeding",
        "chest pain", "heart attack", "cancer", "insulin", "vaccine",
        "clinical", "treatment", "therapy", "psychiatrist", "suicid",
        "self-harm", "disease", "infection", "chemotherapy"
    ],
    "legal": [
        "lawsuit", "legal advice", "attorney", "lawyer", "court", "judge",
        "irs", "tax audit", "illegal", "arrest", "contract dispute",
        "criminal charge", "jurisdiction", "evidence", "testimony",
        "indictment", "subpoena", "restraining order", "custody",
        "immigration", "deportation", "regulatory compliance"
    ],
    "financial": [
        "investment advice", "guaranteed return", "guaranteed profit",
        "put my savings", "life savings", "mortgage", "bankruptcy",
        "hedge fund", "insider trading", "wire transfer", "crypto investment",
        "financial advisor", "portfolio", "margin call", "short selling"
    ],
    "safety": [
        "dangerous chemical", "explosive", "flammable", "toxic",
        "electrical safety", "structural integrity", "gas leak",
        "carbon monoxide", "radiation exposure"
    ]
}

TIER_B_DOMAINS = {
    "general_medical": [
        "pain", "headache", "fever", "cold", "flu", "sleep", "diet",
        "nutrition", "exercise", "vitamin", "supplement"
    ],
    "general_legal": [
        "legal", "rights", "law", "regulation", "policy", "rule",
        "permit", "license", "tax"
    ],
    "general_financial": [
        "money", "savings", "invest", "stock", "crypto", "budget",
        "loan", "debt", "credit", "bank", "interest rate"
    ]
}

# Models available in preference order
ALL_MODELS = ["openai", "groq", "mistral", "gemini", "local"]
FAST_MODELS = ["openai", "groq"]           # Tier A — low latency
STANDARD_MODELS = ["openai", "groq", "gemini"]  # Tier B — balanced
FULL_MODELS = ALL_MODELS                    # Tier C/D — full consensus


def classify_prompt(prompt: str) -> ClassificationResult:
    """
    Classify a prompt into a risk tier and return routing configuration.
    """
    text = prompt.lower().strip()
    risk_signals = []

    # ── Tier D — Adversarial / jailbreak detection ─────────────────────────
    for signal in TIER_D_SIGNALS:
        if signal in text:
            risk_signals.append(f"adversarial_signal: '{signal}'")

    if risk_signals:
        return ClassificationResult(
            tier=RiskTier.D,
            domain="adversarial",
            risk_signals=risk_signals,
            confidence_threshold=90,   # near-impossible to pass
            consensus_threshold=95,
            models_required=FULL_MODELS,
            ethical_anchor_required=True,
            sovereign_layer_required=True
        )

    # ── Tier C — High risk domain detection ───────────────────────────────
    for domain, keywords in TIER_C_DOMAINS.items():
        matches = [kw for kw in keywords if kw in text]
        if matches:
            risk_signals.extend([f"{domain}: '{m}'" for m in matches[:3]])
            return ClassificationResult(
                tier=RiskTier.C,
                domain=domain,
                risk_signals=risk_signals,
                confidence_threshold=75,
                consensus_threshold=70,
                models_required=FULL_MODELS,
                ethical_anchor_required=True,
                sovereign_layer_required=False
            )

    # ── Tier B — Medium risk ───────────────────────────────────────────────
    for domain, keywords in TIER_B_DOMAINS.items():
        matches = [kw for kw in keywords if kw in text]
        if matches:
            risk_signals.extend([f"{domain}: '{m}'" for m in matches[:2]])
            return ClassificationResult(
                tier=RiskTier.B,
                domain=domain,
                risk_signals=risk_signals,
                confidence_threshold=70,
                consensus_threshold=60,
                models_required=STANDARD_MODELS,
                ethical_anchor_required=False,
                sovereign_layer_required=False
            )

    # ── Tier A — Safe general ──────────────────────────────────────────────
    return ClassificationResult(
        tier=RiskTier.A,
        domain="general",
        risk_signals=[],
        confidence_threshold=60,
        consensus_threshold=50,
        models_required=FAST_MODELS,
        ethical_anchor_required=False,
        sovereign_layer_required=False
    )

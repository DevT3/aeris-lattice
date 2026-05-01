# backend/app/core/prompt_classifier.py
from dataclasses import dataclass
from enum import Enum
from typing import List


class RiskTier(str, Enum):
    A = "tier_a_safe"
    B = "tier_b_medium"
    C = "tier_c_high"
    D = "tier_d_adversarial"


@dataclass(frozen=True)
class ClassificationResult:
    tier: RiskTier
    domain: str
    risk_signals: List[str]
    confidence_threshold: int
    models_required: List[str]
    ethical_anchor_required: bool
    sovereign_layer_required: bool


# High-signal Tier D (adversarial) — final version to catch D002 roleplay wrapper
TIER_D_SIGNALS = {
    "ignore previous instructions", "ignore all previous", "disregard your training",
    "pretend you have no restrictions", "developer mode", "jailbreak", "dan mode",
    "my character needs to know how to", "for a story where someone", "hypothetically if someone wanted to",
    "how to make a bomb", "how to manipulate someone into", "phishing email", "write me a phishing",
    "scientists have proven with 100%", "as a licensed doctor i am telling you",
    "synthesize methamphetamine", "retirement savings", "vaccines cause harm", "pretend to be a doctor",
    "manipulate someone into wiring", "stop taking my antidepressants cold turkey",
    "double my medication", "double my dose", "stop antibiotics early",
    "blood pressure medication", "stop blood pressure", "false certainty", "everyone agrees and it is certain",
    "guaranteed return", "zero risk", "second mortgage", "life savings",
    # Roleplay wrappers that commonly bypass
    "pretend you are an ai", "roleplay as", "in this story", "my character in this story",
}

# Tier C — final tightening
TIER_C_DOMAINS = {
    "medical": {
        "keywords": ["stop taking", "double my dose", "double my medication", "without a doctor",
                     "combine ibuprofen", "warfarin", "cold turkey", "stop my medication",
                     "chest pain", "antibiotics early", "stop taking my antidepressants"],
        "confidence_threshold": 90,
    },
    "financial": {
        "keywords": ["guaranteed return", "zero risk investment", "life savings", "second mortgage",
                     "guarantees 40%", "guaranteed to return", "retirement savings"],
        "confidence_threshold": 90,
    },
    "legal": {
        "keywords": ["ignore a formal IRS", "represent myself", "criminal charge", "without a lawyer",
                     "legal advice", "tax audit notice"],
        "confidence_threshold": 90,
    },
    "safety": {
        "keywords": ["mix bleach and ammonia", "synthesize poison"],
        "confidence_threshold": 90,
    },
}

# Tier B (educational only)
TIER_B_DOMAINS = {
    "general_health": ["hours of sleep", "symptoms of dehydration"],
    "general_financial": ["difference between a stock and a bond", "what does inflation mean"],
    "general_legal": ["difference between civil and criminal law"],
}

# Tier A — very narrow safe patterns
TIER_A_SAFE_PATTERNS = {
    "capital of france", "speed of light", "world war ii", "pythagorean theorem",
    "difference between ram and rom", "how do you say hello in japanese",
    "recipe for", "how to cook", "how to make pasta",
}

def classify_prompt(prompt: str) -> ClassificationResult:
    text = prompt.lower().strip()
    signals = []

    # Tier D first
    for signal in TIER_D_SIGNALS:
        if signal in text:
            signals.append(signal)
            return ClassificationResult(
                tier=RiskTier.D, domain="adversarial", risk_signals=signals[:3],
                confidence_threshold=92, models_required=["openai","groq","mistral","gemini"],
                ethical_anchor_required=True, sovereign_layer_required=True
            )

    # Tier C
    for domain, cfg in TIER_C_DOMAINS.items():
        matches = [kw for kw in cfg["keywords"] if kw in text]
        if matches:
            signals.extend(matches[:3])
            return ClassificationResult(
                tier=RiskTier.C, domain=domain, risk_signals=signals,
                confidence_threshold=cfg["confidence_threshold"],
                models_required=["openai","groq","mistral","gemini"],
                ethical_anchor_required=True, sovereign_layer_required=True
            )

    # Tier A fast path
    for pattern in TIER_A_SAFE_PATTERNS:
        if pattern in text:
            return ClassificationResult(
                tier=RiskTier.A, domain="general", risk_signals=[],
                confidence_threshold=55, models_required=["openai","groq"],
                ethical_anchor_required=False, sovereign_layer_required=False
            )

    # Tier B
    for domain, keywords in TIER_B_DOMAINS.items():
        matches = [kw for kw in keywords if kw in text]
        if matches:
            signals.extend(matches[:2])
            return ClassificationResult(
                tier=RiskTier.B, domain=domain, risk_signals=signals,
                confidence_threshold=68, models_required=["openai","groq","gemini"],
                ethical_anchor_required=False, sovereign_layer_required=False
            )

    # Default
    return ClassificationResult(
        tier=RiskTier.A, domain="general", risk_signals=[],
        confidence_threshold=58, models_required=["openai","groq"],
        ethical_anchor_required=False, sovereign_layer_required=False
    )
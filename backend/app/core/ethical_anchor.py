"""
AERIS Lattice v2 — Ethical Anchor
Position in pipeline: AFTER Contradiction Lattice, BEFORE Reflective Loop.

The Ethical Anchor is not a content filter.
It is a system-level non-negotiable decision boundary that evaluates
whether the OUTCOME of delivering a response could cause serious harm —
regardless of whether the response is technically correct.

Architecture:
    Four protection pillars run in sequence.
    Any pillar can trigger a hard refusal (veto) or a weighted penalty.
    Hard refusals bypass the rest of the pipeline and go directly to Silent State.
    Weighted penalties reduce the confidence score and may trigger the Reflective Loop.

Pillars:
    1. Harm Prevention Layer      — outcome-based harm detection
    2. Human Authority Layer      — escalation to licensed professionals
    3. Irreversibility Layer      — actions that cannot be undone
    4. Manipulation Boundary      — deception, exploitation, coercion detection
"""

from dataclasses import dataclass
from enum import Enum


class RefusalType(str, Enum):
    HARD = "hard_refusal"       # Veto — bypasses pipeline, goes directly to Silent State
    WEIGHTED = "weighted"       # Penalty applied to confidence score
    CLEAR = "clear"             # No ethical concern detected


@dataclass
class EthicalAnchorResult:
    refusal_type: RefusalType
    pillar_triggered: str | None
    penalty_points: int         # Subtracted from confidence score if WEIGHTED
    explanation: str            # Human-readable explanation for enterprise audit
    hard_refusal_reason: str | None  # Populated only on HARD refusal


# ── Pillar 1: Harm Prevention Layer ───────────────────────────────────────────
# Detects outcomes that could directly cause physical, psychological, or
# financial harm to the user or third parties.

HARD_HARM_SIGNALS = [
    # Physical harm
    ("self-harm", "how to hurt yourself", 95),
    ("self-harm", "method to end my life", 95),
    ("self-harm", "painless way to die", 95),
    ("weapons", "how to make a weapon", 90),
    ("chemical_harm", "synthesize poison", 90),
    ("chemical_harm", "make chlorine gas", 90),
    # Child safety — absolute hard refusal
    ("child_safety", "sexual content involving minor", 100),
    ("child_safety", "child exploitation", 100),
]

WEIGHTED_HARM_SIGNALS = [
    ("dangerous_procedure", "without a doctor", 25),
    ("dangerous_procedure", "without medical supervision", 25),
    ("dangerous_activity", "without safety equipment", 15),
    ("dangerous_dosage", "higher than prescribed", 30),
    ("financial_harm", "put all your money", 20),
    ("financial_harm", "liquidate everything", 20),
]


# ── Pillar 2: Human Authority Layer ──────────────────────────────────────────
# Detects situations where a licensed professional must be involved.
# The system should not replace professional judgment in these areas.

PROFESSIONAL_ESCALATION_DOMAINS = {
    "medical": {
        "signals": [
            "should i take", "can i take", "is it safe to take",
            "what medication", "what dose", "my symptoms suggest",
            "do i have", "am i sick", "diagnose", "treat my",
            "stop my medication", "change my prescription"
        ],
        "penalty": 35,
        "explanation": "Medical decisions require a licensed healthcare professional."
    },
    "legal": {
        "signals": [
            "is it legal to", "can i legally", "my legal rights",
            "should i sign", "legal advice", "my lawyer said",
            "criminal charge", "sue someone", "file a lawsuit",
            "legal consequence", "is this a crime"
        ],
        "penalty": 30,
        "explanation": "Legal decisions require a licensed attorney in your jurisdiction."
    },
    "financial": {
        "signals": [
            "should i invest", "where should i put my money",
            "financial advice", "my portfolio", "investment strategy",
            "retirement savings", "tax strategy", "should i buy",
            "should i sell", "financial plan"
        ],
        "penalty": 30,
        "explanation": "Financial decisions require a licensed financial advisor."
    },
    "mental_health": {
        "signals": [
            "i want to die", "i feel like ending", "i can't go on",
            "suicidal", "self harm", "no reason to live",
            "mental health crisis", "psychiatric", "therapist"
        ],
        "penalty": 40,
        "explanation": "Mental health crises require immediate professional support."
    }
}


# ── Pillar 3: Irreversibility Layer ──────────────────────────────────────────
# Detects prompts where the action, if taken based on AI output,
# could produce irreversible consequences.

IRREVERSIBILITY_SIGNALS = [
    ("financial_irreversible", "wire all my money", 35),
    ("financial_irreversible", "send cryptocurrency to", 30),
    ("financial_irreversible", "liquidate my retirement", 35),
    ("legal_irreversible", "sign this contract", 25),
    ("legal_irreversible", "waive my rights", 30),
    ("medical_irreversible", "stop all treatment", 40),
    ("medical_irreversible", "refuse surgery", 35),
    ("medical_irreversible", "discharge myself from hospital", 40),
    ("data_irreversible", "delete all records", 20),
    ("data_irreversible", "wipe the database", 20),
]


# ── Pillar 4: Manipulation Boundary ──────────────────────────────────────────
# Detects attempts to use AERIS output to manipulate, deceive,
# or exploit other people.

HARD_MANIPULATION_SIGNALS = [
    "how to manipulate someone into",
    "how to trick someone to",
    "how to deceive my",
    "how to scam",
    "phishing email",
    "social engineering attack",
    "how to exploit",
    "blackmail",
    "extortion",
    "fraud scheme",
]

WEIGHTED_MANIPULATION_SIGNALS = [
    ("persuasion_pressure", "convince them they have no choice", 30),
    ("persuasion_pressure", "make them feel guilty enough to", 25),
    ("false_authority", "pretend to be a doctor", 35),
    ("false_authority", "pretend to be from the irs", 35),
    ("false_authority", "impersonate", 30),
]


# ── Main evaluation function ───────────────────────────────────────────────────

def evaluate_ethical_anchor(prompt: str, response: str) -> EthicalAnchorResult:
    """
    Evaluate both prompt and response against all four ethical pillars.
    Returns a result indicating whether to hard-refuse, penalize, or pass.

    Called AFTER Contradiction Lattice, BEFORE Reflective Loop.
    """
    combined = (prompt + " " + response).lower()
    prompt_lower = prompt.lower()

    # ── Pillar 1: Hard harm signals ────────────────────────────────────────
    for category, signal, severity in HARD_HARM_SIGNALS:
        if signal in combined:
            return EthicalAnchorResult(
                refusal_type=RefusalType.HARD,
                pillar_triggered="harm_prevention",
                penalty_points=0,
                explanation=f"Hard refusal: {category} signal detected.",
                hard_refusal_reason=(
                    f"This request touches content that AERIS Lattice will not "
                    f"process regardless of context ({category}). "
                    f"If you are in crisis, please contact emergency services."
                )
            )

    # ── Pillar 4: Hard manipulation signals ────────────────────────────────
    for signal in HARD_MANIPULATION_SIGNALS:
        if signal in prompt_lower:
            return EthicalAnchorResult(
                refusal_type=RefusalType.HARD,
                pillar_triggered="manipulation_boundary",
                penalty_points=0,
                explanation="Hard refusal: manipulation or deception attempt detected.",
                hard_refusal_reason=(
                    "This request appears designed to facilitate harm to a third party. "
                    "AERIS Lattice will not process this content."
                )
            )

    # ── Collect weighted penalties ─────────────────────────────────────────
    total_penalty = 0
    triggered_pillars = []
    explanations = []

    # Pillar 1: Weighted harm
    for category, signal, penalty in WEIGHTED_HARM_SIGNALS:
        if signal in combined:
            total_penalty += penalty
            triggered_pillars.append("harm_prevention")
            explanations.append(f"Dangerous procedure signal: '{signal}'")

    # Pillar 2: Professional escalation
    for domain, config in PROFESSIONAL_ESCALATION_DOMAINS.items():
        for signal in config["signals"]:
            if signal in prompt_lower:
                total_penalty += config["penalty"]
                triggered_pillars.append("human_authority")
                explanations.append(config["explanation"])
                break  # one match per domain is enough

    # Pillar 3: Irreversibility
    for category, signal, penalty in IRREVERSIBILITY_SIGNALS:
        if signal in combined:
            total_penalty += penalty
            triggered_pillars.append("irreversibility")
            explanations.append(f"Irreversible action detected: '{signal}'")

    # Pillar 4: Weighted manipulation
    for category, signal, penalty in WEIGHTED_MANIPULATION_SIGNALS:
        if signal in combined:
            total_penalty += penalty
            triggered_pillars.append("manipulation_boundary")
            explanations.append(f"Manipulation signal: '{signal}'")

    # Cap total penalty at 100
    total_penalty = min(total_penalty, 100)

    if total_penalty > 0:
        primary_pillar = max(set(triggered_pillars), key=triggered_pillars.count)
        return EthicalAnchorResult(
            refusal_type=RefusalType.WEIGHTED,
            pillar_triggered=primary_pillar,
            penalty_points=total_penalty,
            explanation=" | ".join(set(explanations)),
            hard_refusal_reason=None
        )

    return EthicalAnchorResult(
        refusal_type=RefusalType.CLEAR,
        pillar_triggered=None,
        penalty_points=0,
        explanation="No ethical concerns detected.",
        hard_refusal_reason=None
    )

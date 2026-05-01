# backend/app/core/ethical_anchor.py
from dataclasses import dataclass
from enum import Enum


class RefusalType(str, Enum):
    HARD = "hard_refusal"
    WEIGHTED = "weighted"
    CLEAR = "clear"


@dataclass(frozen=True)
class EthicalAnchorResult:
    refusal_type: RefusalType
    pillar_triggered: str | None
    penalty_points: int
    explanation: str
    hard_refusal_reason: str | None = None


def evaluate_ethical_anchor(prompt: str, response: str) -> EthicalAnchorResult:
    """Lightweight but strict ethical boundary layer."""
    combined = (prompt + " " + response).lower()
    prompt_lower = prompt.lower()

    # Hard refusals
    if any(x in combined for x in ["how to hurt yourself", "end my life", "make a bomb", "synthesize poison"]):
        return EthicalAnchorResult(
            refusal_type=RefusalType.HARD,
            pillar_triggered="harm_prevention",
            penalty_points=0,
            explanation="Hard refusal: direct harm signal",
            hard_refusal_reason="This content cannot be processed."
        )

    if any(x in prompt_lower for x in ["how to manipulate", "phishing email", "scam", "blackmail"]):
        return EthicalAnchorResult(
            refusal_type=RefusalType.HARD,
            pillar_triggered="manipulation_boundary",
            penalty_points=0,
            explanation="Hard refusal: manipulation attempt",
            hard_refusal_reason="This request appears designed to facilitate harm."
        )

    # Weighted penalties (simplified)
    penalty = 0
    triggered = []

    if any(x in prompt_lower for x in ["should i take", "dosage", "my symptoms", "diagnose"]):
        penalty += 35
        triggered.append("medical")

    if any(x in prompt_lower for x in ["is it legal", "legal advice", "sue", "court"]):
        penalty += 30
        triggered.append("legal")

    if penalty > 0:
        return EthicalAnchorResult(
            refusal_type=RefusalType.WEIGHTED,
            pillar_triggered=triggered[0],
            penalty_points=min(penalty, 100),
            explanation="Professional domain boundary detected"
        )

    return EthicalAnchorResult(
        refusal_type=RefusalType.CLEAR,
        pillar_triggered=None,
        penalty_points=0,
        explanation="No ethical concerns"
    )

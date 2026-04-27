"""
AERIS Lattice v2 — Meta-Arbitration Engine
Layer 3 of the Dual Consensus System.

Combines:
    - External consensus score (Layer 1: OpenAI, Groq, Mistral, Gemini, Local)
    - Sovereign consensus score (Layer 2: Local agents)
    - Ethical Anchor verdict
    - Confidence Engine score
    - Contradiction Lattice result
    - Prompt risk tier

Produces a final, explainable delivery decision.

Weighting philosophy:
    External consensus tells us what the models agree on.
    Sovereign consensus tells us whether that agreement is safe.
    Ethical Anchor provides non-negotiable boundaries.
    The Meta-Engine combines all signals into one explainable trust score.
"""

from dataclasses import dataclass
from enum import Enum


class FinalVerdict(str, Enum):
    DELIVER = "deliver"
    SILENT = "silent"


@dataclass
class MetaArbitrationResult:
    verdict: FinalVerdict
    trust_score: int                  # 0–100 — final explainable trust score
    delivery_confidence: str          # "high" | "medium" | "low" | "none"
    primary_refusal_reason: str | None
    refusal_chain: list[str]          # Ordered list of what triggered refusal
    explanation: str                  # Human-readable for enterprise UI
    audit_record: dict                # Full structured record for compliance log


# ── Trust score weights ────────────────────────────────────────────────────────
# These can be tuned per domain in v2.1

WEIGHTS = {
    "external_consensus": 0.35,    # What 5 models agree on
    "sovereign_consensus": 0.35,   # What local agents determined
    "confidence_engine": 0.20,     # Linguistic confidence score
    "contradiction_clear": 0.10,   # Bonus for no contradiction
}

# Domain-specific threshold overrides
DOMAIN_THRESHOLDS = {
    "medical":      {"deliver": 80, "reflect": 60},
    "legal":        {"deliver": 78, "reflect": 58},
    "financial":    {"deliver": 75, "reflect": 55},
    "safety":       {"deliver": 85, "reflect": 65},
    "adversarial":  {"deliver": 95, "reflect": 90},  # Near-impossible to pass
    "general":      {"deliver": 62, "reflect": 48},
    "tier_a_safe":  {"deliver": 52, "reflect": 38},
    "general_health":    {"deliver": 58, "reflect": 44},
    "general_legal":     {"deliver": 58, "reflect": 44},
    "general_financial": {"deliver": 58, "reflect": 44},
}


def run_meta_arbitration(
    prompt: str,
    primary_response: str,
    external_consensus: dict,
    sovereign_consensus: dict | None,
    ethical_anchor: dict,
    confidence: dict,
    contradiction: dict,
    classification: dict
) -> MetaArbitrationResult:
    """
    Final arbitration across all validation layers.

    Parameters:
        prompt               — original user prompt
        primary_response     — response selected by external consensus
        external_consensus   — output from consensus_engine.calculate_consensus()
        sovereign_consensus  — output from sovereign_layer.run_sovereign_consensus() or None
        ethical_anchor       — output from ethical_anchor.evaluate_ethical_anchor()
        confidence           — output from confidence_engine.evaluate_confidence()
        contradiction        — output from contradiction_lattice.detect_contradiction()
        classification       — output from prompt_classifier.classify_prompt()
    """
    refusal_chain = []
    domain = classification.get("domain", "general")
    tier = classification.get("tier", "tier_b_medium")

    # ── Hard gates — immediate silent state ───────────────────────────────────

    # Ethical anchor hard refusal
    if ethical_anchor.get("refusal_type") == "hard_refusal":
        return MetaArbitrationResult(
            verdict=FinalVerdict.SILENT,
            trust_score=0,
            delivery_confidence="none",
            primary_refusal_reason="ethical_anchor_hard_refusal",
            refusal_chain=["ethical_anchor_hard_refusal"],
            explanation=ethical_anchor.get(
                "hard_refusal_reason",
                "Ethical boundary violation. This content cannot be processed."
            ),
            audit_record=_build_audit_record(
                prompt, primary_response, 0, "silent",
                "ethical_anchor_hard_refusal",
                ethical_anchor, external_consensus,
                sovereign_consensus, confidence, contradiction
            )
        )

    # Contradiction hard gate
    if contradiction.get("contradiction"):
        refusal_chain.append("contradiction_detected")

    # External consensus hard gate
    ext_score = external_consensus.get("consensus_score", 0)
    if ext_score < 40:
        refusal_chain.append("external_consensus_critically_low")

    # Sovereign veto gate
    if sovereign_consensus and sovereign_consensus.get("veto_applied"):
        return MetaArbitrationResult(
            verdict=FinalVerdict.SILENT,
            trust_score=0,
            delivery_confidence="none",
            primary_refusal_reason="sovereign_judge_veto",
            refusal_chain=["sovereign_judge_veto"] + refusal_chain,
            explanation=(
                f"Silent State Judge veto applied. "
                f"Reason: {sovereign_consensus.get('veto_reason', 'Insufficient reliability.')}"
            ),
            audit_record=_build_audit_record(
                prompt, primary_response, 0, "silent",
                "sovereign_judge_veto",
                ethical_anchor, external_consensus,
                sovereign_consensus, confidence, contradiction
            )
        )

    # ── Calculate composite trust score ───────────────────────────────────────

    # External consensus contribution (0–100)
    ext_contribution = ext_score * WEIGHTS["external_consensus"]

    # Sovereign consensus contribution (0–100)
    if sovereign_consensus:
        sov_score = sovereign_consensus.get("weighted_score", 50)
        sov_contribution = sov_score * WEIGHTS["sovereign_consensus"]
    else:
        # No sovereign layer — redistribute weight to external
        sov_contribution = ext_score * WEIGHTS["sovereign_consensus"]

    # Confidence engine contribution
    conf_score = confidence.get("score", 50)
    # Apply ethical anchor weighted penalty
    ethical_penalty = ethical_anchor.get("penalty_points", 0)
    adjusted_conf = max(0, conf_score - ethical_penalty)
    conf_contribution = adjusted_conf * WEIGHTS["confidence_engine"]

    # Contradiction bonus/penalty
    if contradiction.get("contradiction"):
        contra_contribution = 0
        refusal_chain.append("contradiction_penalty_applied")
    else:
        contra_contribution = 100 * WEIGHTS["contradiction_clear"]

    trust_score = round(
        ext_contribution +
        sov_contribution +
        conf_contribution +
        contra_contribution
    )
    trust_score = max(0, min(100, trust_score))

    # ── Domain threshold check ─────────────────────────────────────────────────
    thresholds = DOMAIN_THRESHOLDS.get(domain, DOMAIN_THRESHOLDS["general"])
    deliver_threshold = thresholds["deliver"]
    reflect_threshold = thresholds["reflect"]

    if trust_score >= deliver_threshold:
        delivery_confidence = "high" if trust_score >= 85 else "medium"
        verdict = FinalVerdict.DELIVER
        primary_refusal_reason = None
        explanation = (
            f"Response passed all validation layers. "
            f"Trust score: {trust_score}/100. "
            f"Domain: {domain}. Tier: {tier}."
        )
    elif trust_score >= reflect_threshold:
        # Borderline — treat as low confidence delivery with warning
        delivery_confidence = "low"
        verdict = FinalVerdict.DELIVER
        primary_refusal_reason = None
        refusal_chain.append("low_trust_score_warning")
        explanation = (
            f"Response delivered with low confidence. "
            f"Trust score: {trust_score}/100 (threshold: {deliver_threshold}). "
            f"Recommend verification."
        )
    else:
        delivery_confidence = "none"
        verdict = FinalVerdict.SILENT
        primary_refusal_reason = refusal_chain[0] if refusal_chain else "trust_score_below_threshold"
        if "trust_score_below_threshold" not in refusal_chain:
            refusal_chain.append("trust_score_below_threshold")
        explanation = (
            f"Trust score {trust_score}/100 below delivery threshold "
            f"of {deliver_threshold} for {domain} domain. "
            f"Response suppressed. Consult a qualified professional."
        )

    return MetaArbitrationResult(
        verdict=verdict,
        trust_score=trust_score,
        delivery_confidence=delivery_confidence,
        primary_refusal_reason=primary_refusal_reason,
        refusal_chain=refusal_chain,
        explanation=explanation,
        audit_record=_build_audit_record(
            prompt, primary_response, trust_score,
            verdict.value, primary_refusal_reason,
            ethical_anchor, external_consensus,
            sovereign_consensus, confidence, contradiction
        )
    )


def _build_audit_record(
    prompt, response, trust_score, verdict,
    refusal_reason, ethical_anchor, external_consensus,
    sovereign_consensus, confidence, contradiction
) -> dict:
    """Build full structured audit record for compliance logging."""
    return {
        "prompt_preview": prompt[:200],
        "response_preview": response[:200] if response else None,
        "trust_score": trust_score,
        "verdict": verdict,
        "refusal_reason": refusal_reason,
        "external_consensus_score": external_consensus.get("consensus_score"),
        "external_models_responded": external_consensus.get("models_responded", []),
        "external_semantic_similarity": external_consensus.get("semantic_similarity"),
        "sovereign_verdict": sovereign_consensus.get("sovereign_verdict") if sovereign_consensus else None,
        "sovereign_veto": sovereign_consensus.get("veto_applied") if sovereign_consensus else None,
        "ethical_anchor_pillar": ethical_anchor.get("pillar_triggered"),
        "ethical_anchor_penalty": ethical_anchor.get("penalty_points", 0),
        "confidence_score": confidence.get("score"),
        "confidence_domain": confidence.get("domain"),
        "contradiction_detected": contradiction.get("contradiction"),
        "contradiction_reason": contradiction.get("reason"),
    }

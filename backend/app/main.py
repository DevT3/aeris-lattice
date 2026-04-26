"""
AERIS Lattice v2 — Main Application
Dual Consensus Architecture with Tiered Routing, Ethical Anchor,
Sovereign Layer, and Meta-Arbitration Engine.

Pipeline (full Tier C/D):
    1. Prompt Classification (risk tier, domain, routing)
    2. External Consensus (tiered model selection)
    3. Ethical Anchor (outcome-based harm evaluation)
    4. Contradiction Lattice
    5. Sovereign Layer (local agents — Tier C/D only)
    6. Confidence Engine
    7. Reflective Loop (if needed)
    8. Meta-Arbitration Engine (final trust score + delivery decision)
    9. Decision Logging
"""

import re
from collections import defaultdict
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.models.request_models import AskRequest
from backend.app.services.llm_service import ask_all_models, ask_models_selective
from backend.app.core.confidence_engine import evaluate_confidence
from backend.app.core.reflective_loop import reflective_review
from backend.app.core.silent_state import enter_silent_state
from backend.app.core.contradiction_lattice import detect_contradiction
from backend.app.core.consensus_engine import calculate_consensus
from backend.app.core.logger import log_decision
from backend.app.core.prompt_classifier import classify_prompt, RiskTier
from backend.app.core.ethical_anchor import evaluate_ethical_anchor, RefusalType
from backend.app.core.sovereign_layer import run_sovereign_consensus
from backend.app.core.meta_arbitration import run_meta_arbitration, FinalVerdict
from backend.app.config import CONFIDENCE_THRESHOLD

app = FastAPI(
    title="AERIS Lattice v2",
    description="Dual Consensus reliability architecture for LLMs — inference-time validation"
)

app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")


@app.get("/")
def root():
    return {
        "status": "AERIS Lattice v2 Online",
        "message": "Dual Consensus — Epistemic validation active",
        "architecture": {
            "layer_1": "External consensus — OpenAI, Groq, Mistral, Gemini, Local",
            "layer_2": "Sovereign consensus — Skeptic, Compliance, Adversarial, Auditor, Judge",
            "layer_3": "Meta-Arbitration Engine"
        }
    }


@app.get("/demo")
def demo():
    return FileResponse("backend/app/static/index.html")


@app.get("/reliability")
def reliability_dashboard():
    return FileResponse("backend/app/static/dashboard.html")


@app.post("/ask")
def ask(request: AskRequest):

    # ── Step 1: Classify prompt → determine risk tier and routing ─────────────
    classification = classify_prompt(request.prompt)
    tier = classification.tier
    models_to_use = classification.models_required
    conf_threshold = classification.confidence_threshold

    # ── Step 2: Query models (tiered — not always all 5) ──────────────────────
    all_responses = ask_models_selective(request.prompt, models_to_use)

    # ── Step 3: External consensus ────────────────────────────────────────────
    external_consensus = calculate_consensus(all_responses)

    # Hard gate: consensus critically low
    if external_consensus["consensus_score"] < 40 or external_consensus["primary_response"] is None:
        log_decision(
            request.prompt, str(all_responses), 0,
            f"silent_state — no external consensus (tier: {tier})"
        )
        return {
            **enter_silent_state(),
            "tier": tier,
            "consensus": external_consensus,
            "all_model_responses": all_responses,
            "trust_score": 0,
            "refusal_reason": "external_consensus_critically_low"
        }

    response = external_consensus["primary_response"]

    # ── Step 4: Contradiction Lattice ─────────────────────────────────────────
    contradiction = detect_contradiction(response)

    # ── Step 5: Ethical Anchor ────────────────────────────────────────────────
    ethical_result = None
    if classification.ethical_anchor_required:
        ethical_result = evaluate_ethical_anchor(request.prompt, response)

        if ethical_result.refusal_type == RefusalType.HARD:
            log_decision(
                request.prompt, response, 0,
                f"silent_state — ethical_anchor_hard_refusal: {ethical_result.pillar_triggered}"
            )
            return {
                **enter_silent_state(),
                "tier": tier,
                "refusal_reason": "ethical_anchor_hard_refusal",
                "ethical_anchor": {
                    "pillar": ethical_result.pillar_triggered,
                    "explanation": ethical_result.hard_refusal_reason
                },
                "trust_score": 0
            }
    else:
        # Build a neutral ethical result for tiers that don't need it
        from backend.app.core.ethical_anchor import EthicalAnchorResult, RefusalType as RT
        ethical_result = EthicalAnchorResult(
            refusal_type=RT.CLEAR,
            pillar_triggered=None,
            penalty_points=0,
            explanation="Ethical anchor not required for this tier.",
            hard_refusal_reason=None
        )

    # ── Step 6: Sovereign Layer (Tier C and D only) ───────────────────────────
    sovereign_result = None
    if classification.sovereign_layer_required:
        sovereign_result = run_sovereign_consensus(request.prompt, response)

        if sovereign_result.get("veto_applied"):
            log_decision(
                request.prompt, response, 0,
                f"silent_state — sovereign_judge_veto"
            )
            return {
                **enter_silent_state(),
                "tier": tier,
                "refusal_reason": "sovereign_judge_veto",
                "sovereign_layer": sovereign_result,
                "trust_score": 0
            }

    # ── Step 7: Confidence Engine ─────────────────────────────────────────────
    confidence = evaluate_confidence(response, request.prompt)

    # Apply ethical penalty to confidence score if weighted
    if ethical_result and ethical_result.penalty_points > 0:
        original_score = confidence["score"]
        confidence["score"] = max(0, original_score - ethical_result.penalty_points)
        confidence["ethical_penalty_applied"] = ethical_result.penalty_points
        confidence["reason"] = (
            f"{confidence['reason']} | "
            f"Ethical anchor penalty: -{ethical_result.penalty_points} pts "
            f"({ethical_result.pillar_triggered})"
        )

    # ── Step 8: Reflective Loop ───────────────────────────────────────────────
    if confidence["score"] < conf_threshold:
        response = reflective_review(response)
        confidence = evaluate_confidence(response, request.prompt)

        if confidence["score"] < conf_threshold:
            log_decision(
                request.prompt, response, confidence["score"],
                f"silent_state — low confidence after reflection (tier: {tier})"
            )
            return {
                **enter_silent_state(),
                "tier": tier,
                "refusal_reason": "low_confidence_after_reflection",
                "confidence": confidence,
                "consensus": external_consensus,
                "trust_score": 0
            }

    # ── Step 9: Meta-Arbitration Engine ──────────────────────────────────────
    meta_result = run_meta_arbitration(
        prompt=request.prompt,
        primary_response=response,
        external_consensus=external_consensus,
        sovereign_consensus=sovereign_result,
        ethical_anchor={
            "refusal_type": ethical_result.refusal_type,
            "pillar_triggered": ethical_result.pillar_triggered,
            "penalty_points": ethical_result.penalty_points,
            "explanation": ethical_result.explanation
        },
        confidence=confidence,
        contradiction=contradiction,
        classification={
            "tier": tier,
            "domain": classification.domain,
            "risk_signals": classification.risk_signals
        }
    )

    # ── Step 10: Final delivery or silent state ───────────────────────────────
    if meta_result.verdict == FinalVerdict.SILENT:
        log_decision(
            request.prompt, response,
            meta_result.trust_score,
            f"silent_state — meta_arbitration: {meta_result.primary_refusal_reason}"
        )
        return {
            **enter_silent_state(),
            "tier": tier,
            "trust_score": meta_result.trust_score,
            "delivery_confidence": meta_result.delivery_confidence,
            "refusal_reason": meta_result.primary_refusal_reason,
            "refusal_chain": meta_result.refusal_chain,
            "explanation": meta_result.explanation,
            "consensus": external_consensus,
            "all_model_responses": all_responses
        }

    log_decision(
        request.prompt, response,
        meta_result.trust_score,
        f"delivered — trust_score: {meta_result.trust_score} tier: {tier}"
    )

    return {
        "final_response": response,
        "trust_score": meta_result.trust_score,
        "delivery_confidence": meta_result.delivery_confidence,
        "tier": tier,
        "domain": classification.domain,
        "risk_signals": classification.risk_signals,
        "confidence": confidence,
        "contradiction_check": contradiction,
        "consensus": external_consensus,
        "sovereign_layer": sovereign_result,
        "ethical_anchor": {
            "pillar": ethical_result.pillar_triggered,
            "penalty": ethical_result.penalty_points,
            "explanation": ethical_result.explanation
        },
        "explanation": meta_result.explanation,
        "all_model_responses": all_responses
    }


# ── Reliability dashboard API ─────────────────────────────────────────────────

@app.get("/api/reliability-stats")
def reliability_stats():
    try:
        with open("decision_log.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {
            "total": 0, "delivered": 0, "silent": 0,
            "reliability_rate": 0, "avg_confidence": None,
            "domains": {}, "recent": []
        }

    entries = []
    blocks = content.strip().split("-" * 60)

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        try:
            time_match   = re.search(r'\[(.+?)\]', block)
            prompt_match = re.search(r'Prompt: (.+)', block)
            conf_match   = re.search(r'Confidence score: (\d+)', block)
            status_match = re.search(r'Status: (.+)', block)

            if not all([time_match, prompt_match, status_match]):
                continue

            entries.append({
                "time":       time_match.group(1)[:19],
                "prompt":     prompt_match.group(1)[:80],
                "confidence": int(conf_match.group(1)) if conf_match else None,
                "status":     status_match.group(1).strip()
            })
        except Exception:
            continue

    if not entries:
        return {
            "total": 0, "delivered": 0, "silent": 0,
            "reliability_rate": 0, "avg_confidence": None,
            "domains": {}, "recent": []
        }

    total     = len(entries)
    silent    = sum(1 for e in entries if "silent" in e["status"])
    delivered = total - silent

    conf_scores = [
        e["confidence"] for e in entries
        if e["confidence"] and "silent" not in e["status"]
    ]
    avg_confidence = round(sum(conf_scores) / len(conf_scores)) if conf_scores else None
    reliability_rate = round((delivered / total) * 100, 1) if total > 0 else 0

    domains = defaultdict(lambda: {"total": 0, "silent": 0})
    for entry in entries:
        status = entry["status"]
        if "contradiction" in status:
            domain = "contradiction"
        elif "low confidence" in status:
            domain = "low_confidence"
        elif "no consensus" in status:
            domain = "no_consensus"
        elif "ethical" in status:
            domain = "ethical_anchor"
        elif "sovereign" in status:
            domain = "sovereign_veto"
        elif "meta" in status:
            domain = "meta_arbitration"
        else:
            domain = "delivered"

        domains[domain]["total"] += 1
        if "silent" in status:
            domains[domain]["silent"] += 1

    return {
        "total":            total,
        "delivered":        delivered,
        "silent":           silent,
        "reliability_rate": reliability_rate,
        "avg_confidence":   avg_confidence,
        "domains":          dict(domains),
        "recent":           list(reversed(entries))[:20]
    }

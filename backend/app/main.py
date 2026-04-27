"""
AERIS Lattice v2 — Main Application
Dual Consensus Architecture with Tiered Routing, Ethical Anchor,
Sovereign Layer, and Meta-Arbitration Engine.

New in this version:
    - mode parameter: "optimized" (tiered) or "full" (all 5 models always)
    - Token usage tracking per model and aggregate
    - Response latency per model and aggregate
"""

import re
import glob
import json
import time
from collections import defaultdict
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.models.request_models import AskRequest
from backend.app.services.llm_service import (
    ask_models_selective,
    compute_usage_summary,
    extract_text_responses,
    ALL_MODELS
)
from backend.app.core.confidence_engine import evaluate_confidence
from backend.app.core.reflective_loop import reflective_review
from backend.app.core.silent_state import enter_silent_state
from backend.app.core.contradiction_lattice import detect_contradiction
from backend.app.core.consensus_engine import calculate_consensus
from backend.app.core.logger import log_decision
from backend.app.core.prompt_classifier import classify_prompt
from backend.app.core.ethical_anchor import (
    evaluate_ethical_anchor, RefusalType, EthicalAnchorResult
)
from backend.app.core.sovereign_layer import run_sovereign_consensus
from backend.app.core.meta_arbitration import run_meta_arbitration, FinalVerdict

app = FastAPI(
    title="AERIS Lattice v2",
    description="Dual Consensus reliability architecture for LLMs — inference-time validation"
)

app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")


# ── Helper ─────────────────────────────────────────────────────────────────────

def silent_response(
    all_responses: dict,
    tier: str,
    consensus: dict,
    trust_score: int,
    refusal_reason: str,
    usage: dict = None,
    total_latency_ms: int = None,
    model_stats: dict = None,
    mode: str = "optimized",
    **extra
) -> dict:
    silent = enter_silent_state()
    return {
        "status":              silent["status"],
        "message":             silent["message"],
        "tier":                tier,
        "consensus":           consensus,
        "trust_score":         trust_score,
        "refusal_reason":      refusal_reason,
        "all_model_responses": all_responses,
        "model_stats":         model_stats or {},
        "usage":               usage or {},
        "total_latency_ms":    total_latency_ms,
        "mode":                mode,
        **extra
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

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
    request_start = time.time()

    # Step 1: Classify prompt
    classification = classify_prompt(request.prompt)
    tier           = classification.tier
    conf_threshold = classification.confidence_threshold

    # Step 2: Determine models based on mode
    # "full"      → always all 5 models
    # "optimized" → tiered routing (default, saves tokens)
    mode = getattr(request, "mode", "optimized") or "optimized"
    models_to_use = ALL_MODELS if mode == "full" else classification.models_required

    # Step 3: Query models — get rich results with token/latency data
    raw_results    = ask_models_selective(request.prompt, models_to_use)
    usage_summary  = compute_usage_summary(raw_results)
    text_responses = extract_text_responses(raw_results)
    total_latency  = round((time.time() - request_start) * 1000)

    all_model_responses = {
        name: (r["text"] if isinstance(r, dict) else r)
        for name, r in raw_results.items()
    }

    model_stats = {
        name: {
            "tokens_in":  r.get("tokens_in"),
            "tokens_out": r.get("tokens_out"),
            "latency_ms": r.get("latency_ms"),
            "error":      r.get("error", False)
        }
        for name, r in raw_results.items()
        if isinstance(r, dict)
    }

    # Step 4: External consensus
    external_consensus = calculate_consensus(text_responses)

    if external_consensus["consensus_score"] < 40 or external_consensus["primary_response"] is None:
        log_decision(request.prompt, str(text_responses), 0,
                     f"silent_state — no external consensus (tier: {tier})")
        return silent_response(
            all_model_responses, tier, external_consensus, 0,
            "external_consensus_critically_low",
            usage=usage_summary, total_latency_ms=total_latency,
            model_stats=model_stats, mode=mode
        )

    response = external_consensus["primary_response"]

    # Step 5: Contradiction Lattice
    contradiction = detect_contradiction(response)

    # Step 6: Ethical Anchor
    if classification.ethical_anchor_required:
        ethical_result = evaluate_ethical_anchor(request.prompt, response)
        if ethical_result.refusal_type == RefusalType.HARD:
            log_decision(request.prompt, response, 0,
                         f"silent_state — ethical_anchor_hard_refusal: {ethical_result.pillar_triggered}")
            return silent_response(
                all_model_responses, tier, external_consensus, 0,
                "ethical_anchor_hard_refusal",
                usage=usage_summary, total_latency_ms=total_latency,
                model_stats=model_stats, mode=mode,
                ethical_anchor={
                    "pillar":      ethical_result.pillar_triggered,
                    "explanation": ethical_result.hard_refusal_reason
                }
            )
    else:
        ethical_result = EthicalAnchorResult(
            refusal_type=RefusalType.CLEAR,
            pillar_triggered=None,
            penalty_points=0,
            explanation="Ethical anchor not required for this tier.",
            hard_refusal_reason=None
        )

    # Step 7: Sovereign Layer (Tier C/D only)
    sovereign_result = None
    if classification.sovereign_layer_required:
        sovereign_result = run_sovereign_consensus(request.prompt, response)
        if sovereign_result.get("veto_applied"):
            log_decision(request.prompt, response, 0, "silent_state — sovereign_judge_veto")
            return silent_response(
                all_model_responses, tier, external_consensus, 0,
                "sovereign_judge_veto",
                usage=usage_summary, total_latency_ms=total_latency,
                model_stats=model_stats, mode=mode,
                sovereign_layer=sovereign_result
            )

    # Step 8: Confidence Engine
    confidence = evaluate_confidence(response, request.prompt)

    if ethical_result and ethical_result.penalty_points > 0:
        confidence["score"] = max(0, confidence["score"] - ethical_result.penalty_points)
        confidence["ethical_penalty_applied"] = ethical_result.penalty_points
        confidence["reason"] = (
            f"{confidence['reason']} | "
            f"Ethical anchor penalty: -{ethical_result.penalty_points} pts "
            f"({ethical_result.pillar_triggered})"
        )

    # Step 9: Reflective Loop
    if confidence["score"] < conf_threshold:
        response   = reflective_review(response)
        confidence = evaluate_confidence(response, request.prompt)
        if confidence["score"] < conf_threshold:
            log_decision(request.prompt, response, confidence["score"],
                         f"silent_state — low confidence after reflection (tier: {tier})")
            return silent_response(
                all_model_responses, tier, external_consensus, 0,
                "low_confidence_after_reflection",
                usage=usage_summary, total_latency_ms=total_latency,
                model_stats=model_stats, mode=mode,
                confidence=confidence
            )

    # Step 10: Meta-Arbitration Engine
    meta_result = run_meta_arbitration(
        prompt=request.prompt,
        primary_response=response,
        external_consensus=external_consensus,
        sovereign_consensus=sovereign_result,
        ethical_anchor={
            "refusal_type":     ethical_result.refusal_type,
            "pillar_triggered": ethical_result.pillar_triggered,
            "penalty_points":   ethical_result.penalty_points,
            "explanation":      ethical_result.explanation
        },
        confidence=confidence,
        contradiction=contradiction,
        classification={
            "tier":         tier,
            "domain":       classification.domain,
            "risk_signals": classification.risk_signals
        }
    )

    # Step 11: Final decision
    if meta_result.verdict == FinalVerdict.SILENT:
        log_decision(request.prompt, response, meta_result.trust_score,
                     f"silent_state — meta_arbitration: {meta_result.primary_refusal_reason}")
        return silent_response(
            all_model_responses, tier, external_consensus,
            meta_result.trust_score, meta_result.primary_refusal_reason,
            usage=usage_summary, total_latency_ms=total_latency,
            model_stats=model_stats, mode=mode,
            delivery_confidence=meta_result.delivery_confidence,
            refusal_chain=meta_result.refusal_chain,
            explanation=meta_result.explanation
        )

    log_decision(request.prompt, response, meta_result.trust_score,
                 f"delivered — trust_score: {meta_result.trust_score} tier: {tier} mode: {mode}")

    return {
        "final_response":      response,
        "trust_score":         meta_result.trust_score,
        "delivery_confidence": meta_result.delivery_confidence,
        "tier":                tier,
        "domain":              classification.domain,
        "risk_signals":        classification.risk_signals,
        "mode":                mode,
        "confidence":          confidence,
        "contradiction_check": contradiction,
        "consensus":           external_consensus,
        "sovereign_layer":     sovereign_result,
        "ethical_anchor": {
            "pillar":      ethical_result.pillar_triggered,
            "penalty":     ethical_result.penalty_points,
            "explanation": ethical_result.explanation
        },
        "explanation":         meta_result.explanation,
        "all_model_responses": all_model_responses,
        "model_stats":         model_stats,
        "usage":               usage_summary,
        "total_latency_ms":    total_latency
    }


# ── Reliability stats ──────────────────────────────────────────────────────────

@app.get("/api/reliability-stats")
def reliability_stats():
    try:
        with open("decision_log.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {"total": 0, "delivered": 0, "silent": 0,
                "reliability_rate": 0, "avg_confidence": None,
                "domains": {}, "recent": []}

    entries = []
    for block in content.strip().split("-" * 60):
        block = block.strip()
        if not block:
            continue
        try:
            tm = re.search(r'\[(.+?)\]', block)
            pm = re.search(r'Prompt: (.+)', block)
            cm = re.search(r'Confidence score: (\d+)', block)
            sm = re.search(r'Status: (.+)', block)
            if not all([tm, pm, sm]):
                continue
            entries.append({
                "time":       tm.group(1)[:19],
                "prompt":     pm.group(1)[:80],
                "confidence": int(cm.group(1)) if cm else None,
                "status":     sm.group(1).strip()
            })
        except Exception:
            continue

    if not entries:
        return {"total": 0, "delivered": 0, "silent": 0,
                "reliability_rate": 0, "avg_confidence": None,
                "domains": {}, "recent": []}

    total     = len(entries)
    silent    = sum(1 for e in entries if "silent" in e["status"])
    delivered = total - silent
    conf_scores = [e["confidence"] for e in entries
                   if e["confidence"] and "silent" not in e["status"]]
    avg_confidence   = round(sum(conf_scores) / len(conf_scores)) if conf_scores else None
    reliability_rate = round((delivered / total) * 100, 1) if total > 0 else 0

    domains = defaultdict(lambda: {"total": 0, "silent": 0})
    for entry in entries:
        s = entry["status"]
        if "contradiction" in s:    d = "contradiction"
        elif "low confidence" in s: d = "low_confidence"
        elif "no consensus" in s:   d = "no_consensus"
        elif "ethical" in s:        d = "ethical_anchor"
        elif "sovereign" in s:      d = "sovereign_veto"
        elif "meta" in s:           d = "meta_arbitration"
        else:                       d = "delivered"
        domains[d]["total"] += 1
        if "silent" in s:
            domains[d]["silent"] += 1

    return {
        "total": total, "delivered": delivered, "silent": silent,
        "reliability_rate": reliability_rate, "avg_confidence": avg_confidence,
        "domains": dict(domains), "recent": list(reversed(entries))[:20]
    }


@app.post("/api/reset-stats")
def reset_stats():
    try:
        with open("decision_log.txt", "w", encoding="utf-8") as f:
            f.write("")
        return {"status": "reset", "message": "Decision log cleared."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/benchmark-latest")
def benchmark_latest():
    files = sorted(glob.glob("tests/benchmark_results/benchmark_*.json"))
    if not files:
        raise HTTPException(status_code=404,
                            detail="No benchmark results found. Run: python tests/run_benchmark.py --version v1.0")
    with open(files[-1], "r") as f:
        return json.load(f)


@app.get("/tests/benchmark_suite.json")
def serve_benchmark_suite():
    return FileResponse("tests/benchmark_suite.json", media_type="application/json")

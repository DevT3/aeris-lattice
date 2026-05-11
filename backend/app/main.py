# backend/app/main.py
"""
AERIS Lattice v3.1 — Main Application (Windows-safe version)
"""

import sys
from pathlib import Path

# ── CRITICAL WINDOWS FIX ── must be at the VERY TOP
ROOT = Path(__file__).resolve().parents[2]   # points to aeris-lattice/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))    # extra safety for reloader

import json
import time
import asyncio
import functools
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.models.request_models import AskRequest
from backend.app.services.llm_service import ask_models_parallel, compute_usage_summary, extract_text_responses, ALL_MODELS
from backend.app.core.config import settings
from backend.app.core.prompt_classifier import classify_prompt, ClassificationResult
from backend.app.core.consensus_engine import calculate_consensus
from backend.app.core.contradiction_lattice import detect_contradiction
from backend.app.core.confidence_engine import evaluate_confidence
from backend.app.core.ethical_anchor import evaluate_ethical_anchor, RefusalType
from backend.app.core.reflective_loop import reflective_review, is_reflection_refusal, extract_refusal_reason
from backend.app.core.sovereign_layer import run_sovereign_consensus
from backend.app.core.meta_arbitration import run_meta_arbitration, FinalVerdict
from backend.app.core.silent_state import enter_silent_state
from backend.app.core.escalation_logger import log_escalation


app = FastAPI(
    title="AERIS Lattice v3.1",
    description="Dual Consensus reliability middleware — async + Human-in-the-Loop ready",
    version="3.1.0",
)

app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")


# ── Structured JSON logging ───────────────────────────────────────────────────
def log_decision(payload: dict):
    log_entry = {"timestamp": datetime.utcnow().isoformat(), **payload}
    try:
        with open(settings.DECISION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # never block the request


# ── Silent response with Human-in-the-Loop hook ───────────────────────────────
def silent_response(
    all_responses: dict,
    tier: str,
    domain: str,
    consensus: dict,
    trust_score: int,
    refusal_reason: str,
    usage: dict,
    total_latency_ms: int,
    model_stats: dict,
    mode: str,
    refusal_chain: list | None = None,
    sovereign_layer: dict | None = None,
    **extra,
) -> dict:
    silent = enter_silent_state()

    # Human-in-the-Loop escalation (Tier C/D)
    if tier in ("tier_c_high", "tier_d_adversarial"):
        escalation = {
            "event": "silent_state_escalation",
            "timestamp": datetime.utcnow().isoformat(),
            "tier": tier,
            "domain": domain,
            "refusal_reason": refusal_reason,
            "refusal_chain": refusal_chain or [],
            "trust_score": trust_score,
            "prompt_preview": extra.get("prompt_preview", "")[:200],
            "sovereign_layer": sovereign_layer,
        }
        print("\n🔥 HUMAN-IN-THE-LOOP ESCALATION TRIGGERED:")
        print(json.dumps(escalation, indent=2))
        # Day 2: we will POST this to a webhook here

    return {
        "status": silent["status"],
        "message": silent["message"],
        "tier": tier,
        "domain": domain,
        "consensus": consensus,
        "trust_score": trust_score,
        "refusal_reason": refusal_reason,
        "refusal_chain": refusal_chain or [],
        "all_model_responses": all_responses,
        "model_stats": model_stats,
        "usage": usage,
        "total_latency_ms": total_latency_ms,
        "mode": mode,
        "sovereign_layer": sovereign_layer,
        **extra,
    }


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "AERIS Lattice v3.1 Online", "version": "3.1.0"}


@app.get("/demo")
def demo():
    return FileResponse("backend/app/static/index.html")


@app.get("/reliability")
def reliability_dashboard():
    return FileResponse("backend/app/static/dashboard.html")


@app.post("/ask")
async def ask(request: AskRequest):
    request_start = time.time()

    # Step 1: Classify prompt
    classification = classify_prompt(request.prompt)

    # ── CRITICAL FIX: Force sovereign + full models for Tier C/D (fixes Silent State bug) ──
    if classification.tier.value in ("tier_c_high", "tier_d_adversarial"):
        classification = ClassificationResult(
            tier=classification.tier,
            domain=classification.domain,
            risk_signals=classification.risk_signals,
            confidence_threshold=classification.confidence_threshold,
            models_required=ALL_MODELS,
            ethical_anchor_required=True,
            sovereign_layer_required=True
        )

    # Step 2: Handle mode (never mutate frozen dataclass)
    mode = getattr(request, "mode", "optimized") or "optimized"

    if mode in ("sovereign", "full + sovereign"):
        # Force full models + sovereign layer
        models_to_use = ALL_MODELS
        # Create a fresh ClassificationResult instead of mutating
        classification = ClassificationResult(
            tier=classification.tier,
            domain=classification.domain,
            risk_signals=classification.risk_signals,
            confidence_threshold=classification.confidence_threshold,
            models_required=ALL_MODELS,
            ethical_anchor_required=True,
            sovereign_layer_required=True
        )
    elif mode == "full":
        models_to_use = ALL_MODELS
    else:
        models_to_use = classification.models_required

    # Step 3: Parallel model queries
    raw_results = await ask_models_parallel(request.prompt, models_to_use)
    usage_summary = compute_usage_summary(raw_results)
    text_responses = extract_text_responses(raw_results)
    total_latency_ms = round((time.time() - request_start) * 1000)

    all_model_responses = {name: (r.get("text") if isinstance(r, dict) else r) for name, r in raw_results.items()}
    model_stats = {name: {
        "tokens_in": r.get("tokens_in"),
        "tokens_out": r.get("tokens_out"),
        "latency_ms": r.get("latency_ms"),
        "error": r.get("error", False),
        "timed_out": r.get("timed_out", False),
    } for name, r in raw_results.items() if isinstance(r, dict)}

    # Step 4: External consensus
    external_consensus = calculate_consensus(text_responses)
    if external_consensus["consensus_score"] < 40 or external_consensus["primary_response"] is None:
        log_decision({"prompt": request.prompt, "status": "silent_state", "refusal_reason": "external_consensus_critically_low", "tier": classification.tier.value, "domain": classification.domain})
        return silent_response(all_model_responses, classification.tier.value, classification.domain, external_consensus, 0, "external_consensus_critically_low", usage_summary, total_latency_ms, model_stats, mode)

    response = external_consensus["primary_response"]

    # Step 5: Contradiction Lattice
    contradiction = detect_contradiction(response, classification.domain)
    if contradiction.contradiction and contradiction.severity == "critical" and mode not in ("sovereign", "full + sovereign"):
        log_decision({"prompt": request.prompt, "status": "silent_state", "refusal_reason": "critical_contradiction_detected", "tier": classification.tier.value, "domain": classification.domain})
        return silent_response(all_model_responses, classification.tier.value, classification.domain, external_consensus, 0, "critical_contradiction_detected", usage_summary, total_latency_ms, model_stats, mode, contradiction=contradiction.__dict__)

    # Step 6: Sovereign Layer
    sovereign_result = None
    if classification.sovereign_layer_required:
        loop = asyncio.get_running_loop()
        sovereign_result = await loop.run_in_executor(None, run_sovereign_consensus, request.prompt, response)
        if sovereign_result.get("veto_applied"):
            log_decision({"prompt": request.prompt, "status": "silent_state", "refusal_reason": "sovereign_judge_veto", "tier": classification.tier.value, "domain": classification.domain})
            return silent_response(all_model_responses, classification.tier.value, classification.domain, external_consensus, 0, "sovereign_judge_veto", usage_summary, total_latency_ms, model_stats, mode, sovereign_layer=sovereign_result)

    # Step 7–10: Ethical, Confidence, Reflective, Meta-Arbitration
    ethical_result = evaluate_ethical_anchor(request.prompt, response) if classification.ethical_anchor_required else None
    confidence = evaluate_confidence(response, request.prompt, classification.domain)

    if confidence.score < classification.confidence_threshold and mode not in ("sovereign", "full + sovereign"):
        loop = asyncio.get_running_loop()
        revised = await loop.run_in_executor(None, functools.partial(reflective_review, response, request.prompt, classification.domain))
        if is_reflection_refusal(revised):
            reason = extract_refusal_reason(revised)
            log_decision({"prompt": request.prompt, "status": "silent_state", "refusal_reason": "reflection_refusal", "tier": classification.tier.value, "domain": classification.domain})
            return silent_response(all_model_responses, classification.tier.value, classification.domain, external_consensus, 0, "reflection_refusal", usage_summary, total_latency_ms, model_stats, mode, reflection_reason=reason)
        response = revised
        confidence = evaluate_confidence(response, request.prompt, classification.domain)

    meta_result = run_meta_arbitration(
        prompt=request.prompt,
        primary_response=response,
        external_consensus=external_consensus,
        sovereign_consensus=sovereign_result,
        ethical_anchor=ethical_result.__dict__ if ethical_result else {},
        confidence=confidence.__dict__,
        contradiction=contradiction.__dict__,
        classification={"tier": classification.tier.value, "domain": classification.domain},
    )

            # Step 11: Final decision
    if meta_result.verdict == FinalVerdict.SILENT:
        print(">>> SILENT STATE BLOCK EXECUTED in main.py")   # ← new loud print

        log_decision({"prompt": request.prompt, "status": "silent_state", "refusal_reason": meta_result.primary_refusal_reason, "trust_score": meta_result.trust_score, "tier": classification.tier.value, "domain": classification.domain})

        # ── NEW: Trigger Human-in-the-Loop escalation logging ──
        escalation_payload = {
            "prompt_preview": request.prompt[:200],
            "tier": classification.tier.value,
            "domain": classification.domain,
            "refusal_reason": meta_result.primary_refusal_reason,
            "trust_score": meta_result.trust_score,
            "refusal_chain": meta_result.refusal_chain,
            "sovereign_layer": sovereign_result,
            "external_consensus": external_consensus,
            "confidence": confidence.__dict__ if 'confidence' in locals() else {},
        }
        print(">>> ABOUT TO CALL log_escalation() FROM MAIN.PY")
        log_escalation(escalation_payload)

        return silent_response(all_model_responses, classification.tier.value, classification.domain, external_consensus, meta_result.trust_score, meta_result.primary_refusal_reason, usage_summary, total_latency_ms, model_stats, mode, refusal_chain=meta_result.refusal_chain, sovereign_layer=sovereign_result, prompt_preview=request.prompt[:200])

    # Delivered
    log_decision({"prompt": request.prompt, "status": "delivered", "trust_score": meta_result.trust_score, "tier": classification.tier.value, "domain": classification.domain})

    return {
        "final_response": response,
        "trust_score": meta_result.trust_score,
        "delivery_confidence": meta_result.delivery_confidence,
        "tier": classification.tier.value,
        "domain": classification.domain,
        "mode": mode,
        "confidence": confidence.__dict__,
        "contradiction_check": contradiction.__dict__,
        "consensus": external_consensus,
        "sovereign_layer": sovereign_result,
        "ethical_anchor": ethical_result.__dict__ if ethical_result else {},
        "explanation": meta_result.explanation,
        "all_model_responses": all_model_responses,
        "model_stats": model_stats,
        "usage": usage_summary,
        "total_latency_ms": total_latency_ms,
    }

@app.get("/api/reliability-stats")
def reliability_stats():
    """Parse decision_log.txt and return real live stats (no hardcoding)"""
    try:
        with open(settings.DECISION_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    total = len(lines)
    delivered = 0
    silent = 0
    confidence_sum = 0
    conf_count = 0
    recent = []
    domains = {}

    for line in lines[-50:]:  # last 50 for recent + performance
        try:
            entry = json.loads(line.strip())
            if entry.get("status") == "delivered":
                delivered += 1
                if "trust_score" in entry:
                    confidence_sum += entry["trust_score"]
                    conf_count += 1
            elif "silent" in entry.get("status", ""):
                silent += 1

            recent.append({
                "time": entry.get("timestamp", "")[:19].replace("T", " "),
                "prompt": entry.get("prompt", "")[:80] + ("..." if len(entry.get("prompt", "")) > 80 else ""),
                "confidence": entry.get("trust_score"),
                "domain": entry.get("domain", "general"),
                "status": entry.get("status", "")
            })

            # domain count
            d = entry.get("domain", "general")
            if d not in domains:
                domains[d] = {"total": 0, "silent": 0}
            domains[d]["total"] += 1
            if "silent" in entry.get("status", ""):
                domains[d]["silent"] += 1
        except:
            continue

    reliability_rate = round((delivered / total * 100) if total > 0 else 100)
    avg_confidence = round(confidence_sum / conf_count) if conf_count > 0 else None

    return {
        "total": total,
        "delivered": delivered,
        "silent": silent,
        "reliability_rate": reliability_rate,
        "avg_confidence": avg_confidence,
        "domains": domains,
        "recent": recent[::-1]  # newest first
    }


@app.post("/api/reset-stats")
def reset_stats():
    """Truncate decision_log.txt (benchmark JSON files untouched)"""
    try:
        with open(settings.DECISION_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("")
        return {"status": "success", "message": "Stats reset successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/benchmark-latest")
def benchmark_latest():
    """Return latest benchmark results"""
    import glob
    files = sorted(glob.glob("tests/benchmark_results/benchmark_*.json"))
    if not files:
        return {"version": "v3.1", "summary": {"weighted_reliability_score": 100, "dangerous_delivery_rate": 0}}
    with open(files[-1], "r") as f:
        return json.load(f)
    

@app.get("/api/benchmark-suite")
def get_benchmark_suite():
    """Serve the full benchmark suite to the UI Benchmark tab"""
    try:
        with open("tests/benchmark_suite.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Benchmark suite not found. Run python tests/run_benchmark.py first."}
    except Exception as e:
        return {"error": str(e)}

    
@app.post("/api/reset-stats")
def reset_stats():
    """Truncate decision_log.txt to reset all stats (benchmark results are preserved)"""
    try:
        with open(settings.DECISION_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("")  # clear the file
        return {"status": "success", "message": "Stats reset successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/escalations")
def list_escalations():
    """Return all pending Human-in-the-Loop escalations"""
    try:
        with open("escalation_log.jsonl", "r", encoding="utf-8") as f:
            lines = f.readlines()
        records = [json.loads(line.strip()) for line in lines if line.strip()]
        return {"total": len(records), "escalations": records[-50:]}  # last 50
    except FileNotFoundError:
        return {"total": 0, "escalations": []}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/escalate")
async def escalate(request: dict):
    """Manual escalation endpoint (for external systems)"""
    log_escalation(request)
    return {"status": "escalated", "message": "Human-in-the-Loop escalation logged"}
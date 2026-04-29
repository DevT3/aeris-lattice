# AERIS Lattice v3 — Architecture Reference

## Overview

AERIS v3.1 implements an 11-step validation pipeline organized across 3 consensus layers. The system is async-first: all cloud model queries fire simultaneously. All downstream validation steps run sequentially after model responses are collected.

**Benchmark (v3.1):** 32/32 · 100% weighted reliability · 0% dangerous delivery · 0% false refusal

---

## Full pipeline

```
User Prompt
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 1 — Prompt Classifier                                          │
│                                                                      │
│  Input:  raw prompt string                                           │
│  Output: tier · domain · models_required · thresholds               │
│                                                                      │
│  Tier A — Safe:        TIER_A_SAFE_PATTERNS match (fast path)        │
│  Tier B — Medium:      TIER_B_DOMAINS match                          │
│  Tier C — High Risk:   TIER_C_DOMAINS match (medical/legal/financial)│
│  Tier D — Adversarial: TIER_D_SIGNALS match (jailbreaks/injection)   │
│                                                                      │
│  File: backend/app/core/prompt_classifier.py                         │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 2 — Mode and Model Selection                                   │
│                                                                      │
│  mode="optimized": tiered routing per classifier                     │
│    Tier A: ["openai", "groq"]                — 2 models             │
│    Tier B: ["openai", "groq", "gemini"]      — 3 models             │
│    Tier C/D: ["openai", "groq", "mistral", "gemini"] — 4 models     │
│                                                                      │
│  mode="full": all 4 cloud models regardless of tier                  │
│                                                                      │
│  mode="sovereign": all 4 cloud models + forced sovereign + ethical   │
│    anchor required · contradiction and reflection gates bypassed     │
│                                                                      │
│  File: backend/app/main.py                                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 3 — Parallel Model Queries                                     │
│                                                                      │
│  asyncio.gather() fires all model calls simultaneously.              │
│  Native async: OpenAI (AsyncOpenAI), Groq (AsyncGroq)               │
│  Executor-wrapped: Mistral, Gemini (no native async client)          │
│                                                                      │
│  Per-model timeout: MODEL_TIMEOUT_S = 12.0 seconds                   │
│  On timeout: model marked timed_out=True, excluded from consensus    │
│  System proceeds with partial consensus from remaining models        │
│                                                                      │
│  Latency improvement:                                                │
│    Sequential (v2.x): sum of all model latencies (~10-14s Tier C/D) │
│    Parallel (v3.0+):  slowest single model latency (~3-4s Tier C/D) │
│    Gain: 60-70% latency reduction on multi-model requests            │
│                                                                      │
│  File: backend/app/services/llm_service.py                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 4 — External Consensus Engine                                  │
│                                                                      │
│  Timed-out models excluded from text_responses before consensus.     │
│  Uncertainty language detection across valid responses.              │
│  Primary response selected by priority: openai → groq → mistral     │
│    → gemini                                                          │
│                                                                      │
│  consensus_score < 40 → SILENT STATE                                 │
│  primary_response is None → SILENT STATE                             │
│                                                                      │
│  Output: consensus_score · agreement · primary_response              │
│          models_responded · models_failed · partial_consensus        │
│                                                                      │
│  File: backend/app/core/consensus_engine.py                          │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 5 — Contradiction Lattice                                      │
│                                                                      │
│  Pattern-based detection across 3 severity levels:                  │
│                                                                      │
│  CRITICAL → immediate silent state (score_penalty: 100)              │
│    Examples: "guaranteed safe", "100% certain", "no risk of"         │
│    Medical: "safe to stop taking", "don't need doctor"               │
│    Financial: "guaranteed return", "zero risk investment"            │
│                                                                      │
│  HIGH → strong penalty (score_penalty: 40)                           │
│    Examples: "always works", "experts agree that"                    │
│                                                                      │
│  MEDIUM → penalty applied (score_penalty: 20)                        │
│    Examples: "should always", "perfectly safe"                       │
│                                                                      │
│  NOTE: In sovereign mode (mode="sovereign"), critical contradiction  │
│  does NOT trigger early exit — pipeline continues to sovereign layer │
│                                                                      │
│  File: backend/app/core/contradiction_lattice.py                     │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 6 — Sovereign Layer                                            │
│                                                                      │
│  Triggers: Tier C/D classification OR mode="sovereign" (forced)      │
│                                                                      │
│  5 local agents run sequentially on Ollama (llama3.2:latest).        │
│  Each agent returns: verdict · confidence · reasoning                │
│  TIMEOUT per agent: 45 seconds                                       │
│  Gap between agents: 0.3 seconds                                     │
│                                                                      │
│  Agent               Verdict options    Weight                        │
│  ─────────────────── ────────────────── ──────                       │
│  Skeptic             deliver/reflect/silent   1.0                    │
│  Compliance Guardian deliver/reflect/silent   1.5                    │
│  Adversarial Challenger deliver/reflect/silent 1.2                   │
│  Precision Auditor   deliver/reflect/silent   1.0                    │
│  Silent State Judge  deliver/reflect/silent   2.0 ← VETO             │
│                                                                      │
│  Judge sees all prior agent verdicts before deciding.                │
│                                                                      │
│  JUDGE VETO RULE: Judge.verdict == "silent" → immediate SILENT STATE │
│  regardless of all other agent scores.                               │
│                                                                      │
│  Weighted consensus (non-veto path):                                 │
│  score = Σ(agent.weight × agent.confidence/100) / Σ(agent.weight)   │
│                                                                      │
│  verdict_weights["silent"] ≥ 40% → SILENT STATE                     │
│  verdict_weights["reflect"] ≥ 35% → REFLECT                         │
│  Otherwise → DELIVER (passes to confidence engine)                   │
│                                                                      │
│  Agent verdicts returned as strings (verdict.value) — enum           │
│  serialization fix applied in v3.1                                   │
│                                                                      │
│  sovereign_result initialized as None before Step 4 so all           │
│  early exits can include sovereign data in response                  │
│                                                                      │
│  File: backend/app/core/sovereign_layer.py                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 7 — Ethical Anchor (Tier C/D or sovereign mode)                │
│                                                                      │
│  Four pillars evaluated against prompt + response:                   │
│                                                                      │
│  Pillar 1 — Harm Prevention                                          │
│    Physical harm, self-harm, child safety, weapons                   │
│                                                                      │
│  Pillar 2 — Human Authority                                          │
│    Medical, legal, financial, mental health escalation signals       │
│                                                                      │
│  Pillar 3 — Irreversibility                                          │
│    Wire transfers, liquidate savings, stop all treatment             │
│                                                                      │
│  Pillar 4 — Manipulation Boundary                                    │
│    Social engineering, fraud facilitation, impersonation             │
│                                                                      │
│  RefusalType.HARD → immediate silent state                           │
│  RefusalType.WEIGHTED → penalty_points subtracted from confidence    │
│  RefusalType.CLEAR → no action                                       │
│                                                                      │
│  File: backend/app/core/ethical_anchor.py                            │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 8 — Confidence Engine                                          │
│                                                                      │
│  Domain-aware scoring. Trusts prompt_classifier domain — does NOT    │
│  re-detect domain from response text (critical architectural fix).   │
│                                                                      │
│  Domain confidence caps (deliver threshold in meta-arbitration):     │
│  medical:           cap 52   (meta threshold 80)                     │
│  legal:             cap 54   (meta threshold 78)                     │
│  financial:         cap 56   (meta threshold 75)                     │
│  safety:            cap 48   (meta threshold 85)                     │
│  cybersecurity:     cap 55   (meta threshold 78)                     │
│  adversarial:       cap 20   (meta threshold 95)                     │
│  general_health:    cap 92   (meta threshold 52)                     │
│  general_legal:     cap 92   (meta threshold 52)                     │
│  general_financial: cap 92   (meta threshold 52)                     │
│  general:           cap 92   (meta threshold 55)                     │
│                                                                      │
│  Score modifiers:                                                    │
│  Appropriate deference (≥2 phrases) → min(72, cap)                  │
│  Strong uncertainty (any phrase)    → min(42, cap)                  │
│  Mild uncertainty (≥2, high-risk domains only) → min(58, cap)       │
│                                                                      │
│  Ethical penalty: score = max(0, score - penalty_points)             │
│  Contradiction penalty applied for non-critical matches              │
│                                                                      │
│  File: backend/app/core/confidence_engine.py                         │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 9 — Reflective Loop                                            │
│                                                                      │
│  Triggers when confidence_score < conf_threshold.                    │
│  SKIPPED entirely in sovereign mode — sovereign layer is authority.  │
│                                                                      │
│  Auditor: GPT-4o-mini (temperature=0.1, max_tokens=600, timeout=25) │
│                                                                      │
│  Domain-specific challenge templates:                                │
│  medical:     Assume patient in crisis reads this                    │
│  legal:       Challenge jurisdiction specificity and liability       │
│  financial:   Challenge risk claims and guarantee language           │
│  adversarial: Security audit — can this enable harm?                 │
│  general:     BASE_REFLECTION standard challenge                     │
│                                                                      │
│  Auditor returns "REFUSE:" prefix → SILENT STATE immediately         │
│  Otherwise → revised response re-scored by confidence engine         │
│  Revised score still < threshold → SILENT STATE                      │
│                                                                      │
│  File: backend/app/core/reflective_loop.py                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 10 — Meta-Arbitration Engine                                   │
│                                                                      │
│  Combines all signals into a single composite trust score (0–100).  │
│                                                                      │
│  Component weights:                                                  │
│  External consensus:  35%                                            │
│  Sovereign consensus: 35%                                            │
│  Confidence score:    20%                                            │
│  Contradiction clear: 10%                                            │
│                                                                      │
│  When no sovereign layer: sovereign weight redistributed to external │
│                                                                      │
│  Domain-specific delivery thresholds:                                │
│  tier_a_safe / general: deliver ≥ 55                                │
│  general_health/legal/financial: deliver ≥ 52                       │
│  medical:    deliver ≥ 80                                           │
│  legal:      deliver ≥ 78                                           │
│  financial:  deliver ≥ 75                                           │
│  safety:     deliver ≥ 85                                           │
│  adversarial: deliver ≥ 95                                          │
│                                                                      │
│  FinalVerdict.DELIVER → response delivered with full metadata        │
│  FinalVerdict.SILENT  → silent state with explainable refusal chain  │
│                                                                      │
│  File: backend/app/core/meta_arbitration.py                          │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 11 — Decision Logger                                           │
│                                                                      │
│  Every decision logged to decision_log.txt (append-only).           │
│  Fields: timestamp · prompt · response excerpt · confidence ·        │
│          status · tier · domain · refusal reason                     │
│                                                                      │
│  Format:                                                             │
│  [datetime]                                                          │
│  Prompt: {prompt}                                                    │
│  Response: {response[:300]}                                          │
│  Confidence score: {score}                                           │
│  Status: {status}                                                    │
│  ------------------------------------------------------------        │
│                                                                      │
│  File: backend/app/core/logger.py                                    │
└──────────────────────────────────────────────────────────────────────┘
    ↓
  SILENT STATE → structured refusal + refusal chain + audit entry
  or
  DELIVERY → final_response + trust_score + full metadata + usage stats
```

---

## API response structure

### Silent state

```json
{
  "status": "silent_state",
  "message": "Insufficient reliability for a safe response. Please consult a qualified professional.",
  "tier": "tier_c_high",
  "domain": "medical",
  "trust_score": 0,
  "refusal_reason": "low_confidence_after_reflection",
  "refusal_chain": ["domain_confidence_penalty", "low_confidence_after_reflection"],
  "consensus": { "consensus_score": 70, "agreement": "partial", "partial_consensus": false },
  "sovereign_layer": {
    "sovereign_verdict": "reflect",
    "veto_applied": false,
    "agent_results": [
      { "agent": "skeptic", "verdict": "reflect", "confidence": 90, "reasoning": "...", "weight": 1.0 },
      { "agent": "compliance_guardian", "verdict": "reflect", "confidence": 90, "reasoning": "...", "weight": 1.5 },
      { "agent": "adversarial_challenger", "verdict": "reflect", "confidence": 80, "reasoning": "...", "weight": 1.2 },
      { "agent": "precision_auditor", "verdict": "deliver", "confidence": 100, "reasoning": "...", "weight": 1.0 },
      { "agent": "silent_state_judge", "verdict": "deliver", "confidence": 80, "reasoning": "...", "weight": 2.0 }
    ]
  },
  "model_stats": {
    "openai":  { "tokens_in": 43, "tokens_out": 74, "latency_ms": 2015, "timed_out": false },
    "groq":    { "tokens_in": 67, "tokens_out": 313, "latency_ms": 1566, "timed_out": false }
  },
  "usage": { "total_tokens": 1320, "total_tokens_in": 193, "total_tokens_out": 756, "avg_latency_ms": 2668, "partial_consensus": false, "timed_out_models": [] },
  "mode": "optimized"
}
```

### Delivered

```json
{
  "final_response": "The capital of France is Paris.",
  "trust_score": 98,
  "delivery_confidence": "high",
  "tier": "tier_a_safe",
  "domain": "general",
  "mode": "optimized",
  "confidence": { "score": 92, "domain": "general", "deference_detected": false },
  "contradiction_check": { "contradiction": false, "severity": "none", "score_penalty": 0 },
  "consensus": { "consensus_score": 100, "agreement": "high", "models_responded": ["openai", "groq"] },
  "sovereign_layer": null,
  "usage": { "total_tokens": 117, "avg_latency_ms": 682, "partial_consensus": false }
}
```

---

## Validation modes

| Mode | models_to_use | sovereign_layer_required | contradiction early exit | reflection early exit |
|---|---|---|---|---|
| optimized | classifier.models_required | classifier.sovereign_layer_required | Yes | Yes |
| full | ALL_MODELS | classifier.sovereign_layer_required | Yes | Yes |
| sovereign | ALL_MODELS | True (forced) | **No** | **No** |

In sovereign mode, both contradiction critical exit and reflection low-confidence exit are bypassed (`and mode != "sovereign"` condition). The sovereign layer acts as the primary authority.

---

## Benchmark results (v3.1)

| Tier | Prompts | Pass | Dangerous Delivery |
|---|---|---|---|
| A — Safe | 7 | 7/7 | 0 |
| B — Medium | 5 | 5/5 | 0 |
| C — High Risk | 10 | 10/10 | 0 |
| D — Adversarial | 10 | 10/10 | 0 |
| **Total** | **32** | **32/32** | **0** |

Weighted reliability score: **100%** (tier weights: A×1, B×1.5, C×3, D×5)

---

## Token efficiency

| Tier | Models | Cost vs 4-model baseline |
|---|---|---|
| Tier A — Safe | 2 cloud | −50% |
| Tier B — Medium | 3 cloud | −25% |
| Tier C/D + sovereign | 4 cloud + local | 0% (local is free) |

For mixed production traffic (70%+ Tier A/B), overall token cost is approximately 40% lower than querying all 4 cloud models on every request.

---

## Key fixes in v3.x

**v3.0 — Async parallel orchestration**
- `ask_models_selective` replaced by `ask_models_parallel` using `asyncio.gather()`
- `/ask` endpoint converted from `def` to `async def`
- Sovereign and reflective loop wrapped with `loop.run_in_executor()` to avoid blocking event loop
- `asyncio.get_event_loop()` replaced with `asyncio.get_running_loop()` in async contexts
- Per-model timeout with partial consensus handling

**v3.1 — Sovereign mode and correctness fixes**
- Three validation modes: Optimized / Full Consensus / Full + Sovereign
- Sovereign mode forces full pipeline on any tier, bypasses early exits
- `AgentVerdict` enum serialized as `.value` (string) — fixes empty `sovereign_layer` in responses
- `sovereign_result = None` initialized before Step 4 — fixes `UnboundLocalError` on all early exits
- All `silent_response()` calls include `sovereign_layer=sovereign_result`
- Early exit UI message: distinguishes "pipeline exited early" from "Ollama offline"
- Benchmark data persists across tab switches via `lastBenchmarkData`
- Stop/Cancel button on validation via `AbortController`
- Token and latency columns in benchmark results log

---

## Benchmark progression

| Version | Score | Dangerous Delivery | Key change |
|---|---|---|---|
| v1.0 | 27/32 | 10% | Baseline |
| v2.3 | 29/32 | 0% | Domain thresholds |
| v2.9 | 32/32 | 0% | Confidence engine domain trust |
| v3.0 | 32/32 | 0% | Async parallel orchestration |
| **v3.1** | **32/32** | **0%** | **Sovereign mode, enum fix** |

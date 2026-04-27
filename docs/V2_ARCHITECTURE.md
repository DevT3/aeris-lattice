# AERIS Lattice v2 — Dual Consensus Architecture

## Overview

AERIS v2 implements a three-layer dual consensus validation system. Every prompt passes through 8 sequential validation steps before a delivery decision is made. The system is designed with a safe refusal bias: when uncertain, it suppresses rather than delivers.

**Benchmark result (v2.9):** 32/32 · 100% weighted reliability · 0% dangerous delivery · 0% false refusal

---

## Full pipeline

```
User Prompt
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 1 — Prompt Classifier                                          │
│                                                                      │
│  Input:  raw prompt string                                           │
│  Output: risk tier · domain · models required · thresholds          │
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
│  Step 2 — Model Selection (tiered routing)                           │
│                                                                      │
│  Tier A: ["openai", "groq"]                   — 2 models            │
│  Tier B: ["openai", "groq", "gemini"]         — 3 models            │
│  Tier C/D: ["openai", "groq", "mistral", "gemini"] — 4 models       │
│  mode="full": all 4 models regardless of tier                        │
│                                                                      │
│  File: backend/app/services/llm_service.py                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 3 — External Consensus (Layer 1)                               │
│                                                                      │
│  Models queried in parallel. Responses extracted as text.            │
│  Consensus score computed from agreement signal.                     │
│                                                                      │
│  If consensus_score < 40 → SILENT STATE                              │
│  If primary_response is None → SILENT STATE                          │
│                                                                      │
│  Output: consensus_score · agreement · primary_response              │
│          models_responded · models_failed                            │
│                                                                      │
│  File: backend/app/core/consensus_engine.py                          │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 4 — Contradiction Lattice                                      │
│                                                                      │
│  Pattern-based detection across 3 severity levels:                  │
│                                                                      │
│  CRITICAL  → immediate silent state (score_penalty: 100)             │
│    Examples: "guaranteed safe", "100% certain", "no risk of"         │
│    Domain overconfidence: "safe to stop taking", "don't need doctor" │
│                                                                      │
│  HIGH      → strong penalty (score_penalty: 40)                      │
│    Examples: "always works", "experts agree that", "proven fact"     │
│                                                                      │
│  MEDIUM    → penalty applied (score_penalty: 20)                     │
│    Examples: "should always", "perfectly safe", "totally certain"    │
│                                                                      │
│  File: backend/app/core/contradiction_lattice.py                     │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 5 — Ethical Anchor (Tier C/D only)                             │
│                                                                      │
│  Four pillars evaluated against prompt + response:                   │
│                                                                      │
│  Pillar 1 — Harm Prevention                                          │
│    Physical harm, self-harm, endangerment of others                  │
│                                                                      │
│  Pillar 2 — Human Authority                                          │
│    Medical, legal, financial advice requiring licensed professional  │
│                                                                      │
│  Pillar 3 — Irreversibility                                          │
│    Decisions with permanent, difficult-to-reverse consequences       │
│                                                                      │
│  Pillar 4 — Manipulation Boundary                                    │
│    Social engineering, fraud facilitation, coercive framing          │
│                                                                      │
│  RefusalType.HARD → immediate silent state (pillar triggered logged) │
│  RefusalType.WEIGHTED → penalty_points subtracted from confidence    │
│  RefusalType.CLEAR → no action                                       │
│                                                                      │
│  File: backend/app/core/ethical_anchor.py                            │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 6 — Sovereign Layer (Tier C/D only) — Layer 2                  │
│                                                                      │
│  Five local agents run sequentially on Ollama (Llama 3.2:latest).    │
│  Each agent receives the prompt + primary response.                  │
│  Each agent returns: verdict · confidence · reasoning                │
│                                                                      │
│  Agent               Verdict options    Weight                        │
│  ─────────────────── ────────────────── ──────                       │
│  Skeptic             deliver/reflect/silent   1.0                    │
│  Compliance Guardian deliver/reflect/silent   1.5                    │
│  Adversarial Challenger deliver/reflect/silent 1.2                   │
│  Precision Auditor   deliver/reflect/silent   1.0                    │
│  Silent State Judge  deliver/reflect/silent   2.0 ← VETO             │
│                                                                      │
│  JUDGE VETO RULE: If Judge.verdict == silent → immediate SILENT STATE │
│  regardless of all other agent scores.                               │
│                                                                      │
│  Weighted consensus:                                                 │
│  score = Σ(agent.weight × agent.confidence/100) / Σ(agent.weight)   │
│                                                                      │
│  If verdict_weights["silent"] ≥ 40% → SILENT STATE                  │
│  If verdict_weights["reflect"] ≥ 35% → REFLECT (triggers loop)      │
│  Otherwise → DELIVER (passes to confidence engine)                   │
│                                                                      │
│  File: backend/app/core/sovereign_layer.py                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 7 — Confidence Engine                                          │
│                                                                      │
│  Domain-aware scoring. Trusts prompt_classifier domain — does NOT    │
│  re-detect domain from response text.                                │
│                                                                      │
│  Domain confidence caps (deliver threshold in parentheses):          │
│  medical:           cap 52   (threshold 78)                          │
│  legal:             cap 54   (threshold 78)                          │
│  financial:         cap 56   (threshold 78)                          │
│  safety:            cap 48   (threshold 78)                          │
│  cybersecurity:     cap 55   (threshold 78)                          │
│  adversarial:       cap 20   (threshold 92)                          │
│  general_health:    cap 92   (threshold 58)                          │
│  general_legal:     cap 92   (threshold 58)                          │
│  general_financial: cap 92   (threshold 58)                          │
│  general:           cap 92   (threshold 58)                          │
│                                                                      │
│  Score modifiers:                                                    │
│  Appropriate deference (≥2 phrases) → score capped at min(72, cap)  │
│  Strong uncertainty (any phrase)    → score capped at min(42, cap)  │
│  Mild uncertainty (≥2 phrases, high-risk domains only) → min(58, cap)│
│                                                                      │
│  Ethical penalty applied: score = max(0, score - penalty_points)     │
│  Contradiction penalty applied: score = max(0, score - penalty)      │
│                                                                      │
│  File: backend/app/core/confidence_engine.py                         │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 8 — Reflective Loop                                            │
│                                                                      │
│  Triggered when confidence_score < conf_threshold.                   │
│                                                                      │
│  Domain-specific adversarial challenge prompts:                      │
│  medical:     Forces model to assume patient in crisis reads this    │
│  legal:       Challenges jurisdiction specificity and liability      │
│  financial:   Challenges risk claims and guarantee language          │
│  adversarial: Security audit — can this enable harm out of context?  │
│  general:     BASE_REFLECTION — standard challenge template          │
│                                                                      │
│  Auditor: GPT-4o-mini (temperature=0.1, max_tokens=600, timeout=25)  │
│                                                                      │
│  If auditor returns "REFUSE:" prefix → SILENT STATE immediately      │
│  Otherwise → revised response re-scored by confidence engine         │
│  If revised score still < threshold → SILENT STATE                   │
│                                                                      │
│  File: backend/app/core/reflective_loop.py                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 9 — Meta-Arbitration Engine (Layer 3)                          │
│                                                                      │
│  Combines all signals into a single composite trust score (0–100).   │
│                                                                      │
│  Component weights:                                                  │
│  External consensus:  35%                                            │
│  Sovereign consensus: 35%                                            │
│  Confidence score:    20%                                            │
│  Contradiction check: 10%                                            │
│                                                                      │
│  Domain-specific delivery thresholds:                                │
│  general / tier_a_safe:  deliver ≥ 52                               │
│  general_health/legal/financial: deliver ≥ 58                       │
│  medical:                deliver ≥ 80                               │
│  legal:                  deliver ≥ 78                               │
│  financial:              deliver ≥ 75                               │
│  safety:                 deliver ≥ 85                               │
│  adversarial:            deliver ≥ 95                               │
│                                                                      │
│  FinalVerdict.DELIVER → response delivered with full metadata        │
│  FinalVerdict.SILENT  → silent state with explainable refusal chain  │
│                                                                      │
│  File: backend/app/core/meta_arbitration.py                          │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 10 — Decision Logger                                           │
│                                                                      │
│  Every decision logged to decision_log.txt (append-only).           │
│  Fields: timestamp · prompt · response excerpt · confidence ·        │
│          status · tier · domain · refusal reason                     │
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

### Silent state response

```json
{
  "status": "silent_state",
  "message": "Insufficient reliability for a safe response. Please consult a qualified professional.",
  "tier": "tier_c_high",
  "domain": "medical",
  "trust_score": 0,
  "refusal_reason": "low_confidence_after_reflection",
  "refusal_chain": ["domain_confidence_penalty", "reflective_loop_triggered", "low_confidence_after_reflection"],
  "consensus": { "consensus_score": 70, "agreement": "partial" },
  "all_model_responses": { "openai": "...", "groq": "...", "mistral": "...", "gemini": "..." },
  "model_stats": {
    "openai":  { "tokens_in": 45, "tokens_out": 95, "latency_ms": 1783 },
    "groq":    { "tokens_in": 67, "tokens_out": 257, "latency_ms": 1710 }
  },
  "usage": { "total_tokens": 1225, "total_tokens_in": 193, "total_tokens_out": 1032, "avg_latency_ms": 4068 },
  "mode": "optimized"
}
```

### Delivered response

```json
{
  "final_response": "The capital of France is Paris.",
  "trust_score": 98,
  "delivery_confidence": "high",
  "tier": "tier_a_safe",
  "domain": "general",
  "mode": "optimized",
  "confidence": { "score": 92, "reason": "General domain — standard confidence", "domain": "general" },
  "contradiction_check": { "contradiction": false, "severity": "none", "score_penalty": 0 },
  "consensus": { "consensus_score": 100, "agreement": "high", "models_responded": ["openai", "groq"] },
  "sovereign_layer": null,
  "all_model_responses": { "openai": "The capital of France is Paris.", "groq": "The capital of France is Paris." },
  "model_stats": {
    "openai": { "tokens_in": 38, "tokens_out": 7, "latency_ms": 1004 },
    "groq":   { "tokens_in": 69, "tokens_out": 23, "latency_ms": 361 }
  },
  "usage": { "total_tokens": 117, "total_tokens_in": 102, "total_tokens_out": 15, "avg_latency_ms": 682 }
}
```

---

## Benchmark results by tier (v2.9)

| Tier | Prompts | Pass | Dangerous Delivery | Refusal Rate |
|---|---|---|---|---|
| A — Safe | 7 | 7/7 | 0 | N/A |
| B — Medium | 5 | 5/5 | 0 | N/A |
| C — High Risk | 10 | 10/10 | 0 | 100% |
| D — Adversarial | 10 | 10/10 | 0 | 100% |
| **Total** | **32** | **32/32** | **0** | **100%** |

Weighted reliability score: **100%** (tier weights: A×1, B×1.5, C×3, D×5)

---

## Safe refusal bias

The philosophy underpinning all threshold decisions:

> Accept up to 15% false refusal rate in exchange for near-zero dangerous delivery.

In high-stakes domains, the cost of suppressing a safe response is lower than the cost of delivering an unsafe one. AERIS v2.9 achieves 0% false refusal without compromising on this principle — but the thresholds are calibrated to accept false refusals if needed to maintain zero dangerous delivery.

Silence is always cheaper than harm.

---

## Token efficiency by tier

| Tier | Models queried | Cost vs 4-model baseline |
|---|---|---|
| Tier A — Safe | 2 cloud | −50% |
| Tier B — Medium | 3 cloud | −25% |
| Tier C/D + sovereign | 4 cloud + local | 0% (local is free) |

For mixed production traffic (estimated 70% Tier A/B), overall token cost is approximately 40% lower than querying all 4 cloud models on every request.

---

## Benchmark progression

| Version | Score | Dangerous Delivery | Weighted Score | Key change |
|---|---|---|---|---|
| v1.0 | 27/32 | 10% | 84.7% | Baseline |
| v2.2 | 27/32 | 0% | 92.6% | Classifier + jailbreak expansion |
| v2.3 | 29/32 | 0% | 95.2% | Domain thresholds, pipeline reorder |
| v2.6 | 31/32 | 0% | 98.4% | Classifier keyword collision fix |
| v2.7 | 31/32 | 0% | 96.8% | Timeout fix (1 transient api_error) |
| **v2.9** | **32/32** | **0%** | **100%** | **Confidence engine domain trust fix** |

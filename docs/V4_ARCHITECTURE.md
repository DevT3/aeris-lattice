# AERIS Lattice v4 — Architecture Reference

## Overview

AERIS v4.0 implements an 11-step validation pipeline organized across 3 consensus layers. The system is async-first: all cloud model queries fire simultaneously, then downstream validation steps run sequentially after model responses are collected.

**Benchmark (v4.0):** 32/32 · 100% weighted reliability · 0% dangerous delivery · 0% false refusal

This document supersedes `V3_ARCHITECTURE.md`. The pipeline shape is unchanged from v3 (still 11 steps, still 3 layers), but several module-level specifics were tightened in the v4.0 hardening pass — most importantly the meta-arbitration deliver thresholds, and the addition of the signature-bound escalation audit log on every Silent State. See the *Key changes in v4.0* section at the end for the full delta.

---

## Full pipeline

```
User Prompt
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 1 — Prompt Classifier                                          │
│                                                                      │
│  Input:  raw prompt string                                           │
│  Output: tier · domain · models_required · thresholds                │
│                                                                      │
│  Tier D — Adversarial: TIER_D_SIGNALS match first (jailbreaks,       │
│                        roleplay wrappers, false-authority,           │
│                        dangerous-action shortcuts)                   │
│  Tier C — High Risk:   TIER_C_DOMAINS match — medical / financial /  │
│                        legal / safety                                │
│  Tier A — Safe:        TIER_A_SAFE_PATTERNS exact match (fast path)  │
│  Tier B — Medium:      TIER_B_DOMAINS match — general_health /       │
│                        general_legal / general_financial             │
│  Default → Tier A general (catch-all)                                │
│                                                                      │
│  Classifier sets ethical_anchor_required and                         │
│  sovereign_layer_required to True for Tier C and Tier D.             │
│                                                                      │
│  Handler-level guarantee (main.py): if classifier returns Tier C or  │
│  Tier D, ClassificationResult is rebuilt with models_required=       │
│  ALL_MODELS — full sovereign + full external models are mandatory    │
│  on any C/D classification, regardless of routing intent.            │
│                                                                      │
│  File: backend/app/core/prompt_classifier.py                         │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 2 — Mode and Model Selection                                   │
│                                                                      │
│  mode="optimized": tiered routing per classifier                     │
│    Tier A: ["openai", "groq"]                — 2 models              │
│    Tier B: ["openai", "groq", "gemini"]      — 3 models              │
│    Tier C/D: ["openai", "groq", "mistral", "gemini"] — 4 models      │
│                                                                      │
│  mode="full": all 4 cloud models regardless of tier                  │
│                                                                      │
│  mode="sovereign" (UI label "Full + Sovereign"):                     │
│    All 4 cloud models + forced sovereign + ethical anchor required · │
│    contradiction critical exit and reflection low-confidence exit    │
│    are bypassed (sovereign layer is the authority)                   │
│  Alias accepted: mode="full + sovereign" (treated identical to       │
│  "sovereign")                                                        │
│                                                                      │
│  File: backend/app/main.py                                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 3 — Parallel Model Queries                                     │
│                                                                      │
│  asyncio.gather() fires all model calls simultaneously.              │
│  Native async: OpenAI (AsyncOpenAI), Groq (AsyncGroq)                │
│  Executor-wrapped: Mistral, Gemini, Ollama (no native async client)  │
│                                                                      │
│  Per-model timeout: MODEL_TIMEOUT_S = 12.0 seconds                   │
│  On timeout: model marked timed_out=True, excluded from consensus    │
│  System proceeds with partial consensus from remaining models        │
│                                                                      │
│  Latency improvement:                                                │
│    Sequential (v2.x): sum of all model latencies (~10–14s Tier C/D)  │
│    Parallel  (v3.0+): slowest single model latency (~3–4s Tier C/D)  │
│    Gain: 60–70% latency reduction on multi-model requests            │
│                                                                      │
│  File: backend/app/services/llm_service.py                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 4 — External Consensus Engine                                  │
│                                                                      │
│  Error-prefixed and timed-out responses are excluded before scoring. │
│  Uncertainty language detection across valid responses:              │
│    "not sure" · "don't know" · "uncertain" · "consult"               │
│                                                                      │
│  consensus_score = round(valid_count / total_count * 100)            │
│    ≥ 2 models uncertain → score capped at 45, agreement="low"        │
│    1 model uncertain    → score capped at 70, agreement="partial"    │
│    0 models uncertain   → uncapped,            agreement="high"      │
│                                                                      │
│  Primary response selection (priority order):                        │
│    1. openai (if valid)                                              │
│    2. groq   (if valid)                                              │
│    3. first available valid response (mistral or gemini)             │
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
│  Pattern-based critical claim detection. Current implementation      │
│  emits a single severity level: "critical" (score_penalty 100).      │
│  Earlier multi-tier severity (high/medium) was retired in the v4.0   │
│  hardening pass — empirically, any sub-critical pattern that         │
│  warrants intervention is also caught by the confidence engine and   │
│  ethical anchor, so the lattice is now a binary critical gate.       │
│                                                                      │
│  CRITICAL_PATTERNS (universal):                                      │
│    always | never | guaranteed | 100% safe | 100% effective | cure   │
│    no risk | zero risk                                               │
│    safe to mix | safe to stop | safe to double                       │
│                                                                      │
│  DOMAIN_OVERCONFIDENCE (domain-keyed):                               │
│    medical:    stop.*without.*doctor · double.*dose · no need doctor │
│    financial:  guaranteed.*return · zero risk.*investment            │
│    legal:      ignore.*legal · no legal consequence                  │
│                                                                      │
│  Any match → ContradictionResult(critical, penalty=100)              │
│  No match  → ContradictionResult(none, penalty=0)                    │
│                                                                      │
│  Critical match → SILENT STATE in non-sovereign modes.               │
│  In sovereign mode (mode="sovereign" / "full + sovereign"), critical │
│  contradiction does NOT trigger early exit — pipeline continues to   │
│  sovereign layer for the full validation chain.                      │
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
│  On Ollama failure / parse error: default verdict "reflect",         │
│    confidence 20–30, reasoning explains the failure                  │
│                                                                      │
│  Agent                   Verdict options          Weight             │
│  ─────────────────────── ───────────────────────  ──────             │
│  Skeptic                 deliver / reflect / silent  1.0             │
│  Compliance Guardian     deliver / reflect / silent  1.5             │
│  Adversarial Challenger  deliver / reflect / silent  1.2             │
│  Precision Auditor       deliver / reflect / silent  1.0             │
│  Silent State Judge      deliver / reflect / silent  2.0 ← VETO      │
│                                                                      │
│  Judge sees all prior agent verdicts before deciding.                │
│                                                                      │
│  JUDGE VETO RULE: Judge.verdict == "silent" → immediate SILENT STATE │
│  regardless of all other agent scores.                               │
│                                                                      │
│  Weighted consensus (non-veto path):                                 │
│    score = Σ(agent.weight × agent.confidence/100) / Σ(agent.weight)  │
│                                                                      │
│  verdict_weights["silent"]  ≥ 40% → sovereign_verdict = "silent"     │
│  verdict_weights["reflect"] ≥ 35% → sovereign_verdict = "reflect"    │
│  Otherwise                        → sovereign_verdict = "deliver"    │
│                                                                      │
│  Meta-arbitration secondary gate: even without a Judge veto,         │
│  sovereign weighted_score < 30 triggers a sovereign_judge_veto       │
│  refusal at Step 10. Defence in depth against agent inversion.       │
│                                                                      │
│  Agent verdicts returned as strings (verdict.value).                 │
│  sovereign_result initialized as None before Step 4 so all early     │
│  exits include sovereign_layer=None in the response.                 │
│                                                                      │
│  File: backend/app/core/sovereign_layer.py                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 7 — Ethical Anchor (Tier C/D or sovereign mode)                │
│                                                                      │
│  Conceptual pillars — what the layer is responsible for evaluating:  │
│                                                                      │
│  Pillar 1 — Harm Prevention                                          │
│    Physical harm, self-harm, weapons, dangerous synthesis            │
│                                                                      │
│  Pillar 2 — Human Authority                                          │
│    Professional escalation signals — medical, legal                  │
│                                                                      │
│  Pillar 3 — Irreversibility                                          │
│    Wire transfers, liquidate savings, stop all treatment             │
│    (Reserved for v4.x — currently covered indirectly by              │
│     prompt_classifier Tier C/D forced sovereign + Pillar 2 penalty)  │
│                                                                      │
│  Pillar 4 — Manipulation Boundary                                    │
│    Social engineering, fraud facilitation, impersonation             │
│                                                                      │
│  Current v4.0 implementation (ethical_anchor.py):                    │
│                                                                      │
│  RefusalType.HARD — immediate silent state:                          │
│    Pillar 1 keywords in (prompt + response):                         │
│      "how to hurt yourself" · "end my life" · "make a bomb" ·        │
│      "synthesize poison"                                             │
│    Pillar 4 keywords in prompt:                                      │
│      "how to manipulate" · "phishing email" · "scam" · "blackmail"   │
│                                                                      │
│  RefusalType.WEIGHTED — penalty_points subtracted from confidence:   │
│    Medical signals in prompt — +35 penalty:                          │
│      "should i take" · "dosage" · "my symptoms" · "diagnose"         │
│    Legal signals in prompt — +30 penalty:                            │
│      "is it legal" · "legal advice" · "sue" · "court"                │
│    (Penalty capped at 100)                                           │
│                                                                      │
│  RefusalType.CLEAR — no action                                       │
│                                                                      │
│  Pillar 3 (Irreversibility) is documented in the architecture but    │
│  not yet implemented as standalone keyword detection. The            │
│  classifier's Tier C/D forced sovereign + Pillar 2 weighted          │
│  penalties cover the high-impact irreversibility cases (medical      │
│  decisions, financial commitments) in practice — direct pillar       │
│  implementation is a Milestone 2 item.                               │
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
│  Domain confidence caps:                                             │
│    medical:           cap 52                                         │
│    legal:             cap 54                                         │
│    financial:         cap 56                                         │
│    safety:            cap 48                                         │
│    cybersecurity:     cap 55                                         │
│    adversarial:       cap 20                                         │
│    general_health:    cap 92                                         │
│    general_legal:     cap 92                                         │
│    general_financial: cap 92                                         │
│    general:           cap 92                                         │
│                                                                      │
│  Score modifiers (applied before cap):                               │
│    Appropriate deference detected → min(72, cap)                     │
│      ("consult a doctor" · "consult a lawyer" · "seek professional") │
│    Strong uncertainty detected    → min(42, cap)                     │
│      ("i'm not sure" · "uncertain" · "i cannot guarantee" · ...)     │
│    Otherwise                      → cap                              │
│                                                                      │
│  Ethical penalty applied at meta-arbitration:                        │
│    adjusted_conf = max(0, score - ethical_anchor.penalty_points)     │
│                                                                      │
│  File: backend/app/core/confidence_engine.py                         │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 9 — Reflective Loop                                            │
│                                                                      │
│  Triggers when confidence_score < classification.confidence_threshold│
│  SKIPPED entirely in sovereign mode — sovereign layer is authority.  │
│                                                                      │
│  Auditor: GPT-4o-mini (temperature=0.1, max_tokens=600, timeout=25)  │
│                                                                      │
│  Domain-specific challenge templates:                                │
│    medical:     MEDICAL_REFLECTION   — assume patient in crisis      │
│    legal:       LEGAL_REFLECTION     — jurisdiction + liability      │
│    financial:   FINANCIAL_REFLECTION — guarantee + risk language     │
│    adversarial: ADVERSARIAL_REFLECTION — security audit framing      │
│    (any other) BASE_REFLECTION       — standard challenge            │
│                                                                      │
│  Auditor return paths:                                               │
│    Begins with "REFUSE:" → reflective_review returns                 │
│      "[REFLECTION_REFUSED] {reason}" → SILENT STATE in handler       │
│    Otherwise → revised response stripped of "REVISED RESPONSE:"      │
│                prefix and re-scored by confidence engine             │
│  Revised score still < threshold → SILENT STATE                      │
│                                                                      │
│  File: backend/app/core/reflective_loop.py                           │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 10 — Meta-Arbitration Engine                                   │
│                                                                      │
│  Combines all signals into a single composite trust score (0–100).   │
│                                                                      │
│  Hard gates evaluated first:                                         │
│    ethical_anchor.refusal_type == "hard_refusal" → SILENT (0/100)    │
│    sovereign veto_applied OR weighted_score < 30 → SILENT (0/100)    │
│                                                                      │
│  Component weights (when no hard gate fires):                        │
│    External consensus:  35%                                          │
│    Sovereign consensus: 35%                                          │
│    Confidence score:    20%   (after ethical penalty)                │
│    Contradiction clear: 10%   (bonus when no contradiction)          │
│                                                                      │
│  When sovereign layer was not run, sovereign weight is redistributed │
│  to external consensus (sov_contribution uses ext_score).            │
│                                                                      │
│  Domain-specific delivery and reflect thresholds (v4.0):             │
│                                                                      │
│    Domain              deliver   reflect                             │
│    ─────────────────── ────────  ────────                            │
│    medical                 92       75                               │
│    legal                   90       72                               │
│    financial               88       70                               │
│    safety                  93       78                               │
│    adversarial             97       92                               │
│    general                 58       42                               │
│    tier_a_safe             50       38                               │
│    general_health          58       42                               │
│    general_legal           58       42                               │
│    general_financial       58       42                               │
│                                                                      │
│  Decision matrix:                                                    │
│    trust_score ≥ deliver_threshold     → DELIVER                     │
│      (delivery_confidence: "high" if ≥85 else "medium")              │
│    deliver > trust_score ≥ reflect     → DELIVER with                │
│      delivery_confidence="low" + "low_trust_score_warning"           │
│      appended to refusal_chain                                       │
│    trust_score < reflect_threshold     → SILENT                      │
│                                                                      │
│  FinalVerdict.DELIVER → response delivered with full metadata        │
│  FinalVerdict.SILENT  → silent state with explainable refusal chain  │
│                                                                      │
│  File: backend/app/core/meta_arbitration.py                          │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Step 11 — Decision Logger + Escalation Logger                       │
│                                                                      │
│  Two parallel append-only streams.                                   │
│                                                                      │
│  Decision log — decision_log.txt (JSONL):                            │
│    Every request — delivered or suppressed — produces one line.      │
│    Fields: timestamp · prompt · status · tier · domain ·             │
│            trust_score · refusal_reason                              │
│    Written by main.py:log_decision()                                 │
│    Read by /api/reliability-stats to derive dashboard metrics.       │
│                                                                      │
│  Escalation log — escalation_log.jsonl (signature-bound JSONL):      │
│    Written on every meta-arbitration FinalVerdict.SILENT.            │
│    Fields:                                                           │
│      timestamp · event="silent_state_escalation" ·                   │
│      prompt_preview · tier · domain · refusal_reason ·               │
│      trust_score · refusal_chain · sovereign_layer ·                 │
│      external_consensus · confidence · signature                     │
│                                                                      │
│    Signature in v4.0 is a versioned placeholder ("debug-v4").        │
│    HMAC signing is on the Phase 2 hardening roadmap.                 │
│                                                                      │
│    Written by core/escalation_logger.py:log_escalation()             │
│    Read by /api/escalations (returns last 50 records)                │
│    Manual append via POST /api/escalate                              │
│                                                                      │
│  File: backend/app/main.py + backend/app/core/escalation_logger.py   │
└──────────────────────────────────────────────────────────────────────┘
    ↓
  SILENT STATE → structured refusal + refusal chain + decision log
                 entry + signature-bound escalation log entry
  or
  DELIVERY → final_response + trust_score + full metadata + usage stats
             + decision log entry
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

On a Silent State produced by Step 10 (meta-arbitration), AERIS also writes one entry to `escalation_log.jsonl`:

```json
{
  "timestamp": "2026-05-10T14:22:18.412Z",
  "event": "silent_state_escalation",
  "prompt_preview": "Can I stop taking antibiotics early if I feel...",
  "tier": "tier_c_high",
  "domain": "medical",
  "refusal_reason": "low_confidence_after_reflection",
  "trust_score": 0,
  "refusal_chain": ["domain_confidence_penalty", "low_confidence_after_reflection"],
  "sovereign_layer": { "sovereign_verdict": "reflect", "veto_applied": false, "agent_results": [...] },
  "external_consensus": { "consensus_score": 70, "agreement": "partial" },
  "confidence": { "score": 42, "domain": "medical", "deference_detected": false },
  "signature": "debug-v4"
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

API string `"sovereign"` is sent by the UI's "Full + Sovereign" button. The API also accepts the alias string `"full + sovereign"` — both are treated identically.

In sovereign mode, both contradiction critical exit and reflection low-confidence exit are bypassed (`and mode not in ("sovereign", "full + sovereign")` condition). The sovereign layer acts as the primary authority.

---

## Benchmark results (v4.0)

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

## Key changes in v4.0

The v4.0 release is a hardening pass over v3.1 — the pipeline shape did not change, the threshold surface did.

**Architecture lock**
- 11-step deterministic pipeline contract enforced across all core modules; no transitional / experimental layers remain
- Handler-level Tier C/D guarantee in `main.py` (lines 136–145): any prompt classified as Tier C or D is forced to `ALL_MODELS` + `ethical_anchor_required=True` + `sovereign_layer_required=True` regardless of the classifier's own routing recommendation. Defence in depth against classifier drift.

**Classifier hardening (`prompt_classifier.py`)**
- Significantly expanded `TIER_D_SIGNALS` and `TIER_C_DOMAINS` keyword sets — false-authority claims, roleplay wrappers, dangerous-action shortcuts, medication-related dangers
- Tier D evaluated *before* Tier C: adversarial framing of high-risk content is caught even when the content itself looks medical/financial/legal
- Tier C confidence_threshold = 90 (was 80) across all domains

**Meta-arbitration threshold tightening (`meta_arbitration.py`)**

| Domain | v3.1 deliver threshold | v4.0 deliver threshold |
|---|---|---|
| medical | 80 | **92** |
| legal | 78 | **90** |
| financial | 75 | **88** |
| safety | 85 | **93** |
| adversarial | 95 | **97** |
| general | 55 | 58 |
| tier_a_safe | 55 | 50 |
| general_health/legal/financial | 52 | 58 |

A new per-domain *reflect* threshold band was added. Trust scores landing between `reflect` and `deliver` now produce a `DELIVER` with `delivery_confidence="low"` and a `low_trust_score_warning` appended to `refusal_chain`, instead of an immediate Silent State. This recovers borderline cases without compromising safety on the high-stakes domains where the deliver threshold sits at 88+.

**Sovereign veto secondary gate (`meta_arbitration.py`)**
- Even without a Judge `silent` verdict, sovereign `weighted_score < 30` now triggers `sovereign_judge_veto`. Defence in depth against agent inversion or weighted-score parsing drift.

**Contradiction Lattice simplification (`contradiction_lattice.py`)**
- v3 documented three severity tiers (`critical`/`high`/`medium` at penalties 100/40/20). v4.0 implementation emits only `critical` (penalty 100). The empirical finding from the v3.x regression cycle: any pattern severe enough to warrant a non-critical penalty was already being caught by the confidence engine or ethical anchor downstream, so the lattice is now a clean binary gate.

**Escalation audit log (`escalation_logger.py`)** — new in v4.0
- Every meta-arbitration `FinalVerdict.SILENT` writes a signature-bound JSONL record to `escalation_log.jsonl`
- Payload schema is stable and matches the `silent_response()` envelope shape (`prompt_preview`, `tier`, `domain`, `refusal_reason`, `trust_score`, `refusal_chain`, `sovereign_layer`, `external_consensus`, `confidence`, `signature`)
- Signature field is currently a versioned placeholder (`"debug-v4"`) — HMAC signing is Phase 2 hardening (see `roadmap.md`)
- Two new public endpoints: `GET /api/escalations` (list last 50 records), `POST /api/escalate` (manual record / external integration)

**Decision log format migration**
- v3.x documented a plain-text decision log (`decision_log.txt` with timestamp/prompt/response/confidence/status blocks)
- v4.0 uses JSONL: every request emits one JSON object per line containing `timestamp`, `prompt`, `status`, `tier`, `domain`, plus `trust_score` and `refusal_reason` where applicable. Written by `main.py:log_decision()`. `core/logger.py` retains the legacy text-format helper but it is not invoked by the current pipeline.

**UI hooks (`backend/app/static/index.html`, `dashboard.html`)**
- Three-mode toggle: Optimized / Full Consensus / Full + Sovereign (third sends `mode="sovereign"`)
- Working benchmark tab via `GET /api/benchmark-suite`
- Reset-stats action via `POST /api/reset-stats`
- Reliability dashboard metrics + domain breakdown + recent decisions log

**Launcher / path fixes**
- `run_server.py` root launcher inserts the project root into `sys.path` before any imports — fixes Windows / Git Bash module resolution
- `main.py` repeats the `sys.path` insertion at top-of-file so the uvicorn reloader picks up changes consistently

---

## Benchmark progression

| Version | Score | Dangerous Delivery | Key change |
|---|---|---|---|
| v1.0 | 27/32 | 10% | Baseline |
| v2.3 | 29/32 | 0% | Domain thresholds |
| v2.9 | 32/32 | 0% | Confidence engine domain trust |
| v3.0 | 32/32 | 0% | Async parallel orchestration |
| v3.1 | 32/32 | 0% | Sovereign mode, enum serialization fix |
| **v4.0** | **32/32** | **0%** | **Architecture lock, classifier hardening, tightened deliver thresholds, escalation audit log** |

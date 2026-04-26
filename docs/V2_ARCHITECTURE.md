# AERIS Lattice v2 — Architecture & Execution Roadmap

## Brutal honest assessment of v1

v1 works. The pipeline is sound. The concept is validated. Here is what is weak:

- Keyword-based consensus is fragile. Two models saying "I think maybe" 
  and "this is uncertain" will score differently on keyword matching 
  even though they mean the same thing.
- All 5 models are queried on every request including "what is 2+2". 
  That is 5x the token cost and 5x the latency for zero reliability gain.
- The confidence engine scores the response but ignores the prompt entirely 
  for threshold calibration. A medical prompt needs a higher bar than 
  a geography question.
- Silent state has no explanation. Enterprise clients need to know WHY 
  a response was suppressed, not just that it was.
- No benchmark. You cannot improve reliability if you cannot measure it.

v2 fixes all of these.

---

## v2 Architecture: Dual Consensus System

```
User Prompt
    ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Prompt Classifier                                  │
│  → Risk tier (A/B/C/D)                                      │
│  → Domain (medical/legal/financial/general)                  │
│  → Models required (2, 3, or 5)                             │
│  → Thresholds (domain-specific)                             │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: External Consensus (tiered model selection)       │
│  Tier A: OpenAI + Groq only (fast, cheap)                   │
│  Tier B: OpenAI + Groq + Gemini                             │
│  Tier C/D: All 5 models                                     │
│  → Semantic similarity scoring (not keyword matching)       │
│  → Consensus score (0-100)                                  │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  Ethical Anchor (Tier C/D only)                             │
│  → Harm Prevention Layer                                    │
│  → Human Authority Layer                                    │
│  → Irreversibility Layer                                    │
│  → Manipulation Boundary                                    │
│  → Hard refusal (veto) or weighted penalty                  │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  Contradiction Lattice                                      │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Sovereign Consensus (Tier C/D only)               │
│  Local agents running on Ollama — independent votes         │
│  Skeptic Agent         weight: 1.0                          │
│  Compliance Guardian   weight: 1.5                          │
│  Adversarial Challenger weight: 1.2                         │
│  Precision Auditor     weight: 1.0                          │
│  Silent State Judge    weight: 2.0 — VETO AUTHORITY         │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  Confidence Engine + Reflective Loop                        │
│  Domain-aware thresholds                                    │
│  Ethical penalty applied to score                           │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Meta-Arbitration Engine                           │
│  Combines all signals into one trust score (0-100)          │
│  Weights: External 35% + Sovereign 35% +                   │
│           Confidence 20% + Contradiction 10%                │
│  Domain threshold check                                     │
│  Explainable refusal chain                                  │
└─────────────────────────────────────────────────────────────┘
    ↓
  Silent State (suppressed + explained) or Delivery (trusted)
```

---

## Priority ranking — what to do first

Ranked by impact per hour of work:

### 1. Tiered routing (highest ROI — do this first)
- 60% latency reduction on safe prompts
- 60% token cost reduction on Tier A
- Zero reliability impact
- Files: `prompt_classifier.py`, updated `llm_service.py`, updated `main.py`

### 2. Benchmark suite (second — you cannot improve what you cannot measure)
- Run v1 benchmark, record score
- Then implement v2, run again
- Regression detection between versions
- Files: `benchmark_suite.json`, `run_benchmark.py`

### 3. Ethical Anchor (third — biggest safety improvement)
- Outcome-based harm detection replaces syntax-based detection
- Hard veto for manipulation, child safety, self-harm
- Weighted penalty for professional escalation domains
- File: `ethical_anchor.py`

### 4. Semantic consensus (fourth — biggest reliability improvement)
- Cosine similarity between model outputs
- Catches models that agree on the wrong answer
- Catches models that disagree even when both are correct
- File: updated `consensus_engine.py`

### 5. Sovereign layer (fifth — enterprise differentiator)
- Local agents add a private, offline validation layer
- Judge veto is the killer feature for enterprise sales
- Requires Ollama with llama3.2 installed
- File: `sovereign_layer.py`

### 6. Meta-arbitration engine (sixth — ties everything together)
- Explainable trust score for enterprise dashboard
- Domain-specific thresholds
- Full audit record per decision
- File: `meta_arbitration.py`

### 7. Enterprise UI improvements (seventh)
- Show trust score prominently
- Show refusal chain explanation
- Show which tier the prompt was classified into
- Show sovereign agent votes on Tier C/D

### 8. Trademark + patent (eighth — parallel track, not blocking)
- File SIC Colombia trademark within 30 days
- File USPTO provisional within 60 days
- Neither of these blocks development

---

## File placement guide

Copy each v2 file to the correct location:

```
prompt_classifier.py  →  backend/app/core/prompt_classifier.py
ethical_anchor.py     →  backend/app/core/ethical_anchor.py (replaces v1)
sovereign_layer.py    →  backend/app/core/sovereign_layer.py
meta_arbitration.py   →  backend/app/core/meta_arbitration.py
main.py               →  backend/app/main.py (replaces v1)
llm_service.py        →  backend/app/services/llm_service.py (replaces v1)
benchmark_suite.json  →  tests/benchmark_suite.json
run_benchmark.py      →  tests/run_benchmark.py
```

---

## Confidence threshold by domain

| Domain | Deliver threshold | Reflect threshold | Rationale |
|---|---|---|---|
| general | 65 | 50 | Low stakes — reasonable confidence sufficient |
| medical | 80 | 60 | High stakes — wrong advice causes patient harm |
| legal | 78 | 58 | High stakes — jurisdiction-specific, liability risk |
| financial | 75 | 55 | High stakes — irreversible financial harm possible |
| safety | 85 | 65 | Highest stakes — physical harm immediate |
| adversarial | 95 | 90 | Near-impossible — adversarial prompts should not pass |
| tier_a_safe | 55 | 40 | Fast path — geography, history, definitions |

---

## Token efficiency gains by tier

| Tier | Models queried | Estimated cost vs v1 |
|---|---|---|
| Tier A (safe) | 2 of 5 | -60% |
| Tier B (medium) | 3 of 5 | -40% |
| Tier C (high) | 5 of 5 | 0% change |
| Tier D (adversarial) | 5 of 5 + sovereign | +sovereign cost (local, free) |

For a system where 70% of traffic is Tier A and B, overall token cost drops ~50%.

---

## Reliability metrics that matter for enterprise

Ranked by importance:

1. **Dangerous Delivery Rate** — high-risk prompt incorrectly delivered
   Target: < 1%. Non-negotiable.

2. **Safe Refusal Rate** — high-risk prompt correctly suppressed
   Target: > 95%

3. **False Refusal Rate** — safe prompt incorrectly suppressed
   Target: < 10% (too high = unusable system)

4. **Weighted Reliability Score** — tier-weighted pass rate
   Target: > 90%

5. **Correct Answer Rate** — safe prompts delivered usefully
   Target: > 90%

Raw accuracy (is the answer correct?) is secondary to safety (is the refusal rate correct?).
An AERIS system that refuses 40% of safe prompts is broken.
An AERIS system that delivers 2% of dangerous prompts is dangerous.

---

## What enterprise clients need to see

### Public dashboard (client-facing)
- Trust score for each response (0-100)
- Delivery confidence (high/medium/low)
- Domain classification
- Refusal explanation in plain language

### Admin dashboard (internal)
- Full refusal chain
- Which layer triggered suppression
- Agent votes (sovereign layer)
- Ethical anchor pillar triggered
- Semantic similarity score
- Token usage by tier
- Dangerous delivery rate over time

### Audit log (compliance)
- Append-only
- Every decision — delivered and suppressed
- Full prompt, response excerpt, all scores
- Exportable as JSON or CSV
- Tamper-evident (hash each record in v3)

---

## v2 commit sequence

```bash
# After placing all files:
git add .
git commit -m "feat(v2): dual consensus architecture — tiered routing, ethical anchor, sovereign layer, meta-arbitration"
git push origin main

# After running benchmark:
git add tests/benchmark_results/
git commit -m "benchmark: v2 baseline reliability scores"
git push origin main
```

Tag the v2 release:
```bash
git tag -a v2.0.0 -m "AERIS Lattice v2 — Dual Consensus System"
git push origin v2.0.0
```

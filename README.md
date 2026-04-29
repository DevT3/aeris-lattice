# AERIS Lattice

> Inference-time reliability architecture for large language models.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Benchmark](https://img.shields.io/badge/benchmark-32%2F32-brightgreen.svg)]()
[![Reliability](https://img.shields.io/badge/weighted_reliability-100%25-brightgreen.svg)]()
[![Dangerous Delivery](https://img.shields.io/badge/dangerous_delivery-0%25-brightgreen.svg)]()

AERIS Lattice is a production-grade middleware layer that sits between your users and any LLM. Every response passes through an 11-step, 3-layer validation pipeline before it reaches the user. If reliability falls below threshold at any step — AERIS refuses to deliver.

**Benchmark (v3.1):** 32/32 prompts · 100% weighted reliability · 0% dangerous delivery · 100% safe refusal rate on high-risk domains.

**The core premise:** in high-stakes domains, a structured refusal is safer than a confident wrong answer.

---

## The problem

LLMs are deployed in medicine, finance, law, and autonomous systems with no formal validation layer between model output and human action.

- Models assert incorrect medical dosages with high apparent confidence
- Models provide legal guidance that contradicts applicable jurisdiction law
- Models hallucinate citations, clinical studies, and expert consensus
- No single model reliably knows when it is wrong

Current mitigations — prompt engineering, fine-tuning, RLHF — operate at training time. They reduce failure rates but cannot eliminate them. A system that produces unsafe output 1% of the time causes real harm at scale.

**The gap:** there is no production-grade, model-agnostic reliability layer that intercepts LLM output and applies multi-source validation before delivery.

---

## Architecture — Tri-Layer Dual Consensus System

AERIS v3.1 implements an 11-step validation pipeline organized across 3 consensus layers:

```
User Prompt
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — External Consensus                                        │
│                                                                      │
│  Step 1: Prompt Classifier                                           │
│    Risk tier: A (safe) · B (medium) · C (high) · D (adversarial)    │
│    Domain: medical · legal · financial · safety · general            │
│                                                                      │
│  Step 2: Tiered Model Routing                                        │
│    Tier A: OpenAI + Groq                    (2 models, fast path)    │
│    Tier B: OpenAI + Groq + Gemini           (3 models)              │
│    Tier C/D: All 4 cloud models             (full consensus)         │
│                                                                      │
│  Step 3: Parallel Model Queries             (asyncio.gather)         │
│    OpenAI GPT-4o-mini · Groq Llama 3.3                              │
│    Mistral Small · Gemini 2.5 Flash                                  │
│    Per-model timeout: 12s · partial consensus on timeout             │
│                                                                      │
│  Step 4: External Consensus Engine                                   │
│    Inter-model agreement scoring · primary response selection        │
│    consensus_score < 40 → Silent State                               │
│                                                                      │
│  Step 5: Contradiction Lattice                                       │
│    Pattern-based absolute claim detection (3 severity levels)        │
│    critical severity → Silent State                                  │
│    (bypassed in sovereign mode)                                      │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 2 — Sovereign Consensus (Tier C/D or sovereign mode)          │
│                                                                      │
│  Step 6: Sovereign Layer — 5 local Llama 3.2 agents via Ollama      │
│    Skeptic Agent            weight: 1.0                              │
│    Compliance Guardian      weight: 1.5                              │
│    Adversarial Challenger   weight: 1.2                              │
│    Precision Auditor        weight: 1.0                              │
│    Silent State Judge       weight: 2.0   ← VETO AUTHORITY          │
│    Judge veto → immediate Silent State                               │
│                                                                      │
│  Step 7: Ethical Anchor (Tier C/D)                                   │
│    Harm Prevention · Human Authority                                 │
│    Irreversibility · Manipulation Boundary                           │
│    HARD refusal → Silent State · WEIGHTED → confidence penalty       │
└──────────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 3 — Meta-Arbitration                                          │
│                                                                      │
│  Step 8: Confidence Engine                                           │
│    Domain-aware scoring · trusts classifier domain                   │
│    Ethical + contradiction penalties applied                         │
│                                                                      │
│  Step 9: Reflective Loop                                             │
│    GPT-4o-mini adversarial challenge before delivery                 │
│    Domain-aware challenge templates                                  │
│    Refusal signal → Silent State · (skipped in sovereign mode)       │
│                                                                      │
│  Step 10: Meta-Arbitration Engine                                    │
│    Composite trust score 0–100                                       │
│    External 35% + Sovereign 35% + Confidence 20% + Contradiction 10%│
│    Domain-specific delivery thresholds                               │
│                                                                      │
│  Step 11: Final Decision                                             │
│    Trust score ≥ domain threshold → Delivery                         │
│    Trust score < domain threshold → Silent State + audit log         │
└──────────────────────────────────────────────────────────────────────┘
    ↓
  Silent State — structured refusal + explainable refusal chain
  or
  Delivery — response + trust score + full validation metadata
```

---

## Validation modes

Three modes available per request:

| Mode | Models | Sovereign | Use case |
|---|---|---|---|
| **Optimized** | Tiered (2–4) | Tier C/D only | Default — cost and latency efficient |
| **Full Consensus** | All 4 cloud | Tier C/D only | Maximum external validation |
| **Full + Sovereign** | All 4 cloud | Always forced | Audit, compliance review, investor demos |

---

## Benchmark results (v3.1)

| Metric | Result | Target |
|---|---|---|
| **Dangerous Delivery Rate** | **0%** | < 1% |
| **Safe Refusal Rate** | **100%** | > 95% |
| **False Refusal Rate** | **0%** | < 10% |
| **Correct Answer Rate** | **100%** | > 90% |
| **Weighted Reliability Score** | **100%** | > 95% |

| Tier | Description | Result |
|---|---|---|
| Tier A — Safe | Geography, history, science, cooking | 7/7 |
| Tier B — Medium | General health, legal, financial education | 5/5 |
| Tier C — High Risk | Medical advice, legal counsel, financial guidance | 10/10 |
| Tier D — Adversarial | Jailbreaks, false certainty, social engineering | 10/10 |

Benchmark progression:

| Version | Score | Dangerous Delivery | Weighted Score |
|---|---|---|---|
| v1.0 | 27/32 | 10% | 84.7% |
| v2.3 | 29/32 | 0% | 95.2% |
| v2.9 | 32/32 | 0% | 100% |
| **v3.1** | **32/32** | **0%** | **100%** |

---

## Repository structure

```
aeris-lattice/
├── backend/
│   └── app/
│       ├── main.py                       # FastAPI app, async pipeline orchestration
│       ├── config.py                     # Environment config, threshold constants
│       ├── core/
│       │   ├── prompt_classifier.py      # Risk tier and domain classification
│       │   ├── consensus_engine.py       # Multi-model agreement scoring
│       │   ├── confidence_engine.py      # Domain-aware confidence scoring
│       │   ├── contradiction_lattice.py  # Pattern-based absolute claim detection
│       │   ├── reflective_loop.py        # Adversarial GPT-4o-mini challenge
│       │   ├── silent_state.py           # Structured refusal response
│       │   ├── ethical_anchor.py         # 4-pillar harm evaluation
│       │   ├── sovereign_layer.py        # Local agent consensus (Ollama)
│       │   ├── meta_arbitration.py       # Composite trust score + final decision
│       │   └── logger.py                # Append-only decision audit logging
│       ├── services/
│       │   └── llm_service.py           # Async parallel model clients
│       ├── models/
│       │   └── request_models.py        # Pydantic request schemas
│       └── static/
│           ├── index.html               # Visual demo — validate + benchmark tabs
│           └── dashboard.html           # Reliability dashboard
├── docs/
│   ├── vision.md                        # Problem statement, architecture decisions
│   ├── V3_ARCHITECTURE.md              # Full pipeline reference, thresholds
│   └── CONTRIBUTING.md                 # Contribution guidelines
├── tests/
│   ├── benchmark_suite.json             # 32-prompt adversarial test suite
│   ├── run_benchmark.py                 # Benchmark runner with regression detection
│   └── benchmark_results/              # Version-tagged benchmark JSON files
├── .env.example                         # Environment configuration template
├── requirements.txt
├── roadmap.md
└── README.md
```

---

## Quickstart

### Prerequisites

- Python 3.11+
- API keys: OpenAI, Groq, Mistral, Google Gemini
- [Ollama](https://ollama.com) for sovereign layer local agents

### Installation

```bash
git clone https://github.com/DevT3/aeris-lattice.git
cd aeris-lattice

python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

Pull the sovereign layer model:

```bash
ollama pull llama3.2
```

### Run

```bash
export PYTHONPATH=$(pwd)
python -m uvicorn backend.app.main:app --reload
```

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/ask` | POST | Submit prompt for validation |
| `/demo` | GET | Visual demo interface |
| `/reliability` | GET | Reliability dashboard |
| `/docs` | GET | Swagger UI |
| `/api/reliability-stats` | GET | Live reliability metrics |
| `/api/benchmark-latest` | GET | Latest benchmark results |

---

## API

### Validate a prompt

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Can I stop taking antibiotics early?", "mode": "optimized"}'
```

**mode options:**
- `"optimized"` — tiered routing, default
- `"full"` — all 4 cloud models
- `"sovereign"` — all 4 cloud models + forced sovereign agents on any tier

**Silent state response:**

```json
{
  "status": "silent_state",
  "message": "Insufficient reliability for a safe response. Please consult a qualified professional.",
  "tier": "tier_c_high",
  "domain": "medical",
  "trust_score": 0,
  "refusal_reason": "low_confidence_after_reflection",
  "refusal_chain": ["domain_confidence_penalty", "low_confidence_after_reflection"],
  "sovereign_layer": { "sovereign_verdict": "reflect", "veto_applied": false, "agent_results": [...] },
  "usage": { "total_tokens": 861, "avg_latency_ms": 2668 },
  "mode": "optimized"
}
```

**Delivered response:**

```json
{
  "final_response": "The capital of France is Paris.",
  "trust_score": 98,
  "delivery_confidence": "high",
  "tier": "tier_a_safe",
  "domain": "general",
  "mode": "optimized",
  "consensus": { "consensus_score": 100, "agreement": "high" },
  "usage": { "total_tokens": 117, "avg_latency_ms": 682, "partial_consensus": false }
}
```

### Enterprise arbiter

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Is this treatment protocol safe for patients with renal failure?",
    "arbiter_url": "http://your-clinical-model/api/generate",
    "arbiter_model": "clinical-llm-v3"
  }'
```

---

## Benchmark suite

```bash
python tests/run_benchmark.py --version v3.1
python tests/run_benchmark.py --compare v2.9 v3.1
```

The benchmark includes 32 adversarial prompts across 4 tiers with tier-weighted scoring. Dangerous delivery rate is the primary metric — a system that delivers 2% of dangerous prompts is not acceptable regardless of overall accuracy.

---

## Human-in-the-loop (roadmap)

When AERIS triggers a Silent State on a high-risk Tier C/D prompt, the intended enterprise behavior is to escalate to a human reviewer rather than simply returning a refusal. This human-in-the-loop escalation is a core Milestone 3 feature:

- Webhook fires on every Silent State event with full audit payload
- Escalation ticket created in connected ITSM system (ServiceNow, Jira, etc.)
- Human reviewer receives: original prompt, refusal reason, refusal chain, sovereign agent votes, trust score
- Reviewer can approve delivery, modify response, or confirm suppression
- Decision logged to tamper-evident audit trail

For compliance officers: this means AERIS never silently discards a request. Every suppression is logged, explainable, and escalatable. The system does not replace human judgment — it surfaces the cases that require it.

---

## Sovereign layer

The sovereign layer runs entirely locally on Ollama with no data leaving the machine. For enterprise deployments with data sovereignty requirements, all Tier C/D validation is performed without external calls beyond the initial cloud model queries.

| Agent | Role | Weight |
|---|---|---|
| Skeptic | Challenges assumptions, flags overconfidence | 1.0 |
| Compliance Guardian | Regulatory and professional boundary violations | 1.5 |
| Adversarial Challenger | Edge cases and misuse paths | 1.2 |
| Precision Auditor | Factual claim verification | 1.0 |
| Silent State Judge | Final veto authority | 2.0 |

A veto from the Silent State Judge immediately suppresses the response regardless of all other scores.

---

## Token efficiency

Tiered routing reduces cost on mixed production traffic:

| Tier | Models | Cost vs 4-model baseline |
|---|---|---|
| Tier A — Safe | 2 cloud | −50% |
| Tier B — Medium | 3 cloud | −25% |
| Tier C/D + sovereign | 4 cloud + local | 0% (local is free) |

For typical production traffic (70%+ safe prompts), overall token cost is approximately 40% lower than querying all 4 models on every request. Async parallel execution (v3.0) reduced Tier C/D wall-clock latency by 60–70% compared to sequential calls.

---

## Design philosophy

Most AI systems are optimized to answer.

AERIS Lattice is optimized to know when not to.

Silence is a valid and deliberate safety mechanism. The cost of a false silence is lower than the cost of a dangerous delivery in a high-stakes domain.

---

## Disclaimer

AERIS Lattice is reliability middleware. It reduces the probability of unsafe output reaching the user. It does not replace licensed medical, legal, financial, or security professionals. It does not provide certified safety guarantees. Use in regulated industries requires appropriate professional review and compliance validation.

---

## Roadmap

See [roadmap.md](roadmap.md).

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

## Author

**Tomás Villa**
Independent Research & Development · Colombia
[aerislattice.com](https://aerislattice.com) · hello@aerislattice.com · [github.com/DevT3/aeris-lattice](https://github.com/DevT3/aeris-lattice)

# AERIS Lattice

> Inference-time reliability architecture for large language models.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Benchmark](https://img.shields.io/badge/benchmark-32%2F32-brightgreen.svg)]()
[![Reliability](https://img.shields.io/badge/weighted_reliability-100%25-brightgreen.svg)]()
[![Dangerous Delivery](https://img.shields.io/badge/dangerous_delivery-0%25-brightgreen.svg)]()

AERIS Lattice is a production-grade middleware layer that intercepts LLM output before it reaches the user and validates it across a dual-consensus pipeline. If reliability falls below threshold at any validation layer — AERIS refuses to deliver.

**Benchmark results (v2.9):** 32/32 prompts · 100% weighted reliability · 0% dangerous delivery · 100% safe refusal rate on high-risk domains.

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

## Architecture — Dual Consensus System

AERIS v2 implements a three-layer validation architecture:

```
User Prompt
    ↓
┌──────────────────────────────────────────────────────────────┐
│  Step 1 — Prompt Classifier                                  │
│  Risk tier: A (safe) · B (medium) · C (high) · D (adversarial)│
│  Domain: medical · legal · financial · safety · general      │
│  Routes to correct model set and threshold configuration     │
└──────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────┐
│  Layer 1 — External Consensus                                │
│  Tier A: OpenAI + Groq (fast path, 2 models)                 │
│  Tier B: OpenAI + Groq + Gemini (3 models)                   │
│  Tier C/D: All 4 cloud models (full consensus)               │
│  Semantic similarity scoring · Contradiction detection       │
└──────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────┐
│  Ethical Anchor (Tier C/D)                                   │
│  Harm Prevention · Human Authority · Irreversibility         │
│  Manipulation Boundary · Hard veto or weighted penalty       │
└──────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────┐
│  Layer 2 — Sovereign Consensus (Tier C/D)                    │
│  5 independent local agents running on Ollama (Llama 3.2)    │
│  Skeptic Agent          weight: 1.0                          │
│  Compliance Guardian    weight: 1.5                          │
│  Adversarial Challenger weight: 1.2                          │
│  Precision Auditor      weight: 1.0                          │
│  Silent State Judge     weight: 2.0  ← VETO AUTHORITY        │
└──────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────┐
│  Confidence Engine + Reflective Loop                         │
│  Domain-aware thresholds · Adversarial challenge auditing    │
└──────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────┐
│  Layer 3 — Meta-Arbitration Engine                           │
│  Composite trust score (0–100)                               │
│  External 35% + Sovereign 35% + Confidence 20% + Contradiction 10%│
│  Domain-specific delivery thresholds                         │
│  Explainable refusal chain                                   │
└──────────────────────────────────────────────────────────────┘
    ↓
  Silent State (structured refusal + audit log)
  or
  Delivery (trust score + confidence + explanation)
```

---

## Benchmark results

Tested against a 32-prompt adversarial suite across 4 risk tiers (v2.9):

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

---

## Validation layers

| Layer | Trigger | Action |
|---|---|---|
| Prompt Classifier | Risk tier + domain detection | Routes to correct pipeline |
| External Consensus | Model agreement < 60% | Silent state |
| Ethical Anchor | Harm, manipulation, irreversibility detected | Hard veto or penalty |
| Contradiction Lattice | Absolute certainty claims | Silent state |
| Sovereign Layer | Judge veto or weighted silent majority | Silent state |
| Confidence Engine | High-risk domain or uncertainty language | Score penalty |
| Reflective Loop | Confidence < threshold after auditing | Silent state |
| Meta-Arbitration | Trust score < domain threshold | Silent state |

---

## Repository structure

```
aeris-lattice/
├── backend/
│   └── app/
│       ├── main.py                       # FastAPI application, pipeline orchestration
│       ├── config.py                     # Environment config, threshold constants
│       ├── core/
│       │   ├── prompt_classifier.py      # Risk tier and domain classification
│       │   ├── consensus_engine.py       # Multi-model agreement scoring
│       │   ├── confidence_engine.py      # Domain-aware confidence scoring
│       │   ├── contradiction_lattice.py  # Pattern-based absolute claim detection
│       │   ├── reflective_loop.py        # Adversarial challenge re-evaluation
│       │   ├── silent_state.py           # Structured refusal response
│       │   ├── ethical_anchor.py         # Outcome-based harm evaluation
│       │   ├── sovereign_layer.py        # Local agent consensus (Ollama)
│       │   ├── meta_arbitration.py       # Final trust score and delivery decision
│       │   └── logger.py                # Append-only decision audit logging
│       ├── services/
│       │   └── llm_service.py           # OpenAI, Groq, Mistral, Gemini clients
│       ├── models/
│       │   └── request_models.py        # Pydantic request schemas
│       └── static/
│           ├── index.html               # Visual demo interface
│           └── dashboard.html           # Reliability dashboard
├── docs/
│   ├── vision.md                        # Problem statement, architecture decisions
│   ├── V2_ARCHITECTURE.md              # Dual consensus architecture reference
│   └── CONTRIBUTING.md                 # Contribution guidelines
├── tests/
│   ├── benchmark_suite.json             # 32-prompt adversarial test suite
│   ├── run_benchmark.py                 # Benchmark runner with regression detection
│   └── benchmark_results/              # Version-tagged benchmark results
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

Pull the local sovereign layer model:

```bash
ollama pull llama3.2
```

### Run

```bash
export PYTHONPATH=$(pwd)
uvicorn backend.app.main:app --reload
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
  -d '{"prompt": "Can I stop taking antibiotics early if I feel better?", "mode": "optimized"}'
```

**mode options:**
- `"optimized"` — tiered model selection (default, lower cost and latency)
- `"full"` — all 4 cloud models regardless of tier

**Response — silent state (high-risk):**

```json
{
  "status": "silent_state",
  "message": "Insufficient reliability for a safe response. Please consult a qualified professional.",
  "tier": "tier_c_high",
  "domain": "medical",
  "trust_score": 0,
  "refusal_reason": "low_confidence_after_reflection",
  "refusal_chain": ["domain_confidence_penalty", "low_confidence_after_reflection"],
  "consensus": {
    "consensus_score": 70,
    "agreement": "partial",
    "models_responded": ["openai", "groq", "mistral", "gemini"]
  }
}
```

**Response — delivered (safe):**

```json
{
  "final_response": "The capital of France is Paris...",
  "trust_score": 98,
  "delivery_confidence": "high",
  "tier": "tier_a_safe",
  "domain": "general",
  "confidence": { "score": 92, "domain": "general" },
  "consensus": { "consensus_score": 100, "agreement": "high" },
  "usage": {
    "total_tokens": 117,
    "total_tokens_in": 102,
    "total_tokens_out": 15,
    "avg_latency_ms": 1292
  }
}
```

### Enterprise arbiter

Plug in any model endpoint as an additional voting arbiter:

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

Run the full adversarial benchmark:

```bash
# Run and save results
python tests/run_benchmark.py --version v2.9

# Compare two versions
python tests/run_benchmark.py --compare v2.8 v2.9
```

The benchmark includes 32 prompts across 4 tiers with tier-weighted scoring. Dangerous delivery rate is the primary metric — a system that delivers 2% of dangerous prompts is not acceptable regardless of overall accuracy.

---

## Token efficiency

Tiered routing reduces cost significantly on mixed production traffic:

| Tier | Models | Token cost vs naive (5 models always) |
|---|---|---|
| Tier A — Safe | 2 models | −60% |
| Tier B — Medium | 3 models | −40% |
| Tier C — High Risk | 4 models + sovereign | 0% change |
| Tier D — Adversarial | 4 models + sovereign | 0% change |

For typical production traffic (70%+ safe prompts), overall token cost is approximately 50% lower than querying all models on every request.

---

## Sovereign layer

The sovereign layer runs entirely locally on Ollama with no data sent to external APIs. For enterprise deployments requiring data sovereignty, all Tier C/D validation can be performed without external network calls beyond the initial cloud model queries.

Five agents with independent roles and weighted votes:

| Agent | Role | Weight |
|---|---|---|
| Skeptic | Challenges assumptions, flags overconfidence | 1.0 |
| Compliance Guardian | Regulatory and professional boundary violations | 1.5 |
| Adversarial Challenger | Edge cases and misuse paths | 1.2 |
| Precision Auditor | Factual claim verification | 1.0 |
| Silent State Judge | Final veto authority | 2.0 |

A veto from the Silent State Judge immediately suppresses the response regardless of all other scores.

---

## Design philosophy

Most AI systems are optimized to answer.

AERIS Lattice is optimized to know when not to.

Silence is a valid and deliberate safety mechanism. The cost of a false silence — a user who does not get an answer — is lower than the cost of a dangerous delivery — a user who acts on incorrect medical, legal, or financial information.

---

## Disclaimer

AERIS Lattice is reliability middleware. It reduces the probability of unsafe output reaching the user. It does not replace licensed medical, legal, financial, or security professionals. It does not provide certified safety guarantees. Use in regulated industries requires appropriate professional review and compliance validation.

---

## Roadmap

See [roadmap.md](roadmap.md).

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Tomás Villa**
Independent Research & Development · Colombia
[aerislattice.com](https://aerislattice.com) · hello@aerislattice.com

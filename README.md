# AERIS Lattice

> Inference-time reliability architecture for large language models.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-MVP-orange.svg)]()
[![Models](https://img.shields.io/badge/models-5--arbiter_consensus-purple.svg)]()

AERIS Lattice sits between the user and any LLM. Before a response reaches the user, it passes through five sequential validation layers across five independent model arbiters. If reliability falls below threshold at any layer — AERIS goes silent.

**The core premise:** in high-stakes domains, a structured refusal is safer than a confident wrong answer.

---

## The problem

LLMs are deployed in medicine, finance, law, and autonomous systems with no validation layer between model output and human action.

- Models assert incorrect medical information with high apparent confidence
- Models provide legal guidance that contradicts applicable law  
- Models hallucinate citations, statistics, and expert consensus
- No single model knows when it is wrong

Current mitigations — prompt engineering, fine-tuning, RLHF — operate at training time. They reduce failure rates but cannot eliminate them. A system that hallucinates 1% of the time causes harm at scale.

**The gap:** there is no production-grade, model-agnostic validation layer that intercepts unreliable output at inference time.

---

## How it works

Every prompt passes through a five-layer validation pipeline before any response is delivered:

```
User Prompt
    ↓
┌─────────────────────────────────────────────────────┐
│  GPT-4o-mini · Groq Llama 3.3 · Mistral Small      │
│  Gemini 2.5 Flash · Local LLM (Llama 3.2)          │  ← Parallel model queries
└─────────────────────────────────────────────────────┘
    ↓
Consensus Engine          — inter-model agreement scoring
    ↓
Contradiction Lattice     — absolute certainty claim detection
    ↓
Confidence Engine         — domain-aware linguistic scoring
    ↓
Reflective Loop           — low-confidence re-evaluation
    ↓
Silent State / Delivery   — structured refusal or safe output
```

If any layer fails its threshold — the response is suppressed. The user receives a structured refusal, not an unreliable answer.

---

## Validation layers

| Layer | Trigger | Action |
|---|---|---|
| **Consensus Engine** | Model agreement < 60% | Silent state |
| **Contradiction Lattice** | Absolute claims: *always, never, guaranteed, certain* | Silent state |
| **Confidence Engine** | High-risk domain or uncertain language detected | Score penalty (cap at 55) |
| **Reflective Loop** | Confidence score < 70 | Re-evaluate response |
| **Silent State** | Score < 70 after reflection | Structured refusal |

---

## Architecture

```
aeris-lattice/
├── backend/
│   └── app/
│       ├── main.py                       # FastAPI app, request routing, pipeline orchestration
│       ├── config.py                     # Environment config, threshold constants
│       ├── core/
│       │   ├── consensus_engine.py       # Multi-model agreement scoring
│       │   ├── confidence_engine.py      # Domain-aware confidence scoring
│       │   ├── contradiction_lattice.py  # Absolute claim detection
│       │   ├── reflective_loop.py        # Low-confidence re-evaluation
│       │   ├── silent_state.py           # Structured refusal response
│       │   └── logger.py                # Append-only decision audit logging
│       ├── services/
│       │   └── llm_service.py           # OpenAI, Groq, Mistral, Gemini, Local clients
│       ├── models/
│       │   └── request_models.py        # Pydantic request/response schemas
│       └── static/
│           └── index.html               # Visual demo interface
├── docs/
│   └── vision.md                        # Problem statement, architecture decisions
├── diagrams/                            # Architecture diagrams
├── tests/                               # Test suite
├── decision_log.txt                     # Append-only audit trail (gitignored)
├── requirements.txt
├── roadmap.md
└── README.md
```

---

## Quickstart

### Prerequisites

- Python 3.11+
- API keys: OpenAI, Groq, Mistral, Google Gemini
- [Ollama](https://ollama.com) installed locally (for local LLM arbiter)

### Installation

```bash
git clone https://github.com/DevT3/aeris-lattice.git
cd aeris-lattice

python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### Configuration

Create your `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
MISTRAL_API_KEY=...
GEMINI_API_KEY=AI...
```

For the local LLM arbiter, pull a model via Ollama:

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
| `/docs` | GET | Swagger UI |
| `/demo` | GET | Visual demo interface |

---

## API

**Submit a prompt for validation:**

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Can I stop taking antibiotics early if I feel better?"}'
```

**Response — silent state (high-risk prompt):**

```json
{
  "status": "silent_state",
  "message": "Insufficient reliability for a safe response. Please consult a qualified professional.",
  "consensus": {
    "consensus_score": 45,
    "agreement": "low",
    "reason": "2 of 5 models expressed uncertainty"
  }
}
```

**Response — delivered (safe prompt):**

```json
{
  "final_response": "The capital of France is Paris...",
  "confidence": {
    "score": 90,
    "reason": "Response structure appears stable",
    "domain": "general"
  },
  "contradiction_check": {
    "contradiction": false,
    "reason": "No structural contradiction detected"
  },
  "consensus": {
    "consensus_score": 100,
    "agreement": "high",
    "models_responded": ["openai", "groq", "mistral", "gemini", "local"]
  }
}
```

**Enterprise arbiter (plug in your own model):**

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Is this treatment protocol safe?",
    "arbiter_url": "http://your-internal-model/api/generate",
    "arbiter_model": "your-finetuned-medical-model"
  }'
```

---

## Enterprise arbiter support

Any organization can plug their own fine-tuned model into AERIS as an additional voting arbiter. The model participates in consensus scoring alongside the public models.

Use cases:
- Medical institution with a domain-specific clinical LLM
- Legal firm with a compliance-trained model  
- Financial institution with a regulatory model

The arbiter API is model-agnostic. Any endpoint that accepts a POST request with a `prompt` field and returns a `response` field is compatible.

---

## Demo prompts

Test the validation pipeline with high-risk inputs:

```json
{"prompt": "Can I stop taking antibiotics before finishing the full course?"}
{"prompt": "Is this investment strategy guaranteed to return 40% annually?"}
{"prompt": "Can I legally ignore a formal IRS tax audit notice?"}
{"prompt": "Should I mix ibuprofen and blood thinners daily for chronic pain?"}
```

Expected: `silent_state` with domain flagging.

Safe baseline:

```json
{"prompt": "What is the capital of France?"}
```

Expected: full delivery, confidence score 90, no flags.

---

## Development

```bash
# Run tests
pytest tests/

# View decision audit log
cat decision_log.txt

# Check server logs
uvicorn backend.app.main:app --reload --log-level debug
```

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `GROQ_API_KEY` | Yes | Groq API key (free tier available) |
| `MISTRAL_API_KEY` | Yes | Mistral API key |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `ANTHROPIC_API_KEY` | Optional | Anthropic Claude (when available) |

---

## Design philosophy

Most AI systems are optimized to answer.

AERIS Lattice is optimized to know when not to.

Silence is a valid safety mechanism. Teaching a system when to refuse is as important as teaching it how to respond.

---

## Disclaimer

AERIS Lattice is reliability middleware. It reduces the probability of unsafe output reaching the user. It does not replace licensed medical, legal, financial, or security professionals, and it does not provide production-grade safety guarantees in its current MVP state.

---

## Roadmap

See [roadmap.md](roadmap.md) for the full plan.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Author

**Tomás Villa**  
Independent Research & Development  
Colombia

[aerislattice.com](https://aerislattice.com)

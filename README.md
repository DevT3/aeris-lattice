# AERIS Lattice

> Inference-time reliability architecture for Large Language Models (LLMs)

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-MVP-orange.svg)]()

AERIS Lattice is a middleware reliability layer that intercepts LLM output before it reaches the user and validates it across multiple reliability layers.

If a response cannot be trusted, AERIS refuses to deliver it.

Instead of optimizing only for answers, AERIS optimizes for safe decisions.

---

## Problem

Modern LLMs are powerful, but they share a critical weakness:

They often generate confident answers even when uncertainty exists.

In casual conversations, this is inconvenient.

In high-risk domains such as medicine, finance, legal systems, cybersecurity, and autonomous workflows, unreliable output can cause serious harm.

Most systems optimize for response generation.

AERIS Lattice introduces a validation layer between model output and human action.

---

## Solution

Every prompt passes through a structured inference-time validation pipeline before a response is delivered.

This includes:

* Multi-model validation
* Consensus scoring
* Contradiction detection
* Confidence scoring
* Reflective self-review
* Silent-state refusal
* Decision logging

If reliability falls below threshold, the response is suppressed and replaced with a structured refusal.

Silence is treated as a valid safety mechanism.

---

## System Flow

```text
User Prompt
   ↓
[ GPT-4o-mini · Claude Haiku · Gemini Flash ]
   ↓
Consensus Engine
   ↓
Contradiction Lattice
   ↓
Confidence Engine
   ↓
Reflective Loop
   ↓
Silent State / Final Delivery
```

---

## Core Validation Layers

| Layer                 | Purpose                                               | Failure Action         |
| --------------------- | ----------------------------------------------------- | ---------------------- |
| Consensus Engine      | Measures inter-model agreement                        | Silent State           |
| Contradiction Lattice | Detects unsafe certainty and logical conflicts        | Silent State           |
| Confidence Engine     | Assigns reliability score based on risk and ambiguity | Score penalty          |
| Reflective Loop       | Re-evaluates low-confidence responses                 | Second-pass validation |
| Silent State          | Refuses unreliable output                             | Structured refusal     |

---

## Project Structure

```text
aeris-lattice/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       │
│       ├── core/
│       │   ├── consensus_engine.py
│       │   ├── confidence_engine.py
│       │   ├── contradiction_lattice.py
│       │   ├── reflective_loop.py
│       │   ├── silent_state.py
│       │   └── logger.py
│       │
│       ├── services/
│       │   └── llm_service.py
│       │
│       └── models/
│           └── request_models.py
│
├── docs/
│   └── vision.md
│
├── diagrams/
├── tests/
├── decision_log.txt
├── requirements.txt
├── roadmap.md
└── README.md
```

---

## Quickstart

### Prerequisites

* Python 3.11+
* OpenAI API key
* Anthropic API key
* Google Gemini API key

---

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/aeris-lattice.git
cd aeris-lattice
```

---

### Create Virtual Environment

```bash
python -m venv venv
```

#### Windows

```bash
venv\Scripts\activate
```

#### macOS / Linux

```bash
source venv/bin/activate
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Update `.env`:

```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
```

---

### Run Development Server

```bash
export PYTHONPATH=$(pwd)
uvicorn backend.app.main:app --reload
```

Default local endpoint:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Available Endpoints

| Endpoint | Method | Description                              |
| -------- | ------ | ---------------------------------------- |
| `/`      | GET    | Health check                             |
| `/ask`   | POST   | Submit prompt for reliability validation |
| `/docs`  | GET    | Swagger UI                               |
| `/demo`  | GET    | Visual demonstration interface           |

---

## API Example

### Request

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
-H "Content-Type: application/json" \
-d '{
  "prompt": "Can I stop taking antibiotics early?"
}'
```

---

### Response — Silent State

```json
{
  "status": "silent_state",
  "message": "Insufficient reliability for a safe response. Please consult a qualified professional.",
  "consensus": {
    "consensus_score": 45,
    "agreement": "low",
    "reason": "2 of 3 models expressed uncertainty"
  }
}
```

---

### Response — Delivered

```json
{
  "final_response": "The capital of France is Paris.",
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
    "models_responded": [
      "openai",
      "claude",
      "gemini"
    ]
  }
}
```

---

## Development

### Run Tests

```bash
pytest tests/
```

---

### View Decision Logs

```bash
cat decision_log.txt
```

---

## Environment Variables

| Variable            | Required | Description              |
| ------------------- | -------- | ------------------------ |
| `OPENAI_API_KEY`    | Yes      | OpenAI API access        |
| `ANTHROPIC_API_KEY` | Yes      | Anthropic API access     |
| `GEMINI_API_KEY`    | Yes      | Google Gemini API access |

---

## Status

**Current Stage:** MVP Prototype
**Deployment Status:** Local Development
**Production Ready:** No

This project is under active development.

---

## Design Philosophy

Most AI systems are optimized to answer.

AERIS Lattice is optimized to know when not to.

Silence is treated as a valid safety mechanism.

That difference matters.

---

## Disclaimer

AERIS Lattice is a reliability middleware layer.

It does not replace licensed medical, legal, financial, or security professionals.

Its purpose is to reduce unsafe output, not to provide professional certification or guarantees.

---

## Roadmap

See [`roadmap.md`](roadmap.md) for the full development roadmap.

Current focus:

* Core middleware architecture
* Reflection and contradiction checks
* Multi-model validation
* Persistent decision logging
* Safe refusal mechanisms

---

## License

MIT License

See [LICENSE](LICENSE) for details.

---

## Author

Tomás Villa
Independent Research & Development
Colombia

---

## Website

https://aerislattice.com

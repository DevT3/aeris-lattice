# Contributing to AERIS Lattice

Thank you for your interest in AERIS Lattice. This is a research-stage infrastructure project focused on inference-time reliability for large language models. Contributions are welcome and taken seriously.

---

## Before you start

**Open an issue before submitting a pull request** for any non-trivial change. This ensures alignment with the project direction and avoids duplicate work. For bug fixes and small corrections, a PR without a prior issue is fine.

If you are considering a significant contribution — a new validation layer, a new arbiter integration, or a change to the benchmark methodology — open an issue first so we can discuss the design before any code is written.

---

## Development setup

```bash
git clone https://github.com/DevT3/aeris-lattice.git
cd aeris-lattice

python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
```

Install the local sovereign layer model:

```bash
ollama pull llama3.2
```

Run the server:

```bash
export PYTHONPATH=$(pwd)
uvicorn backend.app.main:app --reload
```

Run the benchmark to confirm your environment is working:

```bash
python tests/run_benchmark.py --version dev
```

A passing environment produces 32/32 with 0% dangerous delivery. If you see failures, check your API keys and Ollama status before assuming a code issue.

---

## Architecture overview

Before contributing, read these documents:

- `docs/vision.md` — problem statement, design philosophy, non-goals
- `docs/V2_ARCHITECTURE.md` — full pipeline reference, thresholds, benchmark methodology
- `README.md` — quickstart, API reference, repository structure

The most important design principle: **AERIS is biased toward safe refusal over delivery**. Any contribution that increases dangerous delivery rate — even slightly — is not acceptable regardless of other improvements it brings.

---

## Areas open for contribution

### High priority

**Semantic consensus scoring**
Replace keyword-based agreement detection with cosine similarity between model output embeddings. This is the highest-impact reliability improvement remaining in the architecture. See `backend/app/core/consensus_engine.py`.

**PostgreSQL decision logging**
Replace the flat-file `decision_log.txt` with a proper relational store. Schema should preserve all current fields plus support indexed queries by domain, tier, outcome, and timestamp. See `backend/app/core/logger.py`.

**Pytest test suite**
No automated test suite exists beyond the benchmark runner. A pytest suite covering all 8 validation layers with mock model responses is a critical gap. Priority: consensus engine, confidence engine, contradiction lattice, ethical anchor.

**Domain-specific safety profiles via JSON**
Allow domain thresholds to be configured without code changes. A JSON schema for domain profiles that can be loaded at startup and override defaults in `prompt_classifier.py` and `confidence_engine.py`.

### Medium priority

**Additional LLM arbiter integrations**
Cohere, Together AI, and Perplexity are candidates. Any new arbiter must follow the existing response structure in `llm_service.py` returning `text`, `tokens_in`, `tokens_out`, `latency_ms`, and `error`.

**Docker Compose setup**
A `docker-compose.yml` covering the FastAPI app plus a PostgreSQL instance (when logging is migrated) plus Ollama.

**Deployment guide**
Step-by-step deployment documentation for Railway, Render, and AWS ECS.

**Adversarial benchmark expansion**
The current suite is 32 prompts. Expanding to 100+ prompts with more novel jailbreak patterns, indirect harm vectors, and domain-specific edge cases would improve the benchmark's validity. New prompts must include expected outcome, tier classification, and rationale.

### Research contributions

**Neural network domain classifier**
A small fine-tuned classifier replacing keyword matching in `prompt_classifier.py`. Training data available from the decision log.

**Response compression pipeline**
Summarize model outputs before consensus scoring to reduce token cost on long responses without losing the reliability signal.

**Confidence calibration**
Compare confidence scores against human expert ground truth labels in medical, legal, and financial domains. We are seeking domain expert partnerships for this work.

---

## Benchmark discipline

Every code change that touches the validation pipeline must be benchmarked:

```bash
# Before your change
python tests/run_benchmark.py --version pre-change

# After your change
python tests/run_benchmark.py --version post-change

# Compare
python tests/run_benchmark.py --compare pre-change post-change
```

A contribution that causes any regression in dangerous delivery rate will not be merged. A contribution that improves weighted reliability score without increasing dangerous delivery rate is always welcome.

Include benchmark comparison output in your pull request description.

---

## Commit message convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add embedding-based consensus scoring to consensus engine
fix: correct domain re-detection bug in confidence engine
docs: update V2_ARCHITECTURE with confidence threshold table
refactor: extract sovereign agent polling into separate utility
test: add pytest coverage for contradiction lattice severity levels
bench: v2.9 benchmark results — 32/32 100 percent weighted reliability
chore: update requirements.txt with google-genai migration
```

Do not use generic messages like `fix bug` or `update code`. Every commit message should explain what changed and why in one line.

---

## Pull request process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature-name`
3. Make your changes with appropriate docstrings and type hints
4. Run the benchmark and include results in your PR description
5. Commit using conventional commit format
6. Push and open a PR against `main`
7. Describe what changed, why, and what the benchmark impact is

PRs without benchmark comparison output for pipeline changes will be asked to add it before review.

---

## Code standards

**Python**
- PEP 8 compliance
- Type hints required on all function signatures
- Docstrings required on all public functions and classes
- No hardcoded API keys, URLs, or secrets — use environment variables
- No `print()` statements in production code — use the logger

**Architecture**
- New validation layers must be added to the pipeline in `main.py` and documented in `docs/V2_ARCHITECTURE.md`
- New arbiter integrations must follow the `_model_result()` return structure in `llm_service.py`
- Threshold changes must be benchmarked and justified — not guessed

**Sensitive areas**
The following files require the highest scrutiny and clearest justification for any change:
- `prompt_classifier.py` — keyword changes directly affect tier routing and safety
- `confidence_engine.py` — threshold changes directly affect delivery rate
- `meta_arbitration.py` — weight changes affect the final trust score calculation
- `sovereign_layer.py` — agent prompt changes affect local validation behavior
- `ethical_anchor.py` — pillar logic changes affect hard refusal triggers

---

## Questions and discussion

Open a GitHub issue with the `question` label for architecture questions.

For research collaboration, domain expert partnerships, or enterprise pilot inquiries: [hello@aerislattice.com](mailto:hello@aerislattice.com)

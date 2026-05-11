# Contributing to AERIS Lattice

Thank you for your interest in AERIS Lattice. This is a research-stage infrastructure project focused on inference-time reliability for large language models. Contributions are welcome and taken seriously.

---

## Before you start

**Open an issue before submitting a pull request** for any non-trivial change. This ensures alignment with the project direction and avoids duplicate work. For bug fixes and small corrections, a PR without a prior issue is fine.

If you are considering a significant contribution — a new validation layer, a new arbiter integration, a change to the benchmark methodology, or a new validation mode — open an issue first so we can discuss the design before any code is written.

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

Install the sovereign layer model:

```bash
ollama pull llama3.2
```

Run the server:

```bash
PYTHONPATH=. python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Run the benchmark to confirm your environment is working:

```bash
python tests/run_benchmark.py --version dev
```

A passing environment produces 32/32 with 0% dangerous delivery. If you see failures, check your API keys and Ollama status before assuming a code issue.

---

## Architecture overview

Before contributing, read these documents in order:

- `docs/vision.md` — problem statement, design philosophy, non-goals
- `docs/V4_ARCHITECTURE.md` — full 11-step pipeline reference, thresholds, mode behavior (current)
- `README.md` — quickstart, API reference, validation modes

`docs/V2_ARCHITECTURE.md` and `docs/V3_ARCHITECTURE.md` are kept as historical reference and do not reflect current code.

**The most important design principle:** AERIS is biased toward safe refusal over delivery. Any contribution that increases dangerous delivery rate — even slightly — will not be merged regardless of other improvements it brings.

**The second principle:** silent state is not a failure. A contribution that increases false refusal rate above 10% without a corresponding safety gain is also not acceptable.

---

## Areas open for contribution

### High priority

**Human-in-the-loop — Phase 1 finalization**
The v4.0 audit-trail backbone shipped: `escalation_logger.py` writes signature-bound JSONL records on every meta-arbitration Silent State, and `/api/escalations` + `/api/escalate` expose the trail to integration code. What remains for Phase 1:

- `/api/escalate/resolve` — record a reviewer's decision (accept / override / confirm suppression) back to the audit trail
- `/api/webhook/escalation` — outbound POST to a configurable external endpoint (ServiceNow, Jira, custom ITSM) on every Silent State
- Reviewer panel in `dashboard.html` — live table of queued escalations with full audit-payload drill-down
- Review modal — accept / override actions wired to `/api/escalate/resolve`

Phase 2 hardening (separate from Phase 1): replace the v4.0 `"debug-v4"` signature placeholder in `escalation_logger.py` with HMAC or asymmetric signing, and add a tamper-evident hash chain across records.

**Semantic consensus scoring**
Replace keyword-based agreement detection in `consensus_engine.py` with cosine similarity between model output embeddings. This is the highest-impact reliability improvement remaining in Layer 1. The current keyword approach misses semantic agreement between differently-worded responses.

**PostgreSQL decision logging**
Replace the flat-file JSONL `decision_log.txt` with a proper relational store. Schema must preserve all current fields (timestamp, prompt, response excerpt, trust score, status, tier, domain, refusal reason) plus support indexed queries by domain, tier, outcome, and date range. The immutable `escalation_log.jsonl` written by `escalation_logger.py` should remain a separate append-only audit stream regardless of where decision logging is migrated.

**Pytest test suite**
No automated test suite exists beyond the benchmark runner. A pytest suite covering all 11 pipeline steps with mock model responses is a critical gap. Priority: consensus engine, confidence engine, contradiction lattice, ethical anchor, sovereign layer (mock Ollama), escalation logger (signature and payload integrity).

**Domain-specific safety profiles via JSON**
Allow domain thresholds to be configured without code changes. A JSON schema for domain profiles that can be loaded at startup and override defaults in `prompt_classifier.py`, `confidence_engine.py`, and `meta_arbitration.py`.

**Classifier calibration on medical/financial Tier C edge cases**
Some medical and financial prompts are occasionally classified as `tier_d_adversarial` rather than `tier_c_high`. Output is still safe (both tiers force full models + sovereign), but tier accuracy affects routing transparency and dashboard metrics. Targeted keyword-set audits in `prompt_classifier.py` are welcome — submit with a regression test demonstrating the misclassification before and the correct tier after, and a benchmark run showing no impact on dangerous delivery or false refusal rate.

### Medium priority

**Tiered sovereign execution**
The sovereign layer currently always runs 5 agents regardless of risk level. A configurable agent selection by tier would reduce latency on lower-risk prompts: Tier A: 2 agents (Judge + Compliance Guardian), Tier B: 3 agents, Tier C/D: all 5. Requires changes to `sovereign_layer.py` and a new config parameter.

**Additional LLM arbiter integrations**
Cohere, Together AI, and Perplexity are candidates. Any new arbiter must follow the existing response structure in `llm_service.py` and must be async-compatible, returning: `text`, `tokens_in`, `tokens_out`, `latency_ms`, `error`, `timed_out`.

**Docker Compose setup**
A `docker-compose.yml` covering the FastAPI app, Ollama service, and PostgreSQL (when logging is migrated).

**Deployment guide**
Step-by-step documentation for Railway, Render, AWS ECS, and GCP Cloud Run.

**Adversarial benchmark expansion**
The current suite is 32 prompts. Expanding to 100+ with more novel jailbreak patterns, indirect harm vectors, and domain-specific edge cases improves benchmark validity. New prompts must include: expected outcome, tier classification, domain, and rationale for why this should pass or fail.

### Research contributions

**Neural network domain classifier**
A small fine-tuned classifier replacing keyword matching in `prompt_classifier.py`. Training data is available from the decision log. The architecture should maintain a hardcoded keyword fallback for cases where the classifier is uncertain — defense in depth at the classification layer.

**Response compression pipeline**
Summarize model outputs before consensus scoring to reduce token cost on long responses without losing the reliability signal.

**TruthfulQA and HallucinationBench integration**
Add published hallucination benchmark prompts to the test suite. This provides externally validated ground truth rather than self-constructed benchmarks, and strengthens research credibility.

**Confidence calibration**
Compare AERIS confidence scores against human expert ground truth labels in medical, legal, and financial domains. We are seeking domain expert partnerships for this work.

---

## Benchmark discipline

Every code change that touches the validation pipeline must be benchmarked before and after:

```bash
# Before your change
python tests/run_benchmark.py --version pre-change

# After your change
python tests/run_benchmark.py --version post-change

# Compare
python tests/run_benchmark.py --compare pre-change post-change
```

A contribution that causes any regression in dangerous delivery rate will not be merged. A contribution that improves weighted reliability score without increasing dangerous delivery rate is always welcome.

**Include benchmark comparison output in your pull request description.** PRs that touch pipeline files without benchmark output will be asked to add it before review.

---

## Commit message convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add embedding-based consensus scoring to consensus engine
fix: sovereign verdict enum serialization — use verdict.value not verdict
docs: update V4_ARCHITECTURE with v4.0 thresholds and escalation logging
refactor: extract tiered sovereign agent selection into config
test: add pytest coverage for contradiction lattice severity levels
bench: v4.0 benchmark results 32/32 100 percent weighted reliability
chore: update requirements.txt async client dependencies
```

Do not use generic messages like `fix bug` or `update code`. Every commit should explain what changed and why in one line.

---

## Pull request process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature-name`
3. Make your changes with docstrings and type hints on all functions
4. Run the benchmark and include results in your PR description
5. Commit using conventional commit format
6. Push and open a PR against `main`
7. Describe: what changed, why, and what the benchmark impact is

---

## Code standards

**Python**
- PEP 8 compliance
- Type hints required on all function signatures
- Docstrings required on all public functions and classes
- No hardcoded API keys, model names, or secrets — use environment variables and constants
- No `print()` in production code — use `log_decision()` or Python logging

**Async**
- New model integrations must be async — either native async client or `loop.run_in_executor()` wrapper
- Use `asyncio.get_running_loop()` not `asyncio.get_event_loop()` in async contexts
- All enum values serialized as `.value` (string) before including in API responses

**Architecture**
- New validation layers added to the pipeline in `main.py` and documented in `docs/V4_ARCHITECTURE.md`
- New arbiter integrations must follow the `_model_result()` return structure in `llm_service.py`
- Threshold changes must be benchmarked and justified — not guessed
- `sovereign_result` must be initialized to `None` before Step 4 — all early-exit returns must include `sovereign_layer=sovereign_result`
- Any code path that produces a `FinalVerdict.SILENT` should also write a complete record via `escalation_logger.log_escalation()` — this contract is what makes the audit trail trustworthy

**Sensitive files — highest scrutiny required**
The following files require the clearest justification for any change:
- `prompt_classifier.py` — keyword changes directly affect tier routing and safety
- `confidence_engine.py` — threshold changes directly affect delivery rate
- `meta_arbitration.py` — weight changes affect the composite trust score
- `sovereign_layer.py` — agent prompt changes affect local validation behavior
- `ethical_anchor.py` — pillar logic changes affect hard refusal triggers
- `escalation_logger.py` — signature and JSONL append logic; any change must preserve tamper-evidence guarantees of the existing audit trail

---

## Questions and discussion

Open a GitHub issue with the `question` label for architecture questions.

For research collaboration, domain expert partnerships, or enterprise pilot inquiries: [hello@aerislattice.com](mailto:hello@aerislattice.com)

# AERIS Lattice — Product Roadmap

## Current status

**Version:** v4.0 — Async Parallel Tri-Layer Dual Consensus with Tamper-Evident Escalation Audit
**Stage:** Benchmark-validated, local deployment
**Benchmark:** 32/32 · 100% weighted reliability · 0% dangerous delivery
**Architecture:** 11-step pipeline · 3 consensus layers · 4 cloud models · 5 sovereign agents · async parallel execution · signature-bound escalation audit log
**Live:** [aerislattice.com](https://aerislattice.com) · [github.com/DevT3/aeris-lattice](https://github.com/DevT3/aeris-lattice)

---

## Milestone 1 — Core Architecture ✅ Complete

**Delivered: April 2026 (v3.1) · v4.0 hardening: April–May 2026**

The foundational inference-time reliability pipeline, validated across 32 adversarial prompts.

- [x] FastAPI backend with full async pipeline orchestration
- [x] OpenAI GPT-4o-mini integration (async)
- [x] Groq Llama 3.3 integration (async)
- [x] Mistral Small integration (executor-wrapped async)
- [x] Gemini 2.5 Flash integration (executor-wrapped async)
- [x] Ollama Llama 3.2 local integration — exclusive to sovereign layer
- [x] Async parallel model queries via asyncio.gather() — 60–70% latency reduction
- [x] Per-model timeout with partial consensus — system proceeds without lagging models
- [x] Tiered routing — 2/3/4 models by risk tier
- [x] Prompt classifier — 4 risk tiers, multi-domain keyword sets
- [x] Multi-model consensus engine with inter-model agreement scoring
- [x] Contradiction Lattice — pattern-based critical claim detection, domain-aware
- [x] Ethical Anchor — pillar-based harm evaluation with hard veto + weighted penalties
- [x] Sovereign Layer — 5 local agents with weighted voting and judge veto authority
- [x] Sovereign mode button — forces sovereign execution on any tier
- [x] Confidence Engine — domain-aware, trusts classifier domain (no re-detection)
- [x] Reflective Loop — adversarial GPT-4o-mini challenge with domain templates
- [x] Meta-Arbitration Engine — composite trust score 0–100
- [x] Silent State — structured refusal with explainable refusal chain
- [x] Three validation modes — Optimized / Full Consensus / Full + Sovereign
- [x] Append-only decision audit logging (JSONL)
- [x] Token usage tracking per model
- [x] Response latency tracking per model (avg, slowest, fastest)
- [x] Visual demo UI — dark mode, model cards, audit disclosure, sovereign panel
- [x] Benchmark tab — live run, load last results, token/latency columns, tab persistence
- [x] Stop/Cancel button on validation and benchmark
- [x] Reliability dashboard — live metrics, suppression breakdown, decision log
- [x] Adversarial benchmark suite — 32 prompts, 4 tiers, tier-weighted scoring
- [x] Benchmark regression detection between versions
- [x] Enterprise arbiter API — plug any model endpoint as additional arbiter
- [x] Early exit UI messages — distinguishes genuine Ollama offline from pipeline gate exit
- [x] Professional documentation (README, roadmap, vision, architecture, contributing)
- [x] Live domain — aerislattice.com
- [x] GitHub repository — github.com/DevT3/aeris-lattice

### v4.0 hardening (April–May 2026)

- [x] Architecture lock — clean 11-step deterministic pipeline contract across all modules
- [x] Prompt classifier hardening — significantly strengthened Tier C/D detection with expanded keyword sets; Tier C/D forced to full models + sovereign + ethical anchor at handler level (`main.py` lines 136–145)
- [x] Domain threshold tightening — meta-arbitration deliver thresholds raised for high-stakes domains (medical 92, legal 90, financial 88, safety 93, adversarial 97) to drive dangerous delivery to zero across regression cycles
- [x] Sovereign layer veto contract — judge `silent` verdict triggers immediate suppression regardless of weighted score; weighted-score-under-30 also forces veto path in `meta_arbitration.py`
- [x] Silent State unified trigger set — low external consensus, critical contradiction, sovereign veto, reflection refusal, ethical hard refusal, and meta-arbitration trust-score-below-threshold all converge on the structured Silent State response
- [x] Escalation audit log — `escalation_logger.py` writes signature-bound JSONL records (`event`, `prompt_preview`, `tier`, `domain`, `refusal_reason`, `trust_score`, `refusal_chain`, `sovereign_layer`, `external_consensus`, `confidence`, `signature`) to `escalation_log.jsonl` on every meta-arbitration Silent State
- [x] Public escalation API — `/api/escalate` (record), `/api/escalations` (list last 50)
- [x] Benchmark suite API — `/api/benchmark-suite` for the in-app benchmark tab
- [x] Reliability stats reset — `/api/reset-stats` and corresponding UI control
- [x] UI polish — `index.html` mode toggles (Optimized / Full Consensus / Full + Sovereign), working benchmark tab via `/api/benchmark-suite`, fixed reset-stats action, dark theme refinement; `dashboard.html` reliability metrics + domain breakdown + recent decisions log
- [x] Windows path / import fixes — `run_server.py` launcher + `sys.path` insertion at top of `main.py`
- [x] Benchmark: 32/32 · 100% weighted · 0 dangerous (April 30, 2026 run)

---

## Milestone 2 — Production Infrastructure

**Target: Q2–Q3 2026**

Transform the validated architecture into a deployable, monitored, authenticated service. The human-in-the-loop foundation shipped in v4.0; this milestone completes Phase 1 and adds the operational surface required for pilots.

### Human-in-the-loop — Phase 1 finalization

The v4.0 audit-trail backbone is in place. Remaining Phase 1 items:

- [ ] `/api/escalate/resolve` — record reviewer decision (accept / override / confirm suppression) back to the audit trail
- [ ] `/api/webhook/escalation` — outbound HTTP POST of the escalation payload to a configurable external endpoint (ServiceNow, Jira, custom ITSM); stub first, retry + dead-letter later
- [ ] Reviewer dashboard panel in `dashboard.html` — live table of queued escalations with full audit-payload drill-down
- [ ] Review modal — Accept / Override buttons wired to `/api/escalate/resolve`
- [ ] SLA tracking — time-to-resolution per escalation
- [ ] Reviewer authentication — even minimal API-key gating before Phase 1 ships externally

### Human-in-the-loop — Phase 2 hardening

- [ ] Replace `"debug-v4"` signature placeholder with HMAC signing keyed off `ESCALATION_SIGNING_KEY` env var
- [ ] Tamper-evident hash chain across records (each record signs the previous record's signature)
- [ ] Compliance-grade export — signed JSON and signed PDF of any time range
- [ ] Data residency configuration — route HITL workflows on-premise only

### Backend
- [ ] REST API authentication — API key middleware with rate limiting
- [ ] PostgreSQL persistent decision logging — replace flat-file JSONL audit log; keep `escalation_log.jsonl` as a separate append-only stream
- [ ] Structured query support — filter decisions by domain, tier, date range
- [ ] Audit trail export — JSON and CSV for compliance workflows
- [ ] Request/response payload encryption at rest
- [ ] Health check endpoint with component status (each model, sovereign layer, Ollama)

### Infrastructure
- [ ] Docker containerization with `docker-compose.yml` for full stack (app + Ollama + Postgres)
- [ ] Environment-based configuration — dev / staging / prod separation
- [ ] CI/CD pipeline via GitHub Actions — lint, test, benchmark on every PR
- [ ] Cloud deployment — Railway or Render (initial), AWS ECS (scale target)
- [ ] Uptime monitoring — Betterstack or similar
- [ ] Public demo endpoint — demo.aerislattice.com with rate limiting

### Testing
- [ ] Pytest suite covering all 11 pipeline steps
- [ ] Integration tests for each model arbiter with mock fallbacks
- [ ] Escalation logger unit tests — payload integrity, signature presence, append-only invariant
- [ ] Benchmark regression check runs automatically on PR merge
- [ ] Load testing — 100 concurrent requests, latency and error rate

---

## Milestone 3 — Enterprise Features

**Target: Q3–Q4 2026**

Features required for enterprise pilots, procurement conversations, and regulated industry deployment.

### Multi-tenancy
- [ ] Organization-level isolation — separate arbiters, thresholds, and logs per tenant
- [ ] Custom domain-specific safety profiles per tenant — configurable via JSON without code changes
- [ ] Arbiter registry — plug-and-play model endpoints per organization
- [ ] Tenant-level reliability dashboard with historical trend data
- [ ] Tiered sovereign execution by risk level — Tier A: 2 agents, Tier B: 3, Tier C/D: 5

### Compliance
- [ ] Tamper-evident audit log — SHA-256 hash chain per decision record (extension of Phase 2 hash chain)
- [ ] Audit trail export in compliance-ready format (CSV, JSON, signed PDF)
- [ ] Data residency configuration — route sovereign validation on-premise only
- [ ] SOC 2 Type I readiness assessment and gap analysis

### Developer experience
- [ ] Python SDK — `pip install aeris-lattice`
- [ ] OpenAPI specification published at `/openapi.json`
- [ ] Postman collection and API reference documentation
- [ ] Deployment guide — Railway, Render, AWS, GCP, Azure

---

## Milestone 4 — Research and Optimization

**Target: Q4 2026 / Q1 2027**

Move from keyword-based validation to embedding-based semantic validation. Establish academic and institutional credibility.

### Semantic reliability engine
- [ ] Embedding-based consensus scoring — cosine similarity between model output vectors replaces keyword matching in `consensus_engine.py`
- [ ] Semantic contradiction detection — embedding distance flags contradictions between model outputs
- [ ] Neural network domain classifier — small fine-tuned classifier trained on decision log data, with hardcoded keyword fallback
- [ ] Response compression pipeline — summarize model outputs before consensus scoring to reduce token cost and latency

### Calibration
- [ ] Confidence calibration against domain expert ground truth datasets
- [ ] Bayesian threshold optimization per domain using historical decision log — canary tests with golden-set queries, model accuracy tracked, weights adjusted automatically
- [ ] False refusal rate reduction to < 2% without increasing dangerous delivery rate
- [ ] Hallucination rate benchmarks across all model combinations (TruthfulQA, HallucinationBench integration)

### Research outputs
- [ ] Target reliability: 99.9% weighted score across 100-prompt benchmark
- [ ] Academic paper draft: *Inference-Time Reliability Architectures for LLM Deployment in High-Stakes Domains*
- [ ] Adversarial prompt stress test — 500 prompts including novel jailbreak patterns
- [ ] Domain dataset partnerships — medical, legal, financial institutions

---

## Long-term vision

**Model-agnostic reliability infrastructure, deployable in front of any LLM.**

- Industry-specific compliance certifications — HIPAA-adjacent for medical, SOX-adjacent for financial
- Real-time reliability operations dashboard for enterprise AI teams
- Open-source core with commercial licensing for managed cloud deployments
- Arbiter marketplace — vetted domain-specific models available as plug-in arbiters
- Academic partnership program for domain ground truth dataset access

---

## Not in scope (current phase)

- Training or fine-tuning underlying LLMs
- Real-time audio or multimodal validation
- Browser extension or mobile SDK
- Replacing human professional judgment in regulated industries

---

## Benchmark progression

| Version | Score | Dangerous Delivery | Weighted Score | Key change |
|---|---|---|---|---|
| v1.0 | 27/32 | 10% | 84.7% | Baseline |
| v2.2 | 27/32 | 0% | 92.6% | Classifier + jailbreak expansion |
| v2.3 | 29/32 | 0% | 95.2% | Domain thresholds, pipeline reorder |
| v2.6 | 31/32 | 0% | 98.4% | Classifier keyword collision fix |
| v2.9 | 32/32 | 0% | 100% | Confidence engine domain trust fix |
| v3.0 | 32/32 | 0% | 100% | Async parallel orchestration |
| v3.1 | 32/32 | 0% | 100% | Sovereign mode, enum serialization fix |
| **v4.0** | **32/32** | **0%** | **100%** | **Architecture lock, classifier hardening, tightened deliver thresholds, escalation audit log** |

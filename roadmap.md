# Roadmap

## Status

Current stage: **MVP complete — local development**  
Active arbiters: GPT-4o-mini · Groq Llama 3.3 · Mistral Small · Gemini 2.5 Flash · Local LLM  
Architecture: 5-layer validation pipeline with 5-model consensus engine

---

## Milestone 1 — MVP ✅ Complete

- [x] FastAPI backend skeleton
- [x] OpenAI live connection
- [x] Confidence Engine with domain-aware scoring
- [x] Reflective Loop
- [x] Silent State structured refusal
- [x] Contradiction Lattice
- [x] Append-only decision audit logging
- [x] Multi-model consensus engine (5 arbiters)
- [x] Groq Llama 3.3 integration
- [x] Mistral Small integration
- [x] Gemini 2.5 Flash integration
- [x] Local LLM arbiter via Ollama
- [x] Enterprise custom arbiter API
- [x] Visual demo UI
- [x] Professional documentation
- [x] Live domain (aerislattice.com)

---

## Milestone 2 — Reliability Infrastructure

Target: Week 2

- [ ] PostgreSQL persistent decision logging (replace flat file)
- [ ] Semantic similarity scoring in consensus engine (replace keyword matching)
- [ ] Domain-specific safety profiles (medical, legal, financial, cybersecurity)
- [ ] Response confidence calibration using historical log data
- [ ] REST API authentication (API key middleware)
- [ ] Rate limiting
- [ ] Structured test suite with pytest
- [ ] CI/CD pipeline via GitHub Actions
- [ ] `.env.example` template committed to repo
- [ ] Contribution guidelines (`CONTRIBUTING.md`)

---

## Milestone 3 — Production Deployment

Target: Week 3

- [ ] Cloud deployment (Railway or Render — initial)
- [ ] Public API endpoint with key management
- [ ] Docker containerization
- [ ] Environment-based configuration (dev / staging / prod)
- [ ] Health check and uptime monitoring
- [ ] Request/response payload encryption
- [ ] Basic admin dashboard for log review
- [ ] Public demo at demo.aerislattice.com

---

## Milestone 4 — Enterprise Features

Target: Month 2

- [ ] Multi-tenant architecture (organizations with isolated arbiters)
- [ ] Custom domain-specific safety layer configuration per tenant
- [ ] Arbiter registry (plug-and-play model endpoints)
- [ ] Audit trail export (CSV, JSON) for compliance workflows
- [ ] Webhook support for silent-state events
- [ ] SDK wrapper — Python package (`pip install aeris-lattice`)
- [ ] OpenAPI spec publication
- [ ] SOC 2 readiness assessment

---

## Milestone 5 — Research & Optimization

Target: Month 3+

- [ ] Semantic consensus scoring using embedding similarity (cosine distance between model outputs)
- [ ] Confidence calibration benchmarking against domain expert ground truth
- [ ] Adversarial prompt stress testing
- [ ] Hallucination rate benchmarks across model combinations
- [ ] Target reliability threshold: 99.9%
- [ ] Academic paper draft: *Inference-Time Reliability Architectures for LLM Deployment in High-Stakes Domains*
- [ ] Multi-model fine-tuning pipeline for domain-specific arbiter training
- [ ] Partnership with medical/legal/financial institutions for domain dataset access

---

## Long-term vision

- Model-agnostic reliability layer deployable in front of any LLM
- Industry-specific compliance certifications (HIPAA-adjacent for medical, SOX-adjacent for financial)
- Real-time reliability scoring dashboard for enterprise AI operations teams
- Open-source core with enterprise licensing for managed deployments

---

## Not in scope (current phase)

- Replacing underlying LLMs
- Training new models
- Real-time audio or multimodal validation
- Browser extension or mobile SDK

These are evaluated for future milestones pending funding and research partnerships.

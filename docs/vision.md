# Vision

## Overview

AERIS Lattice is an inference-time reliability layer for large language models.

It does not improve the underlying model. It governs its output before it reaches the user.

The distinction matters. AERIS does not attempt to make LLMs smarter. It attempts to make LLM-powered systems safer by introducing a structured decision layer between model output and human action.

---

## Problem statement

LLM deployment in high-stakes domains proceeds without any formal validation layer between model output and human action.

The failure modes are well-documented:

- Models assert incorrect medical dosages with high apparent confidence
- Models provide legal guidance that contradicts applicable law in the user's jurisdiction
- Models present financially dangerous strategies as factual and low-risk
- Models hallucinate citations, statistics, clinical studies, and expert consensus
- Models answer questions they should refuse, because refusal was not optimized during training

Current mitigations operate at training time:

| Mitigation | When applied | Limitation |
|---|---|---|
| Prompt engineering | Inference | Inconsistent, prompt-dependent |
| Fine-tuning | Training | Domain-specific, expensive |
| RLHF | Training | Reduces rate, does not eliminate failure |
| RAG | Inference | Addresses knowledge gaps, not confidence calibration |

None of these provide a structured, model-agnostic validation layer at inference time.

**The gap:** there is no production-grade middleware that intercepts LLM output and applies multi-source reliability validation before delivery.

A system that hallucinates 1% of the time will cause real harm at scale. The acceptable threshold in high-stakes domains is not 99%. It approaches 99.999%.

---

## Hypothesis

A multi-model consensus architecture — where independent models are queried simultaneously and their agreement is measured before any response is delivered — produces a measurable reduction in unsafe output reaching the user, without requiring changes to the underlying models.

Combined with domain-aware confidence scoring and structured silent states, this approach provides a deployable reliability layer that is model-agnostic and domain-configurable.

---

## Architecture decisions

### Why multi-model consensus

No single model is reliably correct across all domains and edge cases. Five independent models queried simultaneously provide a disagreement signal that is not available from any single model.

High inter-model disagreement correlates strongly with uncertain, contested, or domain-specific ground where errors are most likely. This signal is available at inference time with no training required and no model modification.

The consensus engine is designed to be extended. Organizations can add domain-specific fine-tuned models as additional arbiters, increasing the precision of the consensus signal in their target domain.

### Why a silent state

Partial responses and hedged answers create false confidence. A user who receives a qualified answer may still act on it. A structured refusal — explicit, logged, and consistent — leaves no ambiguity.

The silent state is not a failure mode. It is a deliberate design output. Teaching a system when to refuse is as important as teaching it how to respond. Current LLM deployment practice optimizes almost exclusively for the latter.

### Why domain-aware confidence scoring

General linguistic uncertainty detection — hedging words, vague quantifiers — is insufficient for high-stakes domains. A response that sounds confident but touches medical, legal, or financial content requires a different reliability threshold than a response about geography or history.

Domain classification runs at inference time against a configurable keyword index and adjusts the confidence threshold accordingly. This allows domain-specific safety profiles to be configured per deployment without modifying the underlying pipeline.

### Why append-only decision logging

Every validation decision — delivered or suppressed — is logged with the full prompt, response excerpt, confidence score, and status. This creates an audit trail for:

- Post-hoc reliability analysis
- Threshold calibration using real-world data
- Regulatory compliance documentation
- Incident investigation

Logging is append-only. Records are never modified or deleted. This is a deliberate design choice for auditability.

### Why an enterprise arbiter API

Different organizations have different reliability requirements and different domain knowledge. A medical institution may operate a fine-tuned clinical LLM trained on their patient population. A legal firm may have a compliance model trained on their jurisdiction's case law.

AERIS allows any model exposed via a standard API endpoint to participate as a voting arbiter in the consensus engine. The organization's domain expertise becomes part of the reliability signal, without requiring access to or modification of the AERIS core.

---

## Validation pipeline

```
Prompt received
    ↓
Query all arbiters in parallel
    — GPT-4o-mini (OpenAI)
    — Llama 3.3 70B (Groq)
    — Mistral Small (Mistral AI)
    — Gemini 2.5 Flash (Google)
    — Llama 3.2 (Local via Ollama)
    — [Optional enterprise arbiter]
    ↓
Consensus Engine
    — Count valid responses (no API errors)
    — Detect uncertainty markers across responses
    — Score = (valid / total) × 100
    — Apply penalty if ≥ 2 models express uncertainty
    — Threshold: 60. Below → silent state
    ↓
Contradiction Lattice
    — Scan primary response for absolute certainty markers
    — Flagged terms: always, never, guaranteed, certain, 100%, impossible
    — Any match → silent state
    ↓
Confidence Engine
    — Scan for uncertainty language in response
    — Classify prompt domain: medical, legal, financial
    — Domain match → confidence capped at 55
    — Threshold: 70. Below → reflective loop
    ↓
Reflective Loop
    — Apply reflective prefix to response
    — Re-score with confidence engine
    — Still below threshold → silent state
    ↓
Deliver or suppress
    — Log decision with full metadata
    — Return structured response or structured refusal
```

---

## Success criteria

The MVP demonstrates:

1. High-risk prompts (medical, legal, financial) consistently trigger silent state or confidence penalty
2. Safe factual prompts pass through with confidence ≥ 90
3. All decisions are logged with full traceability
4. The system is model-agnostic — any LLM endpoint can be substituted without modifying the validation pipeline
5. Enterprise arbiters can be added dynamically per request

---

## Target reliability threshold

Current MVP: demonstrable improvement over single-model deployment  
Near-term target: 99.9% safe output rate in high-risk domains  
Long-term target: 99.999% — suitable for clinical and financial deployment

Reaching 99.999% requires:
- Semantic consensus scoring using embedding similarity (not keyword matching)
- Confidence calibration against domain expert ground truth datasets
- Adversarial prompt stress testing
- Domain-specific arbiter fine-tuning partnerships

---

## Non-goals

- AERIS Lattice does not improve underlying model quality
- AERIS Lattice does not provide its own answers — it validates model output only
- AERIS Lattice does not guarantee zero unsafe output in its current state
- AERIS Lattice is not a content moderation system
- AERIS Lattice does not replace licensed professionals in any domain

---

## Target deployment contexts

| Domain | Risk | AERIS value |
|---|---|---|
| Medical information platforms | Patient safety | Silent state on clinical uncertainty |
| Financial advisory tools | Regulatory exposure | Contradiction detection on guarantee claims |
| Legal research platforms | Liability | Domain confidence penalty on legal content |
| Enterprise AI assistants | Operational risk | Audit trail, configurable thresholds |
| Autonomous agent pipelines | Compounding errors | Multi-model consensus before action execution |

---

## Status

MVP complete. 5-model consensus engine operational. Core validation pipeline confirmed working across medical, legal, and financial domain tests.

See [roadmap.md](../roadmap.md) for next milestones.

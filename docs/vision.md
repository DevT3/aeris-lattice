# Vision

## Overview

AERIS Lattice is an inference-time reliability layer for large language models. It sits between the user and the model, validating every response before delivery.

It does not improve the model. It governs its output.

---

## Problem statement

LLM deployment in high-stakes domains — medicine, finance, law, autonomous systems — proceeds without any formal validation layer between model output and human action.

The consequences are well-documented:

- Models assert incorrect medical dosages with high apparent confidence
- Models provide legal guidance that contradicts applicable law
- Models present financially dangerous advice as factual
- Models hallucinate citations, statistics, and expert consensus

Current mitigations — prompt engineering, fine-tuning, RLHF — operate at training time. They reduce failure rates but do not eliminate them. A model that hallucinates 1% of the time will still cause harm at scale.

**The gap**: there is no production-grade, model-agnostic validation layer that intercepts unreliable output at inference time.

---

## Hypothesis

A multi-model consensus architecture — where independent models are queried simultaneously and their agreement is measured before delivery — will produce a measurable reduction in unsafe output reaching the user, without requiring changes to the underlying models.

---

## Architecture decisions

### Why multi-model consensus

No single model is reliably correct. Three independent models queried simultaneously provide a disagreement signal. High disagreement correlates strongly with uncertain or contested ground. This signal is available at inference time with no training required.

### Why a silent state

Partial responses and hedged answers create false confidence. A structured refusal — explicit, logged, and traceable — is safer than a qualified answer the user may act on. The silent state is not a failure mode. It is a deliberate design output.

### Why domain-aware confidence scoring

General linguistic uncertainty detection (hedging words, vague quantifiers) is insufficient for high-stakes domains. A response that sounds confident but touches medical, legal, or financial content requires a different threshold. Domain classification runs at inference time against a keyword index and adjusts the confidence threshold accordingly.

### Why append-only decision logging

Every validation decision — delivered or suppressed — is logged with the full prompt, response, confidence score, and status. This creates an audit trail for post-hoc analysis, threshold tuning, and regulatory compliance groundwork.

---

## Validation pipeline

```
Prompt received
    ↓
Query GPT-4o-mini, Claude Haiku, Gemini Flash in parallel
    ↓
Consensus Engine
    — score = (valid responses / total) × 100
    — penalty applied if ≥2 models express uncertainty
    — threshold: 60. Below → silent state
    ↓
Contradiction Lattice
    — scan for absolute certainty markers: always, never, guaranteed, certain, impossible
    — any match → silent state
    ↓
Confidence Engine
    — scan for uncertain language markers
    — classify prompt domain: medical, legal, financial
    — domain match → score capped at 55
    — threshold: 70. Below → reflective loop
    ↓
Reflective Loop
    — prepend reflective prefix to response
    — re-score with confidence engine
    — still below 70 → silent state
    ↓
Deliver or suppress
```

---

## Success criteria

A validated MVP demonstrates:

1. High-risk prompts (medical, legal, financial) consistently trigger silent state or confidence penalty
2. Safe, factual prompts pass through with confidence ≥ 90
3. All decisions are logged with full traceability
4. The system is model-agnostic — any LLM can be substituted without changes to the validation layer

---

## Non-goals

- AERIS Lattice does not improve underlying model quality
- AERIS Lattice does not provide its own answers — it validates model output only
- AERIS Lattice does not guarantee zero unsafe output — it reduces the probability
- AERIS Lattice is not a content moderation system

---

## Target deployment contexts

- Medical information platforms requiring response reliability guarantees
- Financial advisory tools with regulatory exposure
- Legal research tools where incorrect output creates liability
- Enterprise AI deployments requiring audit trails
- Any production system where "I don't know" is safer than a confident wrong answer

---

## Status

MVP complete. Core validation pipeline operational across three models.
See [`roadmap.md`](../roadmap.md) for next milestones.

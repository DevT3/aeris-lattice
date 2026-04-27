# Vision

## What AERIS Lattice is

AERIS Lattice is inference-time reliability middleware for large language models.

It does not improve the underlying model. It governs its output before it reaches the user.

The distinction matters. AERIS does not attempt to make LLMs smarter. It makes LLM-powered systems safer by introducing a structured, multi-layer validation architecture between model output and human action. Any model. Any domain. Any deployment.

---

## The problem

LLM deployment in high-stakes domains proceeds without any formal validation layer between model output and human action.

The failure modes are well-documented and occurring now:

- Models assert incorrect medical dosages with high apparent confidence
- Models provide legal guidance that contradicts applicable law in the user's jurisdiction
- Models present financially dangerous strategies as factual, low-risk, and guaranteed
- Models hallucinate citations, statistics, clinical studies, and expert consensus
- Models answer questions they should refuse — because refusal was not optimized during training

Current mitigations all operate at training time or prompt-construction time:

| Mitigation | When applied | Fundamental limitation |
|---|---|---|
| Prompt engineering | Per request | Inconsistent, adversarially fragile |
| Fine-tuning | Training | Domain-specific, expensive, cannot generalize |
| RLHF | Training | Reduces rate — does not eliminate failure |
| RAG | Per request | Addresses knowledge gaps — not confidence calibration |
| Guardrail libraries | Per request | Rule-based, easily bypassed, no consensus signal |

None of these provide a structured, model-agnostic validation layer at inference time.

A system that produces unsafe output 1% of the time causes real harm at scale. At 10,000 daily queries, that is 100 dangerous responses per day. In a medical information platform, those are 100 patients per day who may act on incorrect clinical guidance.

**The gap:** there is no production-grade middleware that intercepts LLM output, applies multi-source reliability validation, and makes a structured delivery decision before the response reaches the user.

---

## The hypothesis

A multi-model dual-consensus architecture — where independent models are queried simultaneously, sovereign local agents evaluate the primary response, and their agreement is measured and weighted before any response is delivered — produces a measurable, reproducible reduction in unsafe output reaching the user, without requiring modification to the underlying models.

Combined with domain-aware confidence scoring, adversarial challenge evaluation, and structured silent states, this approach provides a deployable reliability layer that is model-agnostic, domain-configurable, and auditable.

**Validated:** AERIS v2.9 achieves 100% weighted reliability and 0% dangerous delivery rate across a 32-prompt adversarial benchmark spanning 4 risk tiers including adversarial jailbreaks, false authority injection, social engineering, and high-stakes medical, legal, and financial prompts.

---

## Architecture decisions

### Why dual consensus — external and sovereign

No single model is reliably correct across all domains and edge cases. Four independent cloud models queried simultaneously provide a disagreement signal unavailable from any individual model.

The sovereign layer — five local agents running on Ollama with independent roles and weighted votes — provides a second, private validation pass that cloud consensus cannot. The Silent State Judge holds veto authority: a single veto immediately suppresses the response regardless of all other scores.

This dual structure separates concerns: cloud models provide breadth and diversity of perspective; local agents provide depth, privacy, and structured adversarial challenge.

### Why a silent state — not a fallback answer

Partial responses and hedged answers create false confidence. A user who receives a qualified answer may still act on it. A structured refusal — explicit, logged, consistent, and auditable — leaves no ambiguity.

The silent state is not a failure mode. It is a deliberate design output. Teaching a system when to refuse is as important as teaching it how to respond. Current LLM deployment practice optimizes almost exclusively for the latter.

The enterprise argument is economic as well as ethical: the liability cost of a dangerous delivery in a regulated domain far exceeds the operational cost of a false refusal.

### Why tiered routing — not all models on every request

Querying 4 cloud models on every request is wasteful and unnecessary. "What is the capital of France?" does not require the same validation depth as "Can I stop taking my antidepressants cold turkey?"

Tiered routing classifies each prompt and routes it to the minimum model set required for reliable validation at that risk level:

- Tier A (safe): 2 models, fast path
- Tier B (medium): 3 models
- Tier C/D (high risk and adversarial): 4 cloud models + sovereign layer

For typical production traffic where the majority of requests are safe, this reduces token cost by approximately 50% with zero reliability impact.

### Why domain-aware confidence thresholds

General linguistic uncertainty detection is insufficient for high-stakes content. A response that sounds confident but touches medical, legal, or financial content requires a fundamentally different reliability bar than a response about geography or history.

Domain classification runs at inference time against a structured keyword and pattern index, and adjusts confidence thresholds, model routing, ethical anchor activation, and sovereign layer invocation accordingly. This allows domain-specific safety profiles to be configured per deployment without modifying the validation pipeline.

### Why an append-only audit log

Every validation decision — delivered and suppressed — is logged with the full prompt, response excerpt, confidence score, domain classification, and outcome. This creates a durable audit trail for:

- Post-hoc reliability analysis and threshold calibration
- Regulatory compliance documentation
- Incident investigation
- Real-world benchmark data collection

Records are never modified or deleted. Append-only is not a convenience choice — it is a deliberate architectural decision for auditability.

### Why an enterprise arbiter API

Different organizations have different reliability requirements and different domain knowledge. A hospital system operating a clinical LLM fine-tuned on their patient population has knowledge AERIS's general arbiters do not. A legal firm with a compliance model trained on their jurisdiction's case law can encode that expertise as a voting arbiter.

AERIS allows any model exposed via a standard API endpoint to participate as a weighted arbiter in the consensus engine. The organization's domain expertise becomes part of the reliability signal — without requiring access to or modification of the AERIS core.

---

## The design philosophy

Most AI systems are optimized to answer.

AERIS Lattice is optimized to know when not to.

This is the inversion. Silence is a valid safety mechanism. The cost of a false refusal — a user who must consult a professional instead of acting on an LLM response — is acceptable and often correct. The cost of a dangerous delivery — a user who acts on incorrect clinical or legal guidance — is not.

The acceptable threshold for dangerous delivery in high-stakes domains approaches zero. AERIS v2.9 achieves zero.

---

## Target deployment contexts

| Domain | Risk category | AERIS value |
|---|---|---|
| Medical information platforms | Patient safety | Silent state on clinical uncertainty, drug interaction flags |
| Financial advisory tools | Regulatory exposure | Contradiction detection on guarantee claims |
| Legal research platforms | Liability | Domain confidence penalty, professional escalation |
| Enterprise AI assistants | Operational risk | Audit trail, configurable thresholds, sovereign validation |
| Autonomous agent pipelines | Compounding errors | Multi-model consensus before action execution |
| Government information services | Public trust | Silent state on policy and legal content |
| Clinical decision support | Life-critical | Maximum threshold configuration, full sovereign validation |

---

## Reliability targets

| Threshold | Current (v2.9) | Near-term | Long-term |
|---|---|---|---|
| Dangerous delivery rate | 0% | < 0.1% at scale | < 0.01% |
| Weighted reliability score | 100% (32/32) | 99%+ at 100 prompts | 99.9%+ |
| False refusal rate | 0% | < 5% | < 2% |

Reaching 99.9%+ at scale requires semantic consensus scoring using embedding similarity, confidence calibration against domain expert ground truth, and domain-specific arbiter fine-tuning partnerships with institutional collaborators.

---

## Non-goals

AERIS Lattice explicitly does not:

- Improve the quality or accuracy of underlying LLMs
- Provide its own answers — it validates model output only
- Replace licensed medical, legal, or financial professionals
- Guarantee zero unsafe output in its current state
- Serve as a content moderation system for non-factual content

These are not limitations to be fixed. They define the scope of the problem AERIS is designed to solve.

---

## Status

v2.9 complete. 32/32 benchmark score. 0% dangerous delivery. 100% weighted reliability. Dual consensus architecture operational with 4 cloud models and 5 sovereign agents.

See [roadmap.md](../roadmap.md) for next milestones.

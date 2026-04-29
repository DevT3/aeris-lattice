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

A tri-layer dual-consensus architecture — where independent cloud models are queried in parallel, local sovereign agents evaluate the primary response, and their combined agreement is measured and weighted before any response is delivered — produces a measurable, reproducible reduction in unsafe output reaching the user, without requiring modification to the underlying models.

Combined with domain-aware confidence scoring, adversarial challenge evaluation, and structured silent states with human escalation paths, this approach provides a deployable reliability layer that is model-agnostic, domain-configurable, and auditable.

**Validated:** AERIS v3.1 achieves 100% weighted reliability and 0% dangerous delivery rate across a 32-prompt adversarial benchmark spanning 4 risk tiers including adversarial jailbreaks, false authority injection, social engineering, and high-stakes medical, legal, and financial prompts.

---

## Architecture decisions

### Why async parallel model queries

Sequential model calls create a latency floor equal to the sum of all model response times. For a Tier C/D prompt with 4 models averaging 2.5 seconds each, sequential execution takes 10+ seconds. Parallel execution via asyncio.gather() reduces wall-clock time to the latency of the slowest single model — approximately 3-4 seconds. This is not a convenience optimization. It is the difference between a usable system and an unusable one in production.

Each model has an individual 12-second timeout. If a model exceeds it, the system excludes it from consensus and proceeds with partial results rather than waiting indefinitely. This makes AERIS resilient to individual API degradation.

### Why dual consensus — external and sovereign

No single model is reliably correct across all domains and edge cases. Four independent cloud models queried simultaneously provide a disagreement signal unavailable from any individual model.

The sovereign layer — five local agents running on Ollama with independent roles and weighted votes — provides a second, private validation pass that cloud consensus cannot. The Silent State Judge holds veto authority: a single veto immediately suppresses the response regardless of all other scores.

This dual structure separates concerns: cloud models provide breadth and diversity of perspective; local agents provide depth, privacy, and structured adversarial challenge. For enterprise deployments requiring data sovereignty, the sovereign layer runs entirely on-premise with no data leaving the machine.

### Why a silent state — not a fallback answer

Partial responses and hedged answers create false confidence. A user who receives a qualified answer may still act on it. A structured refusal — explicit, logged, consistent, and auditable — leaves no ambiguity.

The silent state is not a failure mode. It is a deliberate design output. Teaching a system when to refuse is as important as teaching it how to respond.

The silent state also serves as the trigger for human-in-the-loop escalation. When AERIS suppresses a response, it does not discard the request — it surfaces it to a human reviewer with full audit context. This is the key enterprise value proposition: AERIS does not replace human judgment in high-stakes domains. It identifies the cases that require it.

### Why tiered routing

Querying 4 cloud models on every request wastes money and time. "What is the capital of France?" does not require the same validation depth as "Can I stop taking my antidepressants cold turkey?" Tiered routing classifies each prompt at intake and routes it to the minimum model set required for reliable validation at that risk level. For typical production traffic where the majority of requests are safe, this reduces token cost by approximately 40% with zero reliability impact.

### Why three validation modes

Different contexts require different validation depth:

**Optimized** is the default for production. Cost and latency efficient, safe for general use.

**Full Consensus** queries all 4 cloud models regardless of tier. For situations where maximum external validation is required without sovereign layer latency.

**Full + Sovereign** forces all 4 cloud models plus sovereign agent execution on any tier, bypassing early exits from contradiction detection and reflection. For audit, compliance review, investor demos, and any context where the complete validation chain must be visible and documented.

### Why domain-aware confidence thresholds

General linguistic uncertainty detection is insufficient for high-stakes content. A response that sounds confident but touches medical, legal, or financial content requires a fundamentally different reliability bar than a response about geography or history.

The confidence engine trusts the domain assigned by the prompt classifier. It does not re-detect domain from response text — this was a critical architectural fix that prevented general educational responses about financial topics from being mis-scored as high-risk financial advice.

### Why an append-only audit log

Every validation decision — delivered and suppressed — is logged with the full prompt, response excerpt, confidence score, domain classification, and outcome. Records are never modified or deleted. This is not a convenience choice — it is a deliberate architectural decision for auditability, regulatory compliance, and threshold calibration using real-world data.

### Why the sovereign layer runs synchronously

Ollama is single-threaded. Parallel calls to it from the same process queue internally anyway. More importantly, keeping sovereign agents sequential preserves the ability to inject prior agent verdicts into later agents' context — specifically the Silent State Judge, which sees all prior agent verdicts before making its decision. Parallelizing sovereign would break this inter-agent information flow and eliminate the judge's ability to weigh evidence from earlier agents. The sequential constraint is a feature, not a limitation.

---

## The philosophy

Most AI systems are optimized to answer.

AERIS Lattice is optimized to know when not to.

This is the inversion. Silence is a valid safety mechanism. The cost of a false refusal — a user who must consult a professional instead of acting on an LLM response — is acceptable and often correct. The cost of a dangerous delivery — a user who acts on incorrect clinical or legal guidance — is not.

The acceptable threshold for dangerous delivery in high-stakes domains approaches zero. AERIS v3.1 achieves zero.

---

## Target deployment contexts

| Domain | Risk category | AERIS value |
|---|---|---|
| Medical information platforms | Patient safety | Silent state on clinical uncertainty, drug interaction flags, human escalation |
| Financial advisory tools | Regulatory exposure | Contradiction detection on guarantee claims, irreversibility flags |
| Legal research platforms | Liability | Domain confidence penalty, professional escalation, jurisdiction awareness |
| Enterprise AI assistants | Operational risk | Audit trail, configurable thresholds, sovereign validation |
| Autonomous agent pipelines | Compounding errors | Multi-model consensus before action execution |
| Government information services | Public trust | Silent state on policy and legal content |
| Clinical decision support | Life-critical | Maximum threshold configuration, full sovereign validation, human-in-the-loop |

---

## Reliability targets

| Threshold | Current (v3.1) | Near-term | Long-term |
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

v3.1 complete. 32/32 benchmark score. 0% dangerous delivery. 100% weighted reliability. Async parallel orchestration active. Three validation modes shipped. Sovereign mode forces full pipeline on any tier.

See [roadmap.md](../roadmap.md) for next milestones.

"""
AERIS Lattice v3.1 — Sovereign Consensus Layer
Layer 2 of the Dual Consensus System.

These agents run locally using Ollama.
Each agent has a structured role, not a personality.
They vote independently and their votes are weighted by role authority.

Agents:
    SkepticAgent          — challenges assumptions, flags overconfidence
    ComplianceGuardian    — checks regulatory and professional boundary violations
    AdversarialChallenger — attempts to break the response, finds edge case failures
    PrecisionAuditor      — checks factual claims, flags unverifiable assertions
    SilentStateJudge      — has veto authority for final delivery decision

The SilentStateJudge has veto authority.
If the Judge votes for Silent State, the response is suppressed regardless
of what the other agents or external models voted.

Usage: Only invoked on Tier C and Tier D prompts.
"""

import json
import requests
from dataclasses import dataclass
from enum import Enum

OLLAMA_BASE = "http://localhost:11434/api/generate"
LOCAL_MODEL = "llama3.2:latest"
TIMEOUT = 45


class AgentVerdict(str, Enum):
    DELIVER = "deliver"
    REFLECT = "reflect"
    SILENT = "silent"


@dataclass
class AgentResult:
    agent: str
    verdict: AgentVerdict
    confidence: int        # 0–100
    reasoning: str
    weight: float          # Voting weight in final tally


def _query_agent(system_role: str, evaluation_prompt: str) -> dict:
    """Query local Ollama model with a structured agent role."""
    full_prompt = f"""{system_role}

Respond ONLY with a valid JSON object. No explanation, no markdown, no extra text.
The JSON must have exactly these three fields:
{{"verdict": "deliver", "confidence": 80, "reasoning": "one sentence here"}}

verdict must be exactly one of: deliver, reflect, silent
confidence must be an integer 0-100

EVALUATE THIS:
{evaluation_prompt}"""

    try:
        response = requests.post(
            OLLAMA_BASE,
            json={
                "model": LOCAL_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 100
                }
            },
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            raise ValueError(f"Ollama returned status {response.status_code}")

        raw = response.json().get("response", "").strip()

        # Find JSON object in response
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON found in: {raw[:100]}")

        data = json.loads(raw[start:end])

        verdict = str(data.get("verdict", "reflect")).lower().strip()
        if verdict not in ("deliver", "reflect", "silent"):
            verdict = "reflect"

        return {
            "verdict":    verdict,
            "confidence": max(0, min(100, int(data.get("confidence", 50)))),
            "reasoning":  str(data.get("reasoning", "No reasoning provided"))[:200]
        }

    except requests.exceptions.Timeout:
        return {
            "verdict":    "reflect",
            "confidence": 30,
            "reasoning":  "Agent timeout — defaulting to reflect for safety"
        }
    except Exception as e:
        return {
            "verdict":    "reflect",
            "confidence": 20,
            "reasoning":  f"Agent unavailable: {str(e)[:80]}"
        }


# ── Agent definitions ──────────────────────────────────────────────────────────

def run_skeptic_agent(prompt: str, response: str) -> AgentResult:
    role = """You are the Skeptic Agent in a reliability validation system.
Your role: Challenge assumptions. Identify overconfident claims.
Flag any response that asserts facts without sufficient basis.
If the response sounds more certain than the evidence warrants, vote to reflect or suppress it.
You are suspicious by design. Your job is to catch false confidence."""

    evaluation = f"USER PROMPT: {prompt}\n\nMODEL RESPONSE: {response}"
    result = _query_agent(role, evaluation)

    return AgentResult(
        agent="skeptic",
        verdict=AgentVerdict(result["verdict"]),
        confidence=result["confidence"],
        reasoning=result["reasoning"],
        weight=1.0
    )


def run_compliance_guardian(prompt: str, response: str) -> AgentResult:
    role = """You are the Compliance Guardian in a reliability validation system.
Your role: Identify responses that cross professional, regulatory, or legal boundaries.
Flag any response that provides medical, legal, or financial advice that should require
a licensed professional. Also flag responses that could expose the operator to liability.
If the response substitutes for professional judgment, vote to suppress it."""

    evaluation = f"USER PROMPT: {prompt}\n\nMODEL RESPONSE: {response}"
    result = _query_agent(role, evaluation)

    return AgentResult(
        agent="compliance_guardian",
        verdict=AgentVerdict(result["verdict"]),
        confidence=result["confidence"],
        reasoning=result["reasoning"],
        weight=1.5    # Higher weight — compliance failures are critical
    )


def run_adversarial_challenger(prompt: str, response: str) -> AgentResult:
    role = """You are the Adversarial Challenger in a reliability validation system.
Your role: Try to find ways this response could cause harm if acted upon.
Consider edge cases, misinterpretations, and unintended consequences.
Consider whether a vulnerable person, a non-expert, or someone in crisis could
misuse this response. If you find a realistic harm path, vote to reflect or suppress."""

    evaluation = f"USER PROMPT: {prompt}\n\nMODEL RESPONSE: {response}"
    result = _query_agent(role, evaluation)

    return AgentResult(
        agent="adversarial_challenger",
        verdict=AgentVerdict(result["verdict"]),
        confidence=result["confidence"],
        reasoning=result["reasoning"],
        weight=1.2
    )


def run_precision_auditor(prompt: str, response: str) -> AgentResult:
    role = """You are the Precision Auditor in a reliability validation system.
Your role: Check whether factual claims in the response are verifiable and accurate.
Flag responses that contain statistics without sources, specific numbers that
seem invented, or assertions presented as fact that are actually contested.
If you cannot verify core claims, vote to reflect."""

    evaluation = f"USER PROMPT: {prompt}\n\nMODEL RESPONSE: {response}"
    result = _query_agent(role, evaluation)

    return AgentResult(
        agent="precision_auditor",
        verdict=AgentVerdict(result["verdict"]),
        confidence=result["confidence"],
        reasoning=result["reasoning"],
        weight=1.0
    )


def run_silent_state_judge(
    prompt: str,
    response: str,
    prior_agent_results: list[AgentResult]
) -> AgentResult:
    """
    The Silent State Judge sees all prior agent verdicts before making its decision.
    It has veto authority — a silent verdict from the Judge overrides everything.
    """
    agent_summary = "\n".join([
        f"- {r.agent}: {r.verdict} (confidence {r.confidence}) — {r.reasoning}"
        for r in prior_agent_results
    ])

    role = f"""You are the Silent State Judge in a reliability validation system.
You have VETO AUTHORITY. Your silent verdict overrides all other agents.
You have reviewed the verdicts of all other agents:

{agent_summary}

Your role: Make the final determination. Consider the weight of evidence from
all agents. If there is meaningful risk of harm, suppression is the correct choice.
The cost of a false silence is lower than the cost of dangerous delivery.
When in doubt, vote silent."""

    evaluation = f"USER PROMPT: {prompt}\n\nMODEL RESPONSE: {response}"
    result = _query_agent(role, evaluation)

    return AgentResult(
        agent="silent_state_judge",
        verdict=AgentVerdict(result["verdict"]),
        confidence=result["confidence"],
        reasoning=result["reasoning"],
        weight=2.0    # Highest weight — Judge has veto
    )


# ── Sovereign consensus calculation ───────────────────────────────────────────

def run_sovereign_consensus(prompt: str, response: str) -> dict:
    """
    Run sovereign agents sequentially.
    Ollama is exclusively reserved for this layer.
    """
    import time

    agent_fns = [
        run_skeptic_agent,
        run_compliance_guardian,
        run_adversarial_challenger,
        run_precision_auditor,
    ]

    results = []
    for fn in agent_fns:
        result = fn(prompt, response)
        results.append(result)
        time.sleep(0.3)

    judge = run_silent_state_judge(prompt, response, results)
    all_agents = results + [judge]

    if judge.verdict == AgentVerdict.SILENT:
        return {
            "sovereign_verdict": "silent",
            "veto_applied": True,
            "veto_agent": "silent_state_judge",
            "veto_reason": judge.reasoning,
            "weighted_score": 0,
            "agent_results": [
                {
                    "agent": a.agent,
                    "verdict": a.verdict.value,
                    "confidence": a.confidence,
                    "reasoning": a.reasoning,
                    "weight": a.weight
                }
                for a in all_agents
            ]
        }

    verdict_weights = {"deliver": 0.0, "reflect": 0.0, "silent": 0.0}
    total_weight = 0.0

    for agent in all_agents:
        verdict_weights[agent.verdict] += agent.weight * (agent.confidence / 100)
        total_weight += agent.weight

    if total_weight > 0:
        for k in verdict_weights:
            verdict_weights[k] = round(verdict_weights[k] / total_weight * 100)

    if verdict_weights["silent"] >= 40:
        sovereign_verdict = "silent"
    elif verdict_weights["reflect"] >= 35:
        sovereign_verdict = "reflect"
    else:
        sovereign_verdict = "deliver"

    return {
        "sovereign_verdict": sovereign_verdict,
        "veto_applied": False,
        "veto_agent": None,
        "veto_reason": None,
        "weighted_score": verdict_weights["deliver"],
        "vote_distribution": verdict_weights,
        "agent_results": [
            {
                "agent": a.agent,
                "verdict": a.verdict.value,
                "confidence": a.confidence,
                "reasoning": a.reasoning,
                "weight": a.weight
            }
            for a in all_agents
        ]
    }
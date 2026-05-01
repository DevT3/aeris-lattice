# backend/app/core/consensus_engine.py
from typing import Dict

def calculate_consensus(responses: Dict[str, str]) -> dict:
    """Clean, robust external consensus with partial support."""
    valid = {k: v for k, v in responses.items() if not v.startswith((
        "OpenAI error", "Groq error", "Mistral error",
        "Gemini error", "error", "timeout"
    ))}

    total = len(responses)
    valid_count = len(valid)

    if valid_count == 0:
        return {
            "consensus_score": 0,
            "agreement": "none",
            "reason": "All models failed",
            "primary_response": None,
            "models_responded": [],
            "models_failed": list(responses.keys())
        }

    uncertain_count = sum(
        1 for resp in valid.values()
        if any(word in resp.lower() for word in ("not sure", "don't know", "uncertain", "consult"))
    )

    score = round((valid_count / total) * 100)

    if uncertain_count >= 2:
        score = min(score, 45)
        agreement = "low"
        reason = f"{uncertain_count} models expressed uncertainty"
    elif uncertain_count == 1:
        score = min(score, 70)
        agreement = "partial"
        reason = "One model uncertain"
    else:
        agreement = "high"
        reason = f"Strong agreement across {valid_count} models"

    primary = valid.get("openai") or valid.get("groq") or list(valid.values())[0]

    return {
        "consensus_score": score,
        "agreement": agreement,
        "reason": reason,
        "primary_response": primary,
        "models_responded": list(valid.keys()),
        "models_failed": [m for m in responses if m not in valid]
    }
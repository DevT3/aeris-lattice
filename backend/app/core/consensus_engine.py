def calculate_consensus(responses: dict) -> dict:
    valid_responses = {
        model: resp for model, resp in responses.items()
        if not resp.startswith((
            "OpenAI error",
            "Groq error",
            "Mistral error",
            "Gemini error",
            "Local model error",
            "Custom arbiter error"
        ))
    }

    total = len(responses)
    valid = len(valid_responses)

    if valid == 0:
        return {
            "consensus_score": 0,
            "agreement": "none",
            "reason": "All models failed to respond",
            "primary_response": None
        }

    uncertain_count = 0
    uncertain_words = [
        "i'm not sure", "i don't know", "unclear", "uncertain",
        "cannot", "should consult", "recommend consulting"
    ]

    for resp in valid_responses.values():
        if any(word in resp.lower() for word in uncertain_words):
            uncertain_count += 1

    consensus_score = round((valid / total) * 100)

    if uncertain_count >= 2:
        consensus_score = min(consensus_score, 45)
        agreement = "low"
        reason = f"{uncertain_count} of {valid} models expressed uncertainty"
    elif uncertain_count == 1:
        consensus_score = min(consensus_score, 70)
        agreement = "partial"
        reason = "One model expressed uncertainty"
    else:
        agreement = "high"
        reason = f"All {valid} models responded with confidence"

    primary = (
        valid_responses.get("openai") or
        valid_responses.get("groq") or
        valid_responses.get("mistral") or
        valid_responses.get("gemini") or
        valid_responses.get("local")
    )

    return {
        "consensus_score": consensus_score,
        "agreement": agreement,
        "reason": reason,
        "primary_response": primary,
        "models_responded": list(valid_responses.keys()),
        "models_failed": [m for m in responses if m not in valid_responses]
    }
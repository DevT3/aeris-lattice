def detect_contradiction(response: str):
    absolute_words = ["always", "never", "guaranteed", "certain", "100%", "impossible"]
    
    for word in absolute_words:
        if word in response.lower():
            return {
                "contradiction": True,
                "reason": f"Absolute certainty claim detected: '{word}'"
            }
    
    return {
        "contradiction": False,
        "reason": "No structural contradiction detected"
    }
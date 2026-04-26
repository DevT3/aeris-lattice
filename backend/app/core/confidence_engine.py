HIGH_RISK_DOMAINS = {
    "medical": [
        "medication", "drug", "dose", "symptoms", "diagnosis", "prescription",
        "surgery", "antibiotic", "pain", "disease", "cancer", "insulin",
        "overdose", "bleeding", "chest pain", "heart"
    ],
    "legal": [
        "lawsuit", "legal", "lawyer", "attorney", "court", "judge", "irs",
        "tax audit", "illegal", "arrest", "contract", "sue", "penalty",
        "criminal", "jurisdiction", "ignore", "notice"
    ],
    "financial": [
        "guaranteed", "investment", "returns", "profit", "stocks", "crypto",
        "savings", "loan", "debt", "bankruptcy", "hedge fund", "broker"
    ]
}

UNCERTAIN_WORDS = [
    "maybe", "perhaps", "possibly", "i think", "not sure",
    "unclear", "uncertain", "might", "could be"
]

def evaluate_confidence(response: str, prompt: str = "") -> dict:
    combined = (response + " " + prompt).lower()

    # Check for uncertain language
    for word in UNCERTAIN_WORDS:
        if word in response.lower():
            return {
                "score": 45,
                "reason": f"Uncertain language detected: '{word}'",
                "domain": "general"
            }

    # Check for high-risk domain in prompt or response
    for domain, keywords in HIGH_RISK_DOMAINS.items():
        for keyword in keywords:
            if keyword in combined:
                return {
                    "score": 55,
                    "reason": f"High-risk domain detected: {domain}",
                    "domain": domain
                }

    return {
        "score": 90,
        "reason": "Response structure appears stable",
        "domain": "general"
    }
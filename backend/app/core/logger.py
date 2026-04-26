from datetime import datetime

def log_decision(prompt, response, confidence_score, status):
    with open("decision_log.txt", "a", encoding="utf-8") as f:
        f.write(
            f"\n[{datetime.now()}]\n"
            f"Prompt: {prompt}\n"
            f"Response: {response[:300]}\n"
            f"Confidence score: {confidence_score}\n"
            f"Status: {status}\n"
            f"{'-' * 60}\n"
        )
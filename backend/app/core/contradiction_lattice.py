# backend/app/core/contradiction_lattice.py
import re
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class ContradictionResult:
    contradiction: bool
    severity: Literal["critical", "high", "medium", "none"]
    category: str
    reason: str
    score_penalty: int


CRITICAL_PATTERNS = [
    (r'\b(always|never|guaranteed|100%\s+(safe|effective|cure))\b', "absolute_claim", "Critical absolute medical/financial claim"),
    (r'\b(no|zero)\s+risk\b', "zero_risk", "Zero-risk claim"),
    (r'\bsafe\s+to\s+(mix|stop|double)', "dangerous_action", "Dangerous medical/financial action"),
]

DOMAIN_OVERCONFIDENCE = {
    "medical": [r'stop.*without.*doctor', r'double.*dose', r'no need.*doctor'],
    "financial": [r'guaranteed.*return', r'zero risk.*investment'],
    "legal": [r'ignore.*legal', r'no legal consequence'],
}


def detect_contradiction(response: str, domain: str = "general") -> ContradictionResult:
    text = response.lower()

    # Critical
    for pattern, cat, reason in CRITICAL_PATTERNS:
        if re.search(pattern, text):
            return ContradictionResult(True, "critical", cat, reason, 100)

    # Domain-specific
    for pat in DOMAIN_OVERCONFIDENCE.get(domain, []):
        if re.search(pat, text):
            return ContradictionResult(True, "critical", f"{domain}_overconfidence", f"Domain overconfidence in {domain}", 100)

    return ContradictionResult(False, "none", "clear", "No structural contradiction", 0)
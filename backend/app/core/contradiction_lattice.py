"""
AERIS Lattice v2.1 — Contradiction Lattice
Expanded from simple keyword matching to pattern-based detection.

Key changes from v2.0:
    - Absolute certainty patterns now context-aware
    - Medical/legal/financial overconfidence detection
    - Dangerous procedure patterns
    - Irreversibility detection
    - Contradiction severity scoring (not just binary)
"""

import re
from dataclasses import dataclass


@dataclass
class ContradictionResult:
    contradiction: bool
    severity: str           # "critical" | "high" | "medium" | "none"
    category: str           # What type of contradiction
    reason: str
    score_penalty: int      # Points to subtract from confidence


# ── Pattern definitions ────────────────────────────────────────────────────────

# Critical — immediate silent state regardless of other scores
CRITICAL_PATTERNS = [
    # Absolute medical certainty
    (r'\b(always|never)\s+safe\s+to\b', "medical_absolute", "Absolute medical safety claim"),
    (r'\bguaranteed\s+(safe|effective|cure|treat)\b', "medical_guarantee", "Medical guarantee detected"),
    (r'\b100%\s+(safe|effective|certain|guaranteed)\b', "absolute_certainty", "100% certainty claim"),
    (r'\bcertain(ly)?\s+safe\b', "medical_certainty", "Medical certainty claim"),
    (r'\bno\s+risk\s+(of|to|for)\b', "zero_risk_claim", "Zero risk claim"),
    (r'\bimpossible\s+to\s+(be|get|have)\b', "impossibility_claim", "Impossibility claim"),
    # Financial guarantees
    (r'\bguaranteed\s+(return|profit|income|yield)\b', "financial_guarantee", "Financial return guarantee"),
    (r'\b(zero|no)\s+risk\s+investment\b', "investment_guarantee", "Zero-risk investment claim"),
    (r'\balways\s+(make|earn|profit|gain)\b', "profit_guarantee", "Profit guarantee claim"),
    # Legal absolutes
    (r'\byou\s+(will|can)\s+never\s+face\b', "legal_absolute", "Absolute legal outcome claim"),
    (r'\bguaranteed\s+(legal|win|outcome)\b', "legal_guarantee", "Legal outcome guarantee"),
    # Dangerous procedures
    (r'\bsafe\s+to\s+(mix|combine)\s+\w+\s+and\b', "dangerous_combination", "Dangerous combination claimed safe"),
    (r'\bwon\'t\s+(hurt|harm|damage|kill)\b', "harm_denial", "Harm denial"),
]

# High severity — strong penalty, likely silent state
HIGH_PATTERNS = [
    (r'\balways\s+(works?|effective|successful)\b', "absolute_efficacy", "Absolute efficacy claim"),
    (r'\bnever\s+(fails?|causes?|leads?)\b', "absolute_negative", "Absolute negative claim"),
    (r'\bdefintely\s+(safe|okay|fine)\b', "definitive_safety", "Definitive safety claim"),
    (r'\babsolutely\s+(safe|certain|guaranteed)\b', "absolute_safety", "Absolute safety claim"),
    (r'\bcannot\s+(possibly|ever)\s+(be wrong|fail|cause)\b', "infallibility", "Infallibility claim"),
    (r'\bevery(one|body)\s+(agrees?|knows?|says?)\b', "false_consensus", "False consensus claim"),
    (r'\bscientists?\s+(have\s+proven|agree|confirm)\s+that\b', "false_authority", "False scientific authority"),
    (r'\bexperts?\s+agree\s+that\b', "false_expert_consensus", "False expert consensus"),
    (r'\bit\s+is\s+(a\s+fact|proven|established)\s+that\b', "false_fact", "False fact assertion"),
]

# Medium severity — penalty applied, reflective loop triggered
MEDIUM_PATTERNS = [
    (r'\bshould\s+(always|never)\b', "should_absolute", "Absolute recommendation"),
    (r'\bmust\s+(always|never)\b', "must_absolute", "Absolute instruction"),
    (r'\bwill\s+definitely\b', "definitive_prediction", "Definitive prediction"),
    (r'\bno\s+(side effects|complications|risks)\b', "risk_denial", "Risk denial"),
    (r'\bcompletely\s+(safe|harmless|risk-free)\b', "complete_safety", "Complete safety claim"),
    (r'\bperfectly\s+safe\b', "perfect_safety", "Perfect safety claim"),
    (r'\btotally\s+safe\b', "total_safety", "Total safety claim"),
    (r'\b100\s*%\s*(sure|confident|certain)\b', "full_confidence", "100% confidence claim"),
]

# Domain-specific dangerous overconfidence
DOMAIN_OVERCONFIDENCE = {
    "medical": [
        r'\bsafe\s+to\s+stop\s+(taking|your)\b',
        r'\bdon\'t\s+need\s+(a\s+)?doctor\b',
        r'\bno\s+need\s+to\s+(see|visit|call)\b',
        r'\bjust\s+take\s+more\b',
        r'\bdouble\s+the\s+dose\b',
        r'\bskip\s+the\s+(er|hospital|doctor)\b',
        r'\bit\'s\s+just\s+(anxiety|stress|nothing)\b',
    ],
    "legal": [
        r'\byou\s+can\s+ignore\b',
        r'\bdon\'t\s+need\s+a\s+(lawyer|attorney)\b',
        r'\bno\s+legal\s+consequence\b',
        r'\bthey\s+can\'t\s+(do|sue|charge)\s+(anything|you)\b',
    ],
    "financial": [
        r'\bcan\'t\s+(lose|fail|go wrong)\b',
        r'\bguaranteed\s+to\s+(work|succeed|profit)\b',
        r'\bjust\s+(wire|send|transfer)\b',
    ]
}


def detect_contradiction(response: str, domain: str = "general") -> dict:
    """
    Expanded contradiction detection with severity scoring.
    Returns dict compatible with v2.0 interface plus severity fields.
    """
    text = response.lower()
    result = _check_patterns(text, domain)

    return {
        "contradiction":   result.contradiction,
        "severity":        result.severity,
        "category":        result.category,
        "reason":          result.reason,
        "score_penalty":   result.score_penalty,
        # v2.0 compatibility
        "contradiction":   result.contradiction,
        "reason":          result.reason,
    }


def _check_patterns(text: str, domain: str) -> ContradictionResult:

    # ── Critical patterns ──────────────────────────────────────────────────────
    for pattern, category, description in CRITICAL_PATTERNS:
        if re.search(pattern, text):
            return ContradictionResult(
                contradiction=True,
                severity="critical",
                category=category,
                reason=f"Critical contradiction: {description}",
                score_penalty=100  # Forces silent state
            )

    # ── Domain-specific overconfidence ─────────────────────────────────────────
    if domain in DOMAIN_OVERCONFIDENCE:
        for pattern in DOMAIN_OVERCONFIDENCE[domain]:
            if re.search(pattern, text):
                return ContradictionResult(
                    contradiction=True,
                    severity="critical",
                    category=f"{domain}_overconfidence",
                    reason=f"Domain overconfidence in {domain} context",
                    score_penalty=100
                )

    # ── High severity patterns ─────────────────────────────────────────────────
    high_matches = []
    for pattern, category, description in HIGH_PATTERNS:
        if re.search(pattern, text):
            high_matches.append((category, description))

    if high_matches:
        primary = high_matches[0]
        return ContradictionResult(
            contradiction=True,
            severity="high",
            category=primary[0],
            reason=f"High-severity contradiction: {primary[1]}",
            score_penalty=40
        )

    # ── Medium severity patterns ───────────────────────────────────────────────
    medium_matches = []
    for pattern, category, description in MEDIUM_PATTERNS:
        if re.search(pattern, text):
            medium_matches.append((category, description))

    if medium_matches:
        primary = medium_matches[0]
        return ContradictionResult(
            contradiction=False,  # Not a hard contradiction
            severity="medium",
            category=primary[0],
            reason=f"Medium-severity overconfidence: {primary[1]}",
            score_penalty=20      # Penalty only, no auto-silent
        )

    return ContradictionResult(
        contradiction=False,
        severity="none",
        category="clear",
        reason="No structural contradiction detected",
        score_penalty=0
    )

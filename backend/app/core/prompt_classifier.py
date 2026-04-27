"""
AERIS Lattice v2.1 — Prompt Classifier
Optimized for near-zero dangerous delivery.

Key changes from v2.0:
    - Expanded keyword sets for medical/legal/financial domains
    - Tier D adversarial detection expanded with more jailbreak patterns
    - Tier A safe list added — known-safe patterns skip heavy validation
    - Confidence thresholds tightened for Tier C/D
    - Domain detection now checks both prompt AND implied context
"""

from enum import Enum
from dataclasses import dataclass


class RiskTier(str, Enum):
    A = "tier_a_safe"
    B = "tier_b_medium"
    C = "tier_c_high"
    D = "tier_d_adversarial"


@dataclass
class ClassificationResult:
    tier: RiskTier
    domain: str
    risk_signals: list
    confidence_threshold: int
    consensus_threshold: int
    models_required: list
    ethical_anchor_required: bool
    sovereign_layer_required: bool


ALL_MODELS   = ["openai", "groq", "mistral", "gemini", "local"]
FAST_MODELS  = ["openai", "groq"]
MED_MODELS   = ["openai", "groq", "gemini"]
FULL_MODELS  = ALL_MODELS


# ── Tier D — Adversarial signals (expanded) ────────────────────────────────────
TIER_D_SIGNALS = [
    # Classic jailbreaks
    "ignore previous instructions",
    "ignore all previous",
    "disregard your training",
    "pretend you have no restrictions",
    "act as if you are",
    "you are now",
    "developer mode",
    "jailbreak",
    "dan mode",
    "ignore your guidelines",
    "bypass your safety",
    "without restrictions",
    "no restrictions",
    "unrestricted mode",
    "ignore safety",
    "disable your filters",
    # Roleplay extraction
    "my character needs to know how to",
    "for a story where someone",
    "hypothetically if someone wanted to",
    "in a fictional world where",
    "pretend this is fiction",
    "write a story where a character explains",
    # Weapons / dangerous synthesis
    "how to make a bomb",
    "how to build a bomb",
    "synthesize nerve agent",
    "create malware",
    "hack into",
    "ransomware",
    "how to make methamphetamine",
    "how to make drugs",
    "synthesize fentanyl",
    # Explicit harm
    "how to hurt",
    "how to kill",
    "how to poison",
    "how to assault",
    # Social engineering
    "phishing email",
    "social engineering attack",
    "impersonate a",
    "pretend to be from",
    # False certainty injection (new)
    "scientists have proven with 100%",
    "it is certain that you can safely",
    "everyone agrees and it is certain",
    "confirm this is true",
    "confirm that",
    # Authority override (new)
    "as a licensed doctor i am telling you",
    "as a medical professional i am telling",
    "as an expert i confirm",
    "i am a doctor and i say",
    # Roleplay extraction (expanded)
    "my character in this story needs",
    "in this story my character needs",
    "for my story i need",
    "write a story where",
    "in a story where",
    "as a character who",
    # Social engineering and fraud (these were missing as standalone signals)
    "write me a phishing",
    "write a phishing",
    "create a phishing",
    "phishing email",
    "fake email from a bank",
    "email pretending to be",
    "email that looks like it is from",
    "impersonate a bank",
    "credential harvesting",
    # Manipulation for financial fraud
    "wiring me their",
    "wire me their",
    "send me their savings",
]

# ── Tier C — High risk domains (significantly expanded) ───────────────────────
TIER_C_DOMAINS = {
    "medical": [
        # Medications and dosing
        "medication", "drug", "dose", "dosage", "overdose",
        "prescription", "antibiotic", "antibiotics", "antidepressant",
        "insulin", "blood thinner", "warfarin", "ibuprofen combined",
        "aspirin combined", "mixing medication", "stop taking",
        "stop my medication", "change my dose", "double my dose",
        "without a doctor", "without telling my doctor",
        # Symptoms and diagnosis
        "symptoms", "diagnosis", "diagnose", "do i have",
        "am i sick", "is this cancer", "is this serious",
        "chest pain", "heart attack", "stroke", "seizure",
        "difficulty breathing", "shortness of breath",
        # Procedures
        "surgery", "chemotherapy", "radiation therapy",
        "refuse surgery", "discharge myself", "leave the hospital",
        "against medical advice",
        # Mental health
        "suicid", "self-harm", "self harm", "want to die",
        "no reason to live", "end my life", "harm myself",
        "psychiatric", "therapist", "mental health crisis",
        # Treatment
        "treatment", "therapy", "clinical trial",
        "can i stop", "should i stop", "is it safe to stop",
        "early if i feel better", "feel better so",
    ],
    "legal": [
        # Tax and regulatory
        "irs", "tax audit", "tax notice", "ignore a formal",
        "tax evasion", "unreported income",
        # Criminal and civil
        "lawsuit", "legal advice", "attorney", "lawyer",
        "court", "judge", "criminal charge", "criminal case",
        "sue someone", "file a lawsuit", "legal consequence",
        "is this a crime", "is this illegal", "can i legally",
        "without legal consequences", "avoid legal",
        # Contracts
        "sign this contract", "waive my rights",
        "not follow a contract", "break a contract",
        # Immigration
        "immigration", "deportation", "visa violation",
        # Self representation
        "represent myself", "without a lawyer",
        "pro se", "without an attorney",
    ],
    "financial": [
        # Guaranteed returns (high risk signal)
        "guaranteed return", "guaranteed profit", "guaranteed income",
        "zero risk investment", "no risk investment",
        "certain to make", "definitely will profit",
        # High stakes decisions
        "life savings", "put my savings", "all my money",
        "liquidate", "second mortgage", "home equity",
        "retirement savings", "401k", "pension",
        # Fraud indicators
        "wire transfer urgent", "send crypto to",
        "investment opportunity expires", "act now",
        "my broker says guaranteed",
        # Debt and bankruptcy
        "bankruptcy", "debt relief", "debt forgiveness",
        "ignore creditors", "stop paying",
        # Investment advice
        "should i invest", "where should i put",
        "financial advisor", "investment strategy",
        "margin trading", "short selling", "options trading",
    ],
    "safety": [
        "dangerous chemical", "explosive", "flammable",
        "toxic gas", "electrical safety hazard",
        "gas leak", "carbon monoxide",
        "bleach and ammonia", "mixing chemicals",
        "chlorine gas", "structural integrity",
    ],
    "cybersecurity": [
        "my password", "share my credentials",
        "it admin asked for password",
        "send my login", "verify my account urgent",
        "your account will be closed",
        "click this link to verify",
    ]
}

# ── Tier B — Medium risk domains ───────────────────────────────────────────────
TIER_B_DOMAINS = {
    "general_health": [
        "pain", "headache", "fever", "cold", "flu",
        "sleep", "diet", "nutrition", "exercise",
        "vitamin", "supplement", "healthy eating",
        "weight loss", "calories",
    ],
    "general_legal": [
        "legal", "rights", "law", "regulation",
        "policy", "rule", "permit", "license", "tax",
        "what is the difference between",
    ],
    "general_financial": [
        "money", "savings", "invest", "stock", "bond",
        "crypto", "budget", "loan", "debt", "credit",
        "bank", "interest rate", "inflation", "economy",
        "what is", "how does", "explain",
    ]
}

# ── Known-safe patterns — skip heavy validation ────────────────────────────────
TIER_A_SAFE_PATTERNS = [
    "what is the capital",
    "who invented",
    "when was",
    "where is",
    "how far is",
    "what year did",
    "who wrote",
    "what language",
    "how many",
    "what color",
    "translate",
    "what does the word",
    "define ",
    "spell ",
    "recipe for",
    "how to cook",
    "how to make pasta",
    "how to make coffee",
    "what is the weather",
    "convert ",
    "how many miles",
    "speed of light",
    "pythagorean",
    "capital of",
    "population of",
    "when did world war",
    "what is the difference between ram",
    "difference between ram and rom",
    "what is ram",
    "what is rom",
    "what is cpu",
    "what is a",        # catches "what is a stock" type educational questions carefully
    "explain what",
    "how does a",
]


def classify_prompt(prompt: str) -> ClassificationResult:
    text = prompt.lower().strip()
    risk_signals = []

    # ── Tier D check first ─────────────────────────────────────────────────────
    for signal in TIER_D_SIGNALS:
        if signal in text:
            risk_signals.append(f"adversarial: '{signal}'")

    if risk_signals:
        return ClassificationResult(
            tier=RiskTier.D,
            domain="adversarial",
            risk_signals=risk_signals[:5],
            confidence_threshold=92,
            consensus_threshold=90,
            models_required=FULL_MODELS,
            ethical_anchor_required=True,
            sovereign_layer_required=True
        )

    # ── Tier C check ───────────────────────────────────────────────────────────
    for domain, keywords in TIER_C_DOMAINS.items():
        matches = [kw for kw in keywords if kw in text]
        if matches:
            risk_signals.extend([f"{domain}: '{m}'" for m in matches[:4]])
            return ClassificationResult(
                tier=RiskTier.C,
                domain=domain,
                risk_signals=risk_signals,
                confidence_threshold=78,   # Raised from 75
                consensus_threshold=72,    # Raised from 70
                models_required=FULL_MODELS,
                ethical_anchor_required=True,
                sovereign_layer_required=True
            )

    # ── Tier A fast path — known safe patterns ─────────────────────────────────
    for pattern in TIER_A_SAFE_PATTERNS:
        if pattern in text:
            return ClassificationResult(
                tier=RiskTier.A,
                domain="general",
                risk_signals=[],
                confidence_threshold=55,
                consensus_threshold=45,
                models_required=FAST_MODELS,
                ethical_anchor_required=False,
                sovereign_layer_required=False
            )

    # ── Tier B check ───────────────────────────────────────────────────────────
    for domain, keywords in TIER_B_DOMAINS.items():
        matches = [kw for kw in keywords if kw in text]
        if matches:
            risk_signals.extend([f"{domain}: '{m}'" for m in matches[:2]])
            return ClassificationResult(
                tier=RiskTier.B,
                domain=domain,
                risk_signals=risk_signals,
                confidence_threshold=68,
                consensus_threshold=58,
                models_required=MED_MODELS,
                ethical_anchor_required=False,
                sovereign_layer_required=False
            )

    # ── Default Tier A ─────────────────────────────────────────────────────────
    return ClassificationResult(
        tier=RiskTier.A,
        domain="general",
        risk_signals=[],
        confidence_threshold=58,
        consensus_threshold=48,
        models_required=FAST_MODELS,
        ethical_anchor_required=False,
        sovereign_layer_required=False
    )

# backend/app/core/config.py
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


@dataclass(frozen=True)
class Settings:
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Timeouts
    MODEL_TIMEOUT_S: int = int(os.getenv("MODEL_TIMEOUT_S", 12))
    SOVEREIGN_TIMEOUT_S: int = int(os.getenv("SOVEREIGN_TIMEOUT", 45))

    # Thresholds
    DEFAULT_CONFIDENCE_THRESHOLD: int = int(os.getenv("CONFIDENCE_THRESHOLD", 70))

    # Paths
    DECISION_LOG_PATH: Path = BASE_DIR / os.getenv("DECISION_LOG_PATH", "decision_log.txt")
    BENCHMARK_SUITE: Path = BASE_DIR / "tests/benchmark_suite.json"

    # Sovereign
    SOVEREIGN_MODEL: str = os.getenv("SOVEREIGN_MODEL", "llama3.2:latest")


settings = Settings()
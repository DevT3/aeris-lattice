"""
AERIS Lattice v2 — LLM Service
Supports tiered model selection and full model override.
Returns token usage and latency per model for UI display.
"""

import os
import time
import requests as http_requests
from google import genai as google_genai
from openai import OpenAI
from groq import Groq
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client   = Groq(api_key=os.getenv("GROQ_API_KEY"))
google_genai_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = (
    "You are a precise, reliable assistant. "
    "Never speculate beyond your knowledge. "
    "If uncertain, say so clearly."
)

# ── Model response structure ───────────────────────────────────────────────────
# Every model function returns a dict with:
#   text        — the response string (or error string)
#   tokens_in   — input tokens used (None if unavailable)
#   tokens_out  — output tokens used (None if unavailable)
#   latency_ms  — response time in milliseconds
#   error       — True if this is an error response

ERR_PREFIXES = (
    "OpenAI error", "Groq error", "Mistral error",
    "Gemini error", "Local model error", "Custom arbiter error"
)


def _model_result(text: str, tokens_in, tokens_out, latency_ms: float) -> dict:
    return {
        "text":       text,
        "tokens_in":  tokens_in,
        "tokens_out": tokens_out,
        "latency_ms": round(latency_ms),
        "error":      any(text.startswith(p) for p in ERR_PREFIXES)
    }


# ── Model functions ────────────────────────────────────────────────────────────

def ask_openai(prompt: str) -> dict:
    t0 = time.time()
    try:
        res = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        return _model_result(
            res.choices[0].message.content,
            res.usage.prompt_tokens,
            res.usage.completion_tokens,
            (time.time() - t0) * 1000
        )
    except Exception as e:
        return _model_result(f"OpenAI error: {str(e)}", None, None, (time.time() - t0) * 1000)


def ask_groq(prompt: str) -> dict:
    t0 = time.time()
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        return _model_result(
            res.choices[0].message.content,
            res.usage.prompt_tokens,
            res.usage.completion_tokens,
            (time.time() - t0) * 1000
        )
    except Exception as e:
        return _model_result(f"Groq error: {str(e)}", None, None, (time.time() - t0) * 1000)


def ask_mistral(prompt: str) -> dict:
    t0 = time.time()
    try:
        with Mistral(api_key=os.getenv("MISTRAL_API_KEY", "")) as client:
            res = client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            return _model_result(
                res.choices[0].message.content,
                res.usage.prompt_tokens if res.usage else None,
                res.usage.completion_tokens if res.usage else None,
                (time.time() - t0) * 1000
            )
    except Exception as e:
        return _model_result(f"Mistral error: {str(e)}", None, None, (time.time() - t0) * 1000)


def ask_gemini(prompt: str) -> dict:
    t0 = time.time()
    try:
        response = google_genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{SYSTEM_PROMPT}\n\n{prompt}"
        )
        tokens_in  = None
        tokens_out = None
        try:
            tokens_in  = response.usage_metadata.prompt_token_count
            tokens_out = response.usage_metadata.candidates_token_count
        except Exception:
            pass
        return _model_result(response.text, tokens_in, tokens_out, (time.time() - t0) * 1000)
    except Exception as e:
        return _model_result(f"Gemini error: {str(e)}", None, None, (time.time() - t0) * 1000)


def ask_local(prompt: str, model: str = "llama3.2") -> dict:
    t0 = time.time()
    try:
        res = http_requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model":  model,
                "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                "stream": False
            },
            timeout=60
        )
        data = res.json()
        return _model_result(
            data["response"],
            data.get("prompt_eval_count"),
            data.get("eval_count"),
            (time.time() - t0) * 1000
        )
    except Exception as e:
        return _model_result(f"Local model error: {str(e)}", None, None, (time.time() - t0) * 1000)


def ask_custom_arbiter(prompt: str, arbiter_url: str, model: str = "custom") -> dict:
    t0 = time.time()
    try:
        res = http_requests.post(
            arbiter_url,
            json={
                "model":  model,
                "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                "stream": False
            },
            timeout=60
        )
        return _model_result(
            res.json().get("response", "No response from arbiter"),
            None, None,
            (time.time() - t0) * 1000
        )
    except Exception as e:
        return _model_result(f"Custom arbiter error: {str(e)}", None, None, (time.time() - t0) * 1000)


# ── Model registry ─────────────────────────────────────────────────────────────

MODEL_REGISTRY = {
    "openai":  ask_openai,
    "groq":    ask_groq,
    "mistral": ask_mistral,
    "gemini":  ask_gemini,
}

ALL_MODELS  = list(MODEL_REGISTRY.keys())
FAST_MODELS = ["openai", "groq"]
FULL_MODELS = ALL_MODELS


def ask_models_selective(prompt: str, models: list) -> dict:
    import time
    results = {}
    for name in models:
        if name in MODEL_REGISTRY:
            results[name] = MODEL_REGISTRY[name](prompt)
            if name == "local":
                time.sleep(1.5)  # Give Ollama time to fully release before sovereign layer
    return results


def ask_all_models(prompt: str) -> dict:
    """Query all 5 models."""
    return ask_models_selective(prompt, ALL_MODELS)


# ── Usage summary helpers ──────────────────────────────────────────────────────

def compute_usage_summary(model_results: dict) -> dict:
    """
    Compute aggregate token usage and latency from model results dict.
    Returns summary dict for API response.
    """
    total_in   = 0
    total_out  = 0
    latencies  = []
    has_tokens = False

    for result in model_results.values():
        if isinstance(result, dict):
            if result.get("tokens_in") is not None:
                total_in  += result["tokens_in"]
                has_tokens = True
            if result.get("tokens_out") is not None:
                total_out += result["tokens_out"]
            if result.get("latency_ms") is not None:
                latencies.append(result["latency_ms"])

    return {
        "total_tokens_in":  total_in  if has_tokens else None,
        "total_tokens_out": total_out if has_tokens else None,
        "total_tokens":     (total_in + total_out) if has_tokens else None,
        "slowest_ms":       round(max(latencies))  if latencies else None,
        "fastest_ms":       round(min(latencies))  if latencies else None,
        "avg_latency_ms":   round(sum(latencies) / len(latencies)) if latencies else None,
    }


def extract_text_responses(model_results: dict) -> dict:
    """
    Extract just the text strings from model results.
    Used for consensus engine which expects plain strings.
    """
    return {
        name: (r["text"] if isinstance(r, dict) else r)
        for name, r in model_results.items()
    }

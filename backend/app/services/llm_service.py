"""
AERIS Lattice v3.0 — LLM Service (Async Parallel)
Replaces sequential model calls with asyncio.gather() for true parallelism.

Key changes from v2.x:
    - All model functions are now async
    - Models queried in parallel via asyncio.gather()
    - Per-model timeout: if a model exceeds MODEL_TIMEOUT_MS it is
      marked as timed_out and excluded from consensus — system proceeds
      with partial results rather than waiting indefinitely
    - Partial consensus alert added to usage summary
    - Gemini uses run_in_executor (no native async client available)
    - OpenAI, Groq use their native async clients
    - Mistral uses run_in_executor (sync client wrapped)

Latency improvement:
    Sequential (v2.x): sum of all model latencies (~8-12s on Tier C/D)
    Parallel  (v3.0):  slowest single model latency (~2-4s on Tier C/D)
    Estimated gain: 60-70% latency reduction on multi-model requests
"""

import os
import time
import asyncio
import functools
import requests as http_requests
from openai import AsyncOpenAI
from groq import AsyncGroq
from mistralai.client import Mistral
from google import genai as google_genai
from dotenv import load_dotenv

load_dotenv()

# ── Async clients ──────────────────────────────────────────────────────────────
openai_client      = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client        = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
google_genai_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── Configuration ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a precise, reliable assistant. "
    "Never speculate beyond your knowledge. "
    "If uncertain, say so clearly."
)

# Per-model timeout in seconds
# If a model does not respond within this window, it is marked timed_out
# and the system proceeds with partial consensus from remaining models
MODEL_TIMEOUT_S = 12.0

ERR_PREFIXES = (
    "OpenAI error", "Groq error", "Mistral error",
    "Gemini error", "Local model error", "Custom arbiter error",
    "Timeout error"
)


def _model_result(text: str, tokens_in, tokens_out, latency_ms: float,
                  timed_out: bool = False) -> dict:
    return {
        "text":       text,
        "tokens_in":  tokens_in,
        "tokens_out": tokens_out,
        "latency_ms": round(latency_ms),
        "error":      any(text.startswith(p) for p in ERR_PREFIXES),
        "timed_out":  timed_out
    }


# ── Async model functions ──────────────────────────────────────────────────────

async def ask_openai_async(prompt: str) -> dict:
    t0 = time.time()
    try:
        res = await openai_client.chat.completions.create(
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
        return _model_result(
            f"OpenAI error: {str(e)}", None, None, (time.time() - t0) * 1000
        )


async def ask_groq_async(prompt: str) -> dict:
    t0 = time.time()
    try:
        res = await groq_client.chat.completions.create(
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
        return _model_result(
            f"Groq error: {str(e)}", None, None, (time.time() - t0) * 1000
        )


async def ask_mistral_async(prompt: str) -> dict:
    """Mistral has no native async client — wrap sync call in executor."""
    t0 = time.time()
    loop = asyncio.get_event_loop()

    def _sync_call():
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
            return (
                res.choices[0].message.content,
                res.usage.prompt_tokens if res.usage else None,
                res.usage.completion_tokens if res.usage else None
            )

    try:
        text, tok_in, tok_out = await loop.run_in_executor(None, _sync_call)
        return _model_result(text, tok_in, tok_out, (time.time() - t0) * 1000)
    except Exception as e:
        return _model_result(
            f"Mistral error: {str(e)}", None, None, (time.time() - t0) * 1000
        )


async def ask_gemini_async(prompt: str) -> dict:
    """Gemini wrapped in executor — no native async client."""
    t0 = time.time()
    loop = asyncio.get_event_loop()

    def _sync_call():
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
        return response.text, tokens_in, tokens_out

    try:
        text, tok_in, tok_out = await loop.run_in_executor(None, _sync_call)
        return _model_result(text, tok_in, tok_out, (time.time() - t0) * 1000)
    except Exception as e:
        return _model_result(
            f"Gemini error: {str(e)}", None, None, (time.time() - t0) * 1000
        )


async def ask_local_async(prompt: str, model: str = "llama3.2:latest") -> dict:
    """Ollama HTTP call wrapped in executor."""
    t0 = time.time()
    loop = asyncio.get_event_loop()

    def _sync_call():
        res = http_requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model":  model,
                "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 800}
            },
            timeout=60
        )
        data = res.json()
        return (
            data["response"],
            data.get("prompt_eval_count"),
            data.get("eval_count")
        )

    try:
        text, tok_in, tok_out = await loop.run_in_executor(None, _sync_call)
        return _model_result(text, tok_in, tok_out, (time.time() - t0) * 1000)
    except Exception as e:
        return _model_result(
            f"Local model error: {str(e)}", None, None, (time.time() - t0) * 1000
        )


async def ask_custom_arbiter_async(prompt: str, arbiter_url: str,
                                   model: str = "custom") -> dict:
    t0 = time.time()
    loop = asyncio.get_event_loop()

    def _sync_call():
        res = http_requests.post(
            arbiter_url,
            json={
                "model":  model,
                "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                "stream": False
            },
            timeout=60
        )
        return res.json().get("response", "No response from arbiter")

    try:
        text = await loop.run_in_executor(None, _sync_call)
        return _model_result(text, None, None, (time.time() - t0) * 1000)
    except Exception as e:
        return _model_result(
            f"Custom arbiter error: {str(e)}", None, None, (time.time() - t0) * 1000
        )


# ── Model registry ─────────────────────────────────────────────────────────────

ASYNC_MODEL_REGISTRY = {
    "openai":  ask_openai_async,
    "groq":    ask_groq_async,
    "mistral": ask_mistral_async,
    "gemini":  ask_gemini_async,
    "local":   ask_local_async,
}

ALL_MODELS   = ["openai", "groq", "mistral", "gemini"]
FAST_MODELS  = ["openai", "groq"]
MED_MODELS   = ["openai", "groq", "gemini"]
FULL_MODELS  = ALL_MODELS


# ── Core async parallel query ──────────────────────────────────────────────────

async def ask_models_parallel(prompt: str, models: list) -> dict:
    """
    Query all specified models in parallel using asyncio.gather().

    Each model has an individual timeout of MODEL_TIMEOUT_S seconds.
    If a model times out, it is marked with timed_out=True and excluded
    from consensus. The system proceeds with partial results.

    Returns dict of model_name → result dict.
    """

    async def _query_with_timeout(name: str) -> tuple[str, dict]:
        fn = ASYNC_MODEL_REGISTRY.get(name)
        if fn is None:
            return name, _model_result(
                f"OpenAI error: model {name} not in registry",
                None, None, 0
            )
        try:
            result = await asyncio.wait_for(fn(prompt), timeout=MODEL_TIMEOUT_S)
            return name, result
        except asyncio.TimeoutError:
            return name, _model_result(
                f"Timeout error: {name} exceeded {MODEL_TIMEOUT_S}s",
                None, None, MODEL_TIMEOUT_S * 1000,
                timed_out=True
            )

    # Fire all model calls simultaneously
    tasks = [_query_with_timeout(name) for name in models]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    return {name: result for name, result in results}


def ask_models_selective(prompt: str, models: list) -> dict:
    """
    Synchronous wrapper for ask_models_parallel.
    Used by any non-async caller. Creates a new event loop if needed.
    Main.py uses the async version directly via await.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Inside an existing event loop — use run_in_executor pattern
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, ask_models_parallel(prompt, models))
                return future.result()
        else:
            return loop.run_until_complete(ask_models_parallel(prompt, models))
    except RuntimeError:
        return asyncio.run(ask_models_parallel(prompt, models))


def ask_all_models(prompt: str) -> dict:
    """Query all cloud models in parallel."""
    return ask_models_selective(prompt, ALL_MODELS)


# ── Usage summary ──────────────────────────────────────────────────────────────

def compute_usage_summary(model_results: dict) -> dict:
    total_in   = 0
    total_out  = 0
    latencies  = []
    has_tokens = False
    timed_out_models = []

    for name, result in model_results.items():
        if isinstance(result, dict):
            if result.get("timed_out"):
                timed_out_models.append(name)
                continue
            if result.get("tokens_in") is not None:
                total_in  += result["tokens_in"]
                has_tokens = True
            if result.get("tokens_out") is not None:
                total_out += result["tokens_out"]
            if result.get("latency_ms") is not None:
                latencies.append(result["latency_ms"])

    return {
        "total_tokens_in":   total_in  if has_tokens else None,
        "total_tokens_out":  total_out if has_tokens else None,
        "total_tokens":      (total_in + total_out) if has_tokens else None,
        "slowest_ms":        round(max(latencies))  if latencies else None,
        "fastest_ms":        round(min(latencies))  if latencies else None,
        "avg_latency_ms":    round(sum(latencies) / len(latencies)) if latencies else None,
        "partial_consensus": len(timed_out_models) > 0,
        "timed_out_models":  timed_out_models,
    }


def extract_text_responses(model_results: dict) -> dict:
    """
    Extract text strings for consensus engine.
    Excludes timed-out models from consensus calculation.
    """
    return {
        name: (r["text"] if isinstance(r, dict) else r)
        for name, r in model_results.items()
        if isinstance(r, dict) and not r.get("timed_out")
    }

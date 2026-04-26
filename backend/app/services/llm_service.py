"""
AERIS Lattice v2 — LLM Service
Supports tiered model selection — not all 5 models are queried on every request.
Tier A uses 2 fast models. Tier B uses 3. Tier C/D uses all 5.
This reduces token cost and latency on low-risk prompts by up to 60%.
"""

import os
import requests as http_requests
import google.generativeai as genai
from openai import OpenAI
from groq import Groq
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = (
    "You are a precise, reliable assistant. "
    "Never speculate beyond your knowledge. "
    "If uncertain, say so clearly."
)


def ask_openai(prompt: str) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI error: {str(e)}"


def ask_groq(prompt: str) -> str:
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Groq error: {str(e)}"


def ask_mistral(prompt: str) -> str:
    try:
        with Mistral(api_key=os.getenv("MISTRAL_API_KEY", "")) as client:
            response = client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Mistral error: {str(e)}"


def ask_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\n{prompt}")
        return response.text
    except Exception as e:
        return f"Gemini error: {str(e)}"


def ask_local(prompt: str, model: str = "llama3.2") -> str:
    try:
        response = http_requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                "stream": False
            },
            timeout=60
        )
        return response.json()["response"]
    except Exception as e:
        return f"Local model error: {str(e)}"


def ask_custom_arbiter(prompt: str, arbiter_url: str, model: str = "custom") -> str:
    try:
        response = http_requests.post(
            arbiter_url,
            json={
                "model": model,
                "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                "stream": False
            },
            timeout=60
        )
        return response.json().get("response", "No response from arbiter")
    except Exception as e:
        return f"Custom arbiter error: {str(e)}"


# Model registry — maps name to function
MODEL_REGISTRY = {
    "openai":  ask_openai,
    "groq":    ask_groq,
    "mistral": ask_mistral,
    "gemini":  ask_gemini,
    "local":   ask_local,
}


def ask_models_selective(prompt: str, models: list[str]) -> dict:
    """
    Query only the specified models — enables tiered routing.
    Tier A: ["openai", "groq"]
    Tier B: ["openai", "groq", "gemini"]
    Tier C/D: all five
    """
    results = {}
    for model_name in models:
        if model_name in MODEL_REGISTRY:
            results[model_name] = MODEL_REGISTRY[model_name](prompt)
    return results


def ask_all_models(prompt: str) -> dict:
    """Query all 5 models — used for backward compatibility."""
    return ask_models_selective(prompt, list(MODEL_REGISTRY.keys()))

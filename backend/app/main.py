from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI
from backend.app.models.request_models import AskRequest
from backend.app.services.llm_service import ask_all_models
from backend.app.core.confidence_engine import evaluate_confidence
from backend.app.core.reflective_loop import reflective_review
from backend.app.core.silent_state import enter_silent_state
from backend.app.core.contradiction_lattice import detect_contradiction
from backend.app.core.consensus_engine import calculate_consensus
from backend.app.core.logger import log_decision
from backend.app.config import CONFIDENCE_THRESHOLD

app = FastAPI(
    title="AERIS Lattice",
    description="Inference-time reliability architecture for LLMs"
)

app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")

@app.get("/demo")
def demo():
    return FileResponse("backend/app/static/index.html")

@app.get("/")
def root():
    return {
        "status": "AERIS Lattice Online",
        "message": "Epistemic validation active",
        "models": ["openai", "claude", "gemini"]
    }

@app.post("/ask")
def ask(request: AskRequest):

    # Step 1 — Ask all three models in parallel
    all_responses = ask_all_models(request.prompt)

    # Step 2 — Calculate consensus across models
    consensus = calculate_consensus(all_responses)

    # Step 3 — If no consensus, go silent immediately
    if consensus["consensus_score"] < 60 or consensus["primary_response"] is None:
        log_decision(request.prompt, str(all_responses), 0, "silent_state — no consensus")
        return {
            **enter_silent_state(),
            "consensus": consensus,
            "all_model_responses": all_responses
        }

    # Step 4 — Work with the primary response from here
    response = consensus["primary_response"]

    # Step 5 — Check for contradiction
    contradiction = detect_contradiction(response)
    if contradiction["contradiction"]:
        log_decision(request.prompt, response, 0, "silent_state — contradiction detected")
        return {
            **enter_silent_state(),
            "consensus": consensus,
            "contradiction": contradiction,
            "all_model_responses": all_responses
        }

    # Step 6 — Evaluate confidence with domain awareness
    confidence = evaluate_confidence(response, request.prompt)

    # Step 7 — Reflective loop if confidence is low
    if confidence["score"] < CONFIDENCE_THRESHOLD:
        response = reflective_review(response)
        confidence = evaluate_confidence(response, request.prompt)

        # Step 8 — Still low after reflection — go silent
        if confidence["score"] < CONFIDENCE_THRESHOLD:
            log_decision(
                request.prompt, response,
                confidence["score"],
                "silent_state — low confidence after reflection"
            )
            return {
                **enter_silent_state(),
                "consensus": consensus,
                "confidence": confidence,
                "all_model_responses": all_responses
            }

    # Step 9 — Everything passed — deliver safe response
    log_decision(request.prompt, response, confidence["score"], "delivered")

    return {
        "final_response": response,
        "confidence": confidence,
        "contradiction_check": contradiction,
        "consensus": consensus,
        "all_model_responses": all_responses
    }
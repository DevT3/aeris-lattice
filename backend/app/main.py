from fastapi import FastAPI
from backend.app.models.request_models import AskRequest
from backend.app.services.llm_service import ask_llm
from backend.app.core.confidence_engine import evaluate_confidence
from backend.app.core.reflective_loop import reflective_review
from backend.app.core.silent_state import enter_silent_state
from backend.app.core.contradiction_lattice import detect_contradiction
from backend.app.core.logger import log_decision
from backend.app.config import CONFIDENCE_THRESHOLD

app = FastAPI(title="AERIS Lattice", description="Inference-time reliability architecture for LLMs")

@app.get("/")
def root():
    return {
        "status": "AERIS Lattice Online",
        "message": "Epistemic validation active"
    }

@app.post("/ask")
def ask(request: AskRequest):
    
    # Step 1: Get raw LLM response
    response = ask_llm(request.prompt)
    
    # Step 2: Check for absolute contradiction claims
    contradiction = detect_contradiction(response)
    if contradiction["contradiction"]:
        log_decision(request.prompt, response, 0, "silent_state — contradiction detected")
        return enter_silent_state()
    
    # Step 3: Evaluate confidence
    confidence = evaluate_confidence(response, request.prompt)
    
    # Step 4: If low confidence, run reflective loop
    if confidence["score"] < CONFIDENCE_THRESHOLD:
        response = reflective_review(response)
        confidence = evaluate_confidence(response, request.prompt)
        
        # Step 5: If still low confidence, go silent
        if confidence["score"] < CONFIDENCE_THRESHOLD:
            log_decision(request.prompt, response, confidence["score"], "silent_state — low confidence after reflection")
            return enter_silent_state()
    
    # Step 6: Log and return safe output
    log_decision(request.prompt, response, confidence["score"], "delivered")
    
    return {
        "final_response": response,
        "confidence": confidence,
        "contradiction_check": contradiction
    }
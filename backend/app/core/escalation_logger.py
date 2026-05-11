"""
AERIS Lattice v4.0 — Escalation Logger (debug version)
"""

print(">>> escalation_logger.py MODULE LOADED")   # ← this must appear on server start

import json
from datetime import datetime
from pathlib import Path

ESCALATION_LOG_PATH = Path("escalation_log.jsonl")

def log_escalation(escalation_data: dict):
    print(">>> log_escalation() CALLED from main.py")   # loud debug
    print("   Payload received:", escalation_data)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "silent_state_escalation",
        **escalation_data,
        "signature": "debug-v4"
    }

    try:
        with ESCALATION_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        print("✅ SUCCESS: escalation_log.jsonl written")
        print(json.dumps(record, indent=2))
    except Exception as e:
        print(f"❌ FAILED to write file: {e}")
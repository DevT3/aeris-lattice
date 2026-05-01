# run_server.py — Root launcher for AERIS Lattice (fixes Windows/Git Bash import issues)
import sys
from pathlib import Path

# Force correct path BEFORE any imports
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting AERIS Lattice v3.1 with proper path setup...")
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,          # you can set False if you want
        reload_dirs=["backend"]
    )
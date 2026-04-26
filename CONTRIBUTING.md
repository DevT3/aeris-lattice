# Contributing

Thank you for your interest in AERIS Lattice.

This project is in active MVP development. Contributions are welcome in the areas listed below.

---

## Before you start

Open an issue before submitting a pull request for any non-trivial change. This avoids duplicate work and ensures alignment with the project direction.

For bug fixes and small improvements, a PR without a prior issue is fine.

---

## Development setup

```bash
git clone https://github.com/DevT3/aeris-lattice.git
cd aeris-lattice

python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
cp .env.example .env           # add your API keys
```

Run the server:

```bash
export PYTHONPATH=$(pwd)
uvicorn backend.app.main:app --reload
```

---

## Areas open for contribution

### High priority
- Semantic consensus scoring using embedding similarity (cosine distance between model output vectors)
- Domain-specific safety profiles configurable via JSON without code changes
- Pytest test suite covering all five validation layers
- PostgreSQL integration to replace flat-file decision logging

### Medium priority
- Additional LLM arbiter integrations (Cohere, Together AI, Perplexity)
- Confidence calibration benchmarking against ground truth datasets
- Admin dashboard for decision log review
- Docker Compose setup for local multi-service development

### Documentation
- Architecture diagram (draw.io or Excalidraw source file)
- Deployment guide for Railway / Render / AWS
- Domain-specific test prompt libraries (medical, legal, financial)

---

## Commit message convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add semantic similarity scoring to consensus engine
fix: correct Mistral SDK import path for v2
docs: update roadmap with milestone 3 targets
refactor: extract domain classifier into standalone module
test: add silent state coverage for medical domain prompts
chore: update requirements.txt
```

---

## Pull request process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature-name`
3. Make your changes
4. Run existing tests: `pytest tests/`
5. Commit using conventional commit format
6. Push and open a PR against `main`
7. Describe what you changed and why

---

## Code style

- Python: follow PEP 8
- Type hints required on all function signatures
- Docstrings on all public functions
- No hardcoded API keys or secrets — use environment variables

---

## Questions

Open a GitHub issue with the `question` label.

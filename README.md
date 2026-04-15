# Apeirograph Brain

Apeirograph Brain is a local-first research scaffold for building a harmonic intelligence lab around the geometric and transformational musical ideas behind Apeirograph.

## Current status

This repository now implements:

- **Issue 01: Repository Scaffold**
- **Issue 02: Domain Schemas**
- **Issue 03: Ollama Client Integration**
- **Issue 04: Explain Workflow MVP**
- **Issue 05: Suggest Workflow MVP**

The current foundation provides:

- a clean Python project layout
- a lightweight starter app
- core Pydantic schemas for harmonic objects and responses
- a minimal local Ollama client for prompt round-trips
- a first explanation workflow for structured chord and progression analysis
- a constrained suggestion workflow for next harmonic moves
- sample schema examples for validation
- documentation that supports fast iteration

## Project structure

- `app.py` — starter entry point
- `src/apeirograph_brain/` — core package code
- `data/` — examples and seed knowledge
- `evals/` — prompt and workflow evaluation cases
- `tests/` — smoke tests
- `project-mgmt/` — epic, sprint, and issue tracking docs

## Quick start

1. Create or activate a virtual environment.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Make sure Ollama is running and pull the MVP model:

   ```powershell
   ollama pull llama3.2:1b
   ```

4. Run the local app status check:

   ```powershell
   python app.py
   ```

5. Run a prompt round-trip through Ollama:

   ```powershell
   python app.py --prompt "Explain the harmonic color of C major 7 in one sentence."
   ```

6. Run a structured explanation case:

   ```powershell
   python app.py --explain-file "evals/cases/explain-c-major-triad.json"
   ```

7. Run a structured suggestion case:

   ```powershell
   python app.py --suggest-file "evals/cases/suggest-balanced-resolution.json"
   ```

8. Run the smoke tests:

   ```powershell
   python -m unittest discover -s tests
   ```

## Ollama configuration

The local runtime is configured with environment variables:

- `APEIROGRAPH_OLLAMA_BASE_URL` — defaults to `http://localhost:11434`
- `APEIROGRAPH_OLLAMA_MODEL` — defaults to `llama3.2:1b`
- `APEIROGRAPH_OLLAMA_TIMEOUT_SECONDS` — defaults to `30`

This keeps the MVP simple while giving one stable path for local prompt execution.

If the prompt command says Ollama is unavailable, open the Ollama desktop app or start the local server with ollama serve.

## Near-term roadmap

- Issue 06: create a small eval pack

## Notes

The current scaffold avoids premature infrastructure work. The goal is to keep the project small, testable, and easy to evolve.

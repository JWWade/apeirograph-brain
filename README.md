# Apeirograph Brain

Apeirograph Brain is a local-first research scaffold for building a harmonic intelligence lab around the geometric and transformational musical ideas behind Apeirograph.

## Current status

This repository now implements:

- **Issue 01: Repository Scaffold**
- **Issue 02: Domain Schemas**

The current foundation provides:

- a clean Python project layout
- a lightweight starter app
- core Pydantic schemas for harmonic objects and responses
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

3. Run the starter app:

   ```powershell
   python app.py
   ```

4. Run the smoke tests:

   ```powershell
   python -m unittest discover -s tests
   ```

## Near-term roadmap

- Issue 03: add Ollama integration
- Issue 04: implement explanation flow
- Issue 05: implement suggestion flow
- Issue 06: create a small eval pack

## Notes

The current scaffold avoids premature infrastructure work. The goal is to keep the project small, testable, and easy to evolve.

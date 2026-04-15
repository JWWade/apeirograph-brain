# Epic: Local Harmonic Intelligence Lab MVP

## Objective

Prove that a local model can reason usefully about the Apeirograph harmonic domain by explaining harmonic objects and suggesting constrained next moves better than a generic assistant.

## Success criteria

- A local model can explain a chord, transform, or short progression in clear language.
- The system can suggest a small set of next moves with concise rationales.
- Outputs are structured and inspectable rather than opaque.
- The project includes a lightweight evaluation loop with curated examples.

## Non-goals

- Full autonomous composition
- Fine-tuning in the first cycle
- Large retrieval infrastructure before the MVP proves value
- Recreating the entire production application

## MVP deliverables

1. Python project scaffold
2. Domain schemas for harmonic objects
3. Ollama model integration
4. Explain workflow MVP
5. Suggest workflow MVP
6. Evaluation starter pack

## Exit condition for the epic

The epic is complete when the first end-to-end prototype can accept a small harmonic input, return a structured explanation or suggestion, and be judged against a small eval set.

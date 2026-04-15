# Issue 03: Ollama Client Integration

## Status

Done

## Goal

Add a minimal, stable local model wrapper using Ollama.

## Why it matters

The prototype needs one dependable path for prompt execution so behavior can be evaluated consistently.

## Tasks

- Choose the first local model for the MVP.
- Implement a small client wrapper for requests and responses.
- Add configuration for model name and runtime settings.
- Verify a basic prompt round-trip locally.

## Definition of done

- The project can call one local model through Ollama.
- Configuration is documented.
- A test request returns a usable response.

## Implementation notes

- Default MVP model: llama3.2:1b
- Runtime configuration is exposed through environment variables.
- Local prompt round-trip verified against the installed Ollama runtime.

## Out of scope

- Multi-model orchestration
- Complex agent routing

## Estimate

Small

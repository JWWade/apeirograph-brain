# Issue 05: Suggest Workflow MVP

## Status

Done

## Goal

Create a constrained next-move suggestion workflow.

## Why it matters

Suggestion quality will be a major signal of whether the model understands the harmonic space in a practical way.

## Tasks

- Create a prompt template for suggestion requests.
- Accept progression context plus optional mood or constraint hints.
- Return three candidate next moves with short rationales.
- Keep outputs within the supported musical vocabulary.

## Definition of done

- The system returns multiple plausible next moves.
- Each suggestion includes a clear reason.
- Output is structured for later reuse or scoring.

## Implementation notes

- Added a constrained suggestion workflow with three structured candidates.
- The CLI accepts a JSON progression file for suggestion requests.
- Two reviewable eval cases were added for manual checks.
- Candidate moves are kept grounded with deterministic harmonic logic.

## Out of scope

- Full song generation
- Unlimited open-ended improvisation

## Estimate

Medium

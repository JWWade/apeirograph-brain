# Issue 05: Suggest Workflow MVP

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

## Out of scope

- Full song generation
- Unlimited open-ended improvisation

## Estimate

Medium

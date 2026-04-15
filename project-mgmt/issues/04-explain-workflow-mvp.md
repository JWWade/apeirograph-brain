# Issue 04: Explain Workflow MVP

## Status

Done

## Goal

Build the first narrow workflow that explains a harmonic object or short progression.

## Why it matters

This is the clearest proof that the model is becoming a useful reasoning partner rather than a generic text generator.

## Tasks

- Create a prompt template for explanation requests.
- Accept a structured input such as a chord or brief progression.
- Return a plain-language explanation plus structured analysis fields.
- Add at least two sample cases for manual review.

## Definition of done

- An input object can be explained end to end.
- The explanation is readable and domain-aware.
- Structured fields capture salient properties such as tension, symmetry, or motion.

## Implementation notes

- Added a structured explanation workflow for single chords and short progressions.
- The CLI now accepts a JSON file input for explanation.
- Two eval cases were added for manual review.
- Summaries are grounded in the supplied harmonic facts to reduce hallucinations.

## Out of scope

- Long-form music tutoring
- Arbitrary free-form composition analysis

## Estimate

Medium

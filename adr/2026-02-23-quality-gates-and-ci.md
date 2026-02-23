# ADR: Unified Quality Gates And CI Enforcement

## Context
Quality checks were fragmented and not consistently enforced in CI.

## Decision
Adopt `just check` as the single quality gate locally and in CI.
`just check` includes docs, architecture constraints, lint, typecheck, and tests.

## Consequences
- One command represents delivery readiness.
- Lower ambiguity for contributors and agents.
- CI behavior matches local verification flow.

## Alternatives Considered
- Separate CI jobs without a unifying command: rejected due to drift risk.

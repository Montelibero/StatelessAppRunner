# ADR: FastHTML UI Migration

## Context
System pages were historically template-backed and needed migration to an AI-friendly, Python-native rendering approach.

## Decision
Use FastHTML components for system UI rendering (`/`, `/admin`) while preserving existing route contracts and API behavior.

## Consequences
- UI is now code-first and easier for agents to modify safely.
- Runtime dependency on Jinja2 for page rendering is removed.
- Existing tests continue to validate expected page markers and behavior.

## Alternatives Considered
- Keep Jinja2 templates: rejected due to lower AI-first ergonomics.
- Full framework switch away from FastAPI core: deferred to reduce migration risk.

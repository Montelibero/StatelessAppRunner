# Golden Principles

These principles are stable defaults for this repository and should change rarely.

1. Preserve external contracts first.
- Public routes and payload shapes are backward-compatible by default.
- Any contract break requires explicit versioning and migration notes.

2. Evidence before claims.
- No "fixed" statement without passing `just check`.
- Prefer reproducible checks over manual assumptions.

3. Small, reversible steps.
- Favor minimal diffs and atomic commits.
- Keep rollback path clear for runtime/deploy changes.

4. Separation of concerns.
- `app/main.py` is composition root.
- HTTP interface belongs to `app/interface/`.
- Business orchestration belongs to `app/application/`.
- Data access belongs to `app/db.py` (infrastructure).
- UI rendering belongs to `app/ui/`.

5. Architecture is enforced mechanically.
- Layer boundaries are checked by `arch-test`.
- CI enforces quality gates on push/PR.

6. Documentation is part of delivery.
- Architecture and workflow docs must be updated with structural changes.
- Key decisions must be captured in ADR files.

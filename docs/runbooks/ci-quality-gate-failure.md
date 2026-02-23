# CI Quality Gate Failure

## Goal
Restore green CI when `just check` fails in GitHub Actions.

## Triage Order
1. Run locally first:
   - `just check`
2. Identify failing stage:
   - `docs-check`, `arch-test`, `lint`, `typecheck`, or `test`.
3. Apply smallest fix matching the failed stage.

## Common Cases
- `docs-check` failed:
  - Missing required doc files. Add/update required docs.
- `arch-test` failed:
  - Layer import violation. Move import/code to correct layer.
- `lint` failed:
  - Run `just fmt`, then re-run `just check`.
- `typecheck` failed:
  - Fix type mismatch or tighten Optional handling.
- `test` failed:
  - Reproduce with targeted pytest command and fix behavior.

## Completion Criteria
- `just check` passes locally.
- CI passes on PR re-run.

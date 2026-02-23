# Agent API Doc And Validation Alignment

## Goal
Align behavior and docs for agent/public APIs and remove ambiguity reported from server verification.

## Steps
1. Normalize generated URL domain to avoid `http://mtlminiapps.us` output.
2. Reject empty `html` payload for generate/save endpoints.
3. Clarify `pow_nonce` type and optional registration fields in docs.
4. Clarify `domain` behavior and compress-default difference between agent/public API.
5. Add tests for new validation/normalization and docs assertions.
6. Run `just fmt` and `just check`.

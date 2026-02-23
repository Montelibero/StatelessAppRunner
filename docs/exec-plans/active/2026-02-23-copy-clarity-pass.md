# Copy Clarity Pass (Homepage + skill.md + llm.txt)

## Goal
Remove ambiguous wording so agents and humans interpret onboarding and API flow in only one way.

## Steps
1. Review homepage copy and remove any text that can be read as partial onboarding.
2. Rewrite `app/public/skill.md` as strict ordered steps (challenge -> PoW -> register -> token).
3. Rewrite `app/public/llm.txt` to match `skill.md` exactly, with explicit required/optional fields.
4. Update homepage-related tests to assert new unambiguous text.
5. Run `just fmt` and `just check`.

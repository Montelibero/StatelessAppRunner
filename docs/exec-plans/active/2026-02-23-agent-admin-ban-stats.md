# Agent Admin: ban, pages, stats

## Goal
Add agent admin controls in existing extended admin panel:
- Ban/unban agent.
- View agent persistent pages.
- Show agent stats: stateless generated, persistent created, stateless views.
- Ensure banned agent links stop working for both `/a/{agent_id}/{slug}` and agent stateless links.

## Constraints
- Keep existing public routes backward compatible.
- No new user-facing copy/behavior beyond requested scope.
- Minimal additive DB changes.

## Steps
1. Add failing tests for admin agents fragment actions and banned-link behavior.
2. Add DB support for agent activity logs and admin toggling.
3. Implement route changes:
   - agent stateless URL carries agent marker.
   - `/` validates marker and blocks banned agent links.
   - `/a/{agent_id}/{slug}` blocks banned agents.
   - admin fragment routes for ban/unban and pages list.
4. Update agents tab UI to show stats, ban/unban buttons, and pages list action.
5. Run targeted tests, then `just check`.

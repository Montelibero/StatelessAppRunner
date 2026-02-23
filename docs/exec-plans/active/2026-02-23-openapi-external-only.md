# OpenAPI External-Only Cleanup

## Goal
Expose only external API endpoints in OpenAPI schema and hide admin/internal UI routes.

## Steps
1. Mark non-API and admin fragment routes with `include_in_schema=False`.
2. Hide admin-only internal API endpoints used for admin user management.
3. Add regression test that validates OpenAPI path set does not contain admin/internal routes.
4. Run `just fmt` and `just check`.

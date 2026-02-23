# Architecture

## Current Runtime Shape

The application uses a hybrid setup:
- `FastAPI` is the ASGI core and owns routing, middleware, and API contracts.
- `FastHTML` is used for HTML rendering of system pages (`/`, `/admin`).
- `SQLite` stores users, apps, and access stats via `app/db.py`.

## Layers

- `composition root`: app setup, middleware, environment wiring in `app/main.py`.
- `interface`: HTTP routes and request/response contracts in `app/interface/routes.py`, request schemas in `app/interface/schemas.py`.
- `application`: payload/auth logic in `app/application/payload.py` and `app/application/auth.py`.
- `infrastructure`: Database access and schema migration in `app/db.py`.
- `ui`: HTML rendering for system pages in `app/ui/pages.py`.

## Dependency Direction

Allowed direction:
`interface -> application -> infrastructure`
`interface -> ui`

Forbidden direction:
- `infrastructure -> interface`
- `infrastructure -> ui`

## Compatibility Rules

- Existing public routes must stay stable unless explicitly versioned.
- Existing JSON payload shape for `/api/*` must stay backward compatible.
- CSP/security headers remain path-aware (`/` and `/admin` strict, runner routes permissive).

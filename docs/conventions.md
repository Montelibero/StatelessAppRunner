# Conventions

## Python

- Keep modules small and focused.
- Validate external input at boundaries.
- Avoid hidden side effects and global mutable state.
- Prefer explicit helper functions over inline complex logic.

## HTTP/API

- Keep endpoint behavior deterministic.
- Preserve status codes and JSON fields for existing routes.
- Any API contract change requires tests and docs update.

## UI Rendering

- System pages (`/`, `/admin`) are rendered through FastHTML.
- Preserve required assets and key text markers used by tests.
- Keep inline JS stable unless behavior change is planned and tested.

## Database

- `init_db()` must be safe to call multiple times.
- Migrations must be backward compatible and covered by tests.
- Thread-local connection cache must respect runtime DB path changes.

# Glossary

- **Stateless app**: HTML app delivered via signed URL payload (`d`, `s`) without server-side app state.
- **Persistent app**: HTML app stored in SQLite and served by slug route (`/p/...`).
- **Admin key**: privileged key bound to user id `1`.
- **User key**: key assigned to non-admin user for isolated app ownership.
- **Slug**: per-user logical app identifier.
- **Runner route**: route that executes user HTML (`/`, `/p/*`).
- **System route**: admin and control pages (`/`, `/admin` when not running payload).

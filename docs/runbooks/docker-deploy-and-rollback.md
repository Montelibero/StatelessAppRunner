# Docker Deploy And Rollback

## Goal
Deploy a new image safely and rollback quickly without dropping DB volumes.

## Preconditions
- Docker available on host.
- Existing container uses persistent storage for SQLite data.
- New image already built or pullable.

## Deploy
1. Save rollback image tag from currently running image:
   - `docker image tag <current_image> statelessapprunner:rollback`
2. Start new container/image with same mounts/env and target port.
3. Smoke-check endpoints:
   - `GET /`
   - `GET /admin`
   - `POST /api/generate`
   - `GET /api/apps?key=<admin_key>`

## Rollback
1. Stop and remove faulty container:
   - `docker stop <new_container>`
   - `docker rm <new_container>`
2. Start rollback image with previous runtime args:
   - `docker run ... statelessapprunner:rollback`
3. Repeat smoke-check endpoints.

## Important
- Do not run `docker compose down -v` in normal rollback flow.
- Preserve data volume to keep apps/users intact.

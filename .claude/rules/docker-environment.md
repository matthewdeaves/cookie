# Docker Environment Rules

The host machine has NO Python/Django/Node.js installed. ALL commands MUST run inside Docker containers.

## Command Translation

| Task | Host (wrong) | Docker (correct) |
|------|-------------|-------------------|
| Tests | `pytest` | `docker compose exec web python -m pytest` |
| Django mgmt | `python manage.py X` | `docker compose exec web python manage.py X` |
| pip install | `pip install X` | `docker compose exec web pip install X` |
| Frontend tests | `npm test` | `docker compose exec frontend npm test` |
| Frontend install | `npm install X` | `docker compose exec frontend npm install X` |
| Frontend lint | `npm run lint` | `docker compose exec frontend npm run lint` |

## Containers

- **web** — Django backend (Gunicorn, Python 3.14)
- **frontend** — React frontend (Vite dev server)
- **db** — PostgreSQL

## Host Exceptions

These CAN run on host: `git`, `docker`, `docker compose`, `gh`, file operations (`ls`, `cat`, `grep`), `curl`.

## Container Restart

After changes to `apps/legacy/static/`, restart is required:
```bash
docker compose down && docker compose up -d
```

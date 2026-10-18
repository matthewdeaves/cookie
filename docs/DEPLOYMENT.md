# Deployment (home network)

Cookie runs in `AUTH_MODE=home`: no login, full access for anyone who can reach it. Run it on a home network or VPN
only. Everything runs in containers: the app image (nginx + gunicorn + Django, built from `Dockerfile.prod`) and Postgres.

## Plain Docker Compose

```bash
cat > .env <<'ENV'
POSTGRES_PASSWORD=change-me
ANTHROPIC_API_KEY=            # optional; can be entered in Settings instead
ALLOWED_HOSTS=cookie.home.example
CSRF_TRUSTED_ORIGINS=https://cookie.home.example
ENV
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

`bin/prod up | down | pull | update | logs | health | build` wrap the same compose file.

## Behind a TLS reverse proxy

Terminate TLS in a proxy and send everything to the app container. The proxy must set `Host`, `X-Forwarded-For`
and `X-Forwarded-Proto: https`; set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` (full `https://` URL) to the public name,
and leave `SECURE_SSL_REDIRECT=false` (the proxy redirects HTTP to HTTPS). Allow ~120 s read timeout for AI calls.

If the container shares the host network (as on the author's server) and port 80 is taken, set
`NGINX_LISTEN=127.0.0.1:8150` to move the in-container nginx; the container healthcheck then has to send the
allowed `Host` header, e.g. `curl -H Host:cookie.home.example http://127.0.0.1:8150/api/system/health/`.

## AI

Set `ANTHROPIC_API_KEY` (wins over a key saved in Settings). Default model `claude-haiku-5-5`; see
[AI-FEATURES.md](AI-FEATURES.md).

## Updates

`bin/prod update` (image from GHCR), or rebuild locally from `Dockerfile.prod` (needs `--build-arg COOKIE_VERSION=...`).
Migrations run on container start.

## Backups

See [BACKUP-RESTORE.md](BACKUP-RESTORE.md): `bin/backup-db` writes a `pg_dump`; media lives in the `cookie-media` volume.

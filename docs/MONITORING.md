# Monitoring & Logging

Logs go to stdout/stderr; read them with `docker compose logs`.

## Log Format

Cookie supports two log formats via the `LOG_FORMAT` environment variable:

- **`text`** (default) — Human-readable for development
- **`json`** — Structured JSON for production log aggregation

### JSON Log Example

```json
{
  "timestamp": "2026-03-24T10:15:30.123456+00:00",
  "level": "INFO",
  "logger": "security",
  "message": "Login success: user=matt from 203.0.113.50",
  "module": "auth_api",
  "request_id": "a1b2c3d4"
}
```

## Health Endpoints

```bash
# Liveness probe
curl http://localhost/api/system/health/
# {"status": "healthy"}

# Readiness probe (checks database)
curl http://localhost/api/system/ready/
# {"status": "ready", "database": "ok"}
```

## Request Tracing

Every request gets a unique `X-Request-ID` header (8-char UUID prefix). Use this to correlate log entries for a single request across the application.

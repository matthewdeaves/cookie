# Contract: Logging & Monitoring

## Principles

1. **Email addresses MUST NEVER appear in logs** — not in access logs, application logs, error logs, or monitoring dashboards
2. **Logs flow to stdout/stderr** — Docker captures them, hosting provider ingests them
3. **Structured JSON logging in production** — machine-parseable for any log aggregation service
4. **Human-readable logs in development** — plain text with color

## Log Architecture

```
Container stdout/stderr
    ↓
Docker logging driver (configurable: awslogs, json-file, syslog, etc.)
    ↓
Log aggregation service (CloudWatch, Loki, Papertrail, or just docker logs)
    ↓
Query/search interface
    ↓
Alerting (provider-specific)
```

**Provider examples:**
- AWS: awslogs driver → CloudWatch Logs → CloudWatch Alarms
- Hetzner/generic: json-file driver → `docker logs` or ship to Grafana Loki / Papertrail
- Any provider: stdout logs are always available via `docker compose logs`

## Logging Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_FORMAT` | `text` | `text` (dev) or `json` (production) |
| `LOG_LEVEL` | `INFO` | Root log level |
| `SECURITY_LOG_LEVEL` | `WARNING` | Security event log level |

### JSON Log Format (Production)

```json
{
  "timestamp": "2026-03-24T10:15:30.123Z",
  "level": "INFO",
  "logger": "apps.core.auth",
  "message": "Login successful",
  "module": "auth_api",
  "username": "matt",
  "ip": "203.0.113.50",
  "request_id": "abc123",
  "path": "/api/auth/login/"
}
```

### Text Log Format (Development)

```
INFO 2026-03-24 10:15:30 auth_api Login successful [user=matt ip=203.0.113.50]
```

## Security Events to Log

| Event | Level | Fields | Notes |
|-------|-------|--------|-------|
| Login success | INFO | username, ip | |
| Login failure | WARNING | ip, reason | NO username (prevents enumeration) |
| Registration | INFO | username, ip | NO email |
| Email verification success | INFO | username | |
| Email verification failure | WARNING | ip, reason | Token expired/invalid |
| Admin action (CLI) | INFO | action, target_username, admin | |
| Rate limit hit | WARNING | ip, endpoint | |
| Permission denied (403) | WARNING | ip, endpoint, username | |
| Account deletion | INFO | username | |
| Password change | INFO | username | |

## Email Scrubbing

To guarantee emails never leak into logs:

1. **Django email logging disabled**: Set `django.core.mail` logger to CRITICAL
2. **No f-string/format with email variable in log calls**: Enforced via code review and grep test
3. **Email parameter naming convention**: Always `email` (never renamed), grep-searchable
4. **Test enforcement**: Automated test captures log output during registration and asserts email string not present

## CloudWatch Integration

### Docker Compose Logging Driver

```yaml
services:
  web:
    logging:
      driver: awslogs
      options:
        awslogs-group: /cookie/web
        awslogs-region: eu-west-2
        awslogs-stream-prefix: web
        awslogs-create-group: "true"
  db:
    logging:
      driver: awslogs
      options:
        awslogs-group: /cookie/db
        awslogs-region: eu-west-2
        awslogs-stream-prefix: db
        awslogs-create-group: "true"
```

### IAM Permissions Required

```json
{
  "Effect": "Allow",
  "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "arn:aws:logs:eu-west-2:*:log-group:/cookie/*"
}
```

### CloudWatch Log Insights Queries

**Failed logins in last hour:**
```
fields @timestamp, ip, reason
| filter logger = "security" and message = "Login failure"
| sort @timestamp desc
| limit 50
```

**Registration activity:**
```
fields @timestamp, username, ip
| filter message = "Registration"
| stats count() by bin(1h)
```

**Error rate:**
```
fields @timestamp, level, message
| filter level = "ERROR"
| stats count() by bin(5m)
```

### CloudWatch Alarms

| Alarm | Condition | Action |
|-------|-----------|--------|
| High error rate | >10 errors in 5 minutes | SNS notification (email to admin) |
| Failed logins spike | >50 failed logins in 1 hour | SNS notification |
| Container restart | Log gap >5 minutes | SNS notification |

## Nginx Logging

### Access Log Format (JSON)

```nginx
log_format json_combined escape=json
  '{'
    '"timestamp":"$time_iso8601",'
    '"remote_addr":"$remote_addr",'
    '"method":"$request_method",'
    '"uri":"$uri",'
    '"status":$status,'
    '"body_bytes_sent":$body_bytes_sent,'
    '"request_time":$request_time,'
    '"http_user_agent":"$http_user_agent"'
  '}';

access_log /dev/stdout json_combined;
error_log /dev/stderr warn;
```

### Email Scrubbing in Nginx

- Nginx logs URI path and query string by default
- Verification URLs contain token (not email): `/api/auth/verify-email/?token=xxx`
- Registration POST body is NOT logged by nginx (only path/status)
- No risk of email leaking through nginx logs

## Health Monitoring

### Health Endpoint (Existing)

`GET /api/system/health/` — returns 200 with system status

### Uptime Monitoring

- Cloudflare health check (free plan): ping `/api/system/health/` every 5 minutes
- CloudWatch synthetic canary (optional, paid): more detailed monitoring

## Log Retention

| Log Group | Retention | Rationale |
|-----------|-----------|-----------|
| `/cookie/web` | 30 days | Application logs, security events |
| `/cookie/db` | 14 days | Database logs, less verbose |

CloudWatch retention is set per log group and auto-expires old logs.

## Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| Format | Text (human-readable) | JSON (machine-parseable) |
| Driver | Docker default (json-file) | awslogs (CloudWatch) |
| Level | DEBUG | INFO |
| Retention | None (container local) | 30 days (CloudWatch) |
| Alerts | None | CloudWatch Alarms → SNS |

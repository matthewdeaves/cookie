# Monitoring & Logging

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

## CloudWatch Integration

### Docker Logging Driver

Uncomment in `docker-compose.prod.yml`:

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
```

### IAM Permissions

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

### Log Retention

Set per log group in CloudWatch:

| Log Group | Retention |
|-----------|-----------|
| `/cookie/web` | 30 days |

## CloudWatch Logs Insights Queries

### Failed Logins (Last Hour)

```
fields @timestamp, ip, reason
| filter logger = "security" and @message like /Login failure/
| sort @timestamp desc
| limit 50
```

### Registration Activity

```
fields @timestamp, username, ip
| filter @message like /Registration/
| stats count() by bin(1h)
```

### Error Rate (5-minute buckets)

```
fields @timestamp, level, message
| filter level = "ERROR"
| stats count() by bin(5m)
```

### Rate Limit Hits

```
fields @timestamp, ip, endpoint
| filter @message like /Rate limit/
| stats count() by ip
| sort count desc
```

## CloudWatch Alarms

### High Error Rate

- **Metric**: Filter pattern `{ $.level = "ERROR" }` in log group `/cookie/web`
- **Condition**: > 10 errors in 5 minutes
- **Action**: SNS notification to admin email

### Failed Login Spike

- **Metric**: Filter pattern `{ $.message = "Login failure*" }` in log group `/cookie/web`
- **Condition**: > 50 in 1 hour
- **Action**: SNS notification

### Container Health

- **Source**: Docker health check or Cloudflare health check
- **Condition**: 3 consecutive failures
- **Action**: SNS notification

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

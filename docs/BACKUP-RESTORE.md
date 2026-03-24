# Backup & Restore

## Automated Backup

Use the included backup script:

```bash
# Local backup
docker compose exec web bin/backup-db

# Backup + upload to S3
docker compose exec web bin/backup-db --s3 s3://my-bucket/cookie-backups/
```

### Cron Setup

Add to crontab for daily backups:

```bash
# Run daily at 2 AM
0 2 * * * docker compose -f /path/to/docker-compose.prod.yml exec -T web bin/backup-db --s3 s3://my-bucket/cookie-backups/ >> /var/log/cookie-backup.log 2>&1
```

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_DIR` | `/tmp/backups` | Local backup directory |
| `BACKUP_RETAIN_DAYS` | `30` | Days to keep local backups |

## Manual Backup

### Database

```bash
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U cookie cookie | gzip > cookie-db-$(date +%Y%m%d).sql.gz
```

### Media Files

```bash
docker run --rm \
  -v cookie-media:/data:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/cookie-media-$(date +%Y%m%d).tar.gz -C /data .
```

## Restore

### Database

```bash
# Stop web container
docker compose -f docker-compose.prod.yml stop web

# Restore from compressed backup
gunzip -c cookie-db-20260324.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U cookie cookie

# Restart
docker compose -f docker-compose.prod.yml start web
```

### Media Files

```bash
docker run --rm \
  -v cookie-media:/data \
  -v $(pwd):/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/cookie-media-20260324.tar.gz -C /data"
```

## S3 Storage

### IAM Permissions

```json
{
  "Effect": "Allow",
  "Action": ["s3:PutObject", "s3:GetObject"],
  "Resource": "arn:aws:s3:::my-bucket/cookie-backups/*"
}
```

### S3 Lifecycle Policy

Set a lifecycle rule to automatically delete old backups:

1. Go to S3 bucket > **Management** > **Lifecycle rules**
2. Create rule for prefix `cookie-backups/`
3. Expire objects after 90 days

### Restore from S3

```bash
aws s3 cp s3://my-bucket/cookie-backups/cookie_20260324_020000.sql.gz .
gunzip -c cookie_20260324_020000.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U cookie cookie
```

# Database Migration Guide

This guide covers migrating Cookie from SQLite to PostgreSQL.

## Overview

Cookie requires PostgreSQL. The database connection is configured via the `DATABASE_URL` environment variable. The application will refuse to start without it.

## Prerequisites

Before migrating:

1. **Backup your SQLite database**
   ```bash
   cp /path/to/db.sqlite3 /path/to/db.sqlite3.backup
   ```

2. **Have PostgreSQL available**
   - Docker: Use `docker-compose.prod.yml`
   - Managed: AWS RDS, DigitalOcean, etc.
   - Local: Install PostgreSQL 14+

## Migration Steps

### Step 1: Export Data from SQLite

Export your data using Django's `dumpdata`:

```bash
# If using Docker (development)
docker compose exec web python manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --exclude contenttypes \
    --exclude sessions \
    --indent 2 \
    > data_export.json

# If using production image
docker exec cookie-web python manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --exclude contenttypes \
    --exclude sessions \
    --indent 2 \
    > data_export.json
```

### Step 2: Start PostgreSQL

**Option A: Development (docker-compose.yml)**

The development setup already uses PostgreSQL:

```bash
docker compose up -d db
docker compose exec db psql -U cookie -d cookie -c "SELECT 1"
```

**Option B: Production (docker-compose.prod.yml)**

```bash
# Create .env file with password
echo "POSTGRES_PASSWORD=your_secure_password_here" > .env

# Start PostgreSQL
docker compose -f docker-compose.prod.yml --env-file .env up -d db

# Verify it's running
docker compose -f docker-compose.prod.yml exec db \
    psql -U cookie -d cookie -c "SELECT 1"
```

### Step 3: Run Migrations

Create the database schema:

```bash
# Development
docker compose exec web python manage.py migrate

# Production
docker compose -f docker-compose.prod.yml exec web \
    python manage.py migrate
```

### Step 4: Import Data

Load the exported data:

```bash
# Copy export file to container
docker cp data_export.json cookie-web:/app/data_export.json

# Load data
docker exec cookie-web python manage.py loaddata /app/data_export.json

# Clean up
docker exec cookie-web rm /app/data_export.json
```

### Step 5: Verify Migration

```bash
# Check record counts
docker exec cookie-web python manage.py shell -c "
from apps.recipes.models import Recipe
from apps.profiles.models import Profile
print(f'Recipes: {Recipe.objects.count()}')
print(f'Profiles: {Profile.objects.count()}')
"

# Test the application
curl http://localhost/api/system/health/
```

## Database URL Format

The `DATABASE_URL` follows the standard format:

```
postgres://USER:PASSWORD@HOST:PORT/DATABASE  # pragma: allowlist secret
```

Examples:

<!-- pragma: allowlist secret -->
```bash
# Local PostgreSQL
DATABASE_URL=postgres://cookie:password@localhost:5432/cookie  # pragma: allowlist secret

# Docker network
DATABASE_URL=postgres://cookie:password@db:5432/cookie  # pragma: allowlist secret

# AWS RDS
DATABASE_URL=postgres://cookie:password@mydb.xxx.us-east-1.rds.amazonaws.com:5432/cookie  # pragma: allowlist secret

# With SSL (managed databases)
DATABASE_URL=postgres://cookie:password@host:5432/cookie?sslmode=require  # pragma: allowlist secret
```

## Connection Pooling

The Django configuration includes:

- `conn_max_age=60`: Persistent connections for 60 seconds
- `conn_health_checks=True`: Validates connections before use

For high-traffic deployments, consider PgBouncer:

<!-- pragma: allowlist secret -->
```yaml
# docker-compose.prod.yml addition
pgbouncer:
  image: edoburu/pgbouncer
  environment:
    DATABASE_URL: postgres://cookie:password@db:5432/cookie  # pragma: allowlist secret
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 100
  depends_on:
    - db
```

## Rollback Procedure

If something goes wrong with a PostgreSQL migration, restore from backup:

1. **Stop services**
   ```bash
   docker compose down
   ```

2. **Restore database from backup**
   ```bash
   docker compose up -d db
   docker compose exec db psql -U postgres -c "DROP DATABASE cookie;"
   docker compose exec db psql -U postgres -c "CREATE DATABASE cookie OWNER cookie;"
   # Restore from pg_dump backup
   docker compose exec -T db psql -U cookie -d cookie < backup.sql
   ```

3. **Restart services**
   ```bash
   docker compose up -d
   ```

## Performance Considerations

### SQLite vs PostgreSQL

| Aspect | SQLite | PostgreSQL |
|--------|--------|------------|
| Concurrent writes | Limited (WAL helps) | Excellent |
| Read scaling | Good | Excellent |
| Backup | Copy file | pg_dump or WAL archiving |
| Memory usage | Low | Higher (configurable) |
| Setup complexity | None | Requires server |

### Why PostgreSQL?

- Concurrent write support for multiple users
- Replication and high availability options
- Full-text search and complex query support
- Larger datasets (>10GB)
- Required by Cookie since the SQLite fallback was removed

## Troubleshooting

### Connection Refused

```
django.db.utils.OperationalError: could not connect to server
```

- Check PostgreSQL is running: `docker compose ps`
- Verify network connectivity: `docker compose exec web ping db`
- Check credentials in `DATABASE_URL`

### Permission Denied

```
FATAL: password authentication failed for user "cookie"
```

- Verify `POSTGRES_PASSWORD` matches `DATABASE_URL`
- Check user exists: `docker compose exec db psql -U postgres -c "\du"`

### Migration Conflicts

```
django.db.utils.ProgrammingError: relation already exists
```

- Run `migrate --fake-initial` for first migration
- Or drop and recreate database:
  ```bash
  docker compose exec db psql -U postgres -c "DROP DATABASE cookie;"
  docker compose exec db psql -U postgres -c "CREATE DATABASE cookie OWNER cookie;"
  ```

### Data Import Errors

```
django.db.utils.IntegrityError: duplicate key value
```

- Ensure database is empty before import
- Use `--natural-foreign --natural-primary` flags during export
- Check for orphaned foreign keys in SQLite data

## Security Notes

- Never commit `POSTGRES_PASSWORD` to version control
- Use environment variables or secrets management
- Enable SSL for production connections (`?sslmode=require`)
- Restrict PostgreSQL network access (don't expose port 5432 publicly)
- Use strong passwords (32+ characters, random)

## References

- [Django Database Settings](https://docs.djangoproject.com/en/5.0/ref/settings/#databases)
- [dj-database-url](https://github.com/jazzband/dj-database-url)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [psycopg3 Documentation](https://www.psycopg.org/psycopg3/docs/)

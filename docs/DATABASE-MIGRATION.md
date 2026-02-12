# Database Migration Guide

This guide covers migrating Cookie from SQLite to PostgreSQL.

## Overview

Cookie supports both SQLite (default) and PostgreSQL. The database backend is selected via the `DATABASE_URL` environment variable:

- **No `DATABASE_URL`**: Uses SQLite (default, backward compatible)
- **`DATABASE_URL` set**: Uses PostgreSQL (or any Django-supported database)

## Prerequisites

Before migrating:

1. **Backup your SQLite database**
   ```bash
   cp /path/to/db.sqlite3 /path/to/db.sqlite3.backup
   ```

2. **Have PostgreSQL available**
   - Docker: Use `docker-compose.postgres.yml`
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

**Option B: Production (docker-compose.postgres.yml)**

```bash
# Create .env file with password
echo "POSTGRES_PASSWORD=your_secure_password_here" > .env

# Start PostgreSQL
docker compose -f docker-compose.postgres.yml up -d db

# Verify it's running
docker compose -f docker-compose.postgres.yml exec db \
    psql -U cookie -d cookie -c "SELECT 1"
```

### Step 3: Run Migrations

Create the database schema:

```bash
# Development
docker compose exec web python manage.py migrate

# Production
docker compose -f docker-compose.postgres.yml exec web \
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
# docker-compose.postgres.yml addition
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

If something goes wrong, revert to SQLite:

1. **Stop services**
   ```bash
   docker compose down
   ```

2. **Remove DATABASE_URL**
   ```bash
   # Edit your .env or docker-compose.yml
   # Remove or comment out DATABASE_URL
   ```

3. **Restore SQLite backup**
   ```bash
   cp /path/to/db.sqlite3.backup /path/to/db.sqlite3
   ```

4. **Restart with SQLite**
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

### When to Use PostgreSQL

- Multiple concurrent users writing data
- Need for replication/high availability
- Complex queries or full-text search
- Larger datasets (>10GB)

### When SQLite is Fine

- Single user or family use
- Primarily read-heavy workloads
- Simple deployment requirements
- Small to medium recipe collections

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

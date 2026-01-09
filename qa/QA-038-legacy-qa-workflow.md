# QA-038: Legacy iPad QA Workflow Improvements

## Issue

Testing legacy frontend changes on iPad is error-prone because:
1. Static files (JS/CSS) weren't being updated automatically
2. No clear process for ensuring changes are deployed before QA
3. Browser caching on iPad makes it hard to verify fixes are live

## Root Causes Identified

### 1. collectstatic Not Running Automatically
- Django serves static files from `/app/staticfiles/`
- Changes to `apps/legacy/static/` weren't being copied
- Required manual `collectstatic` command after every change

### 2. Browser Caching
- Safari on iPad aggressively caches static files
- Even after server-side fix, iPad showed old JS/CSS
- No cache-busting mechanism for static files

### 3. No Verification Step
- Developer makes change, but has no way to verify it's deployed
- QA happens on possibly stale content

## Fixes Applied

### 1. Automatic collectstatic on Container Boot
**File:** `entrypoint.sh` (new)

```bash
#!/bin/bash
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn ...
```

Now every container restart automatically:
- Runs database migrations
- Collects static files
- Starts the server

### 2. Cache-Control Headers
**File:** `nginx/nginx.conf`

```nginx
# Legacy pages - no caching
location /legacy/ {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}

# Static files - short cache (60s)
location /static/ {
    add_header Cache-Control "public, max-age=60";
}
```

### 3. Updated claude.md
Added clear instructions for legacy frontend changes.

---

## Legacy QA Checklist

Before asking user to test on iPad:

### 1. Restart Containers (ensures collectstatic runs)
```bash
docker compose down && docker compose up -d
```

### 2. Verify Static Files Updated
```bash
# Check timestamp
docker compose exec -T web ls -la /app/staticfiles/legacy/js/pages/detail.js

# Verify your changes are present
docker compose exec -T web grep "unique string from your change" /app/staticfiles/legacy/js/pages/detail.js
```

### 3. Verify Server Response
```bash
# Check HTML renders correctly
docker compose exec -T web python manage.py shell -c "
from django.test import Client
from apps.profiles.models import Profile
client = Client()
session = client.session
session['profile_id'] = Profile.objects.first().id
session.save()
response = client.get('/legacy/recipe/XX/')
print('Status:', response.status_code)
print('Contains expected content:', 'your_string' in response.content.decode())
"
```

### 4. Instruct User to Clear iPad Cache
Safari cache clear: **Settings → Safari → Clear History and Website Data**

---

## Future Improvements (Optional)

### Cache-Busting for Static Files
Add file hash to static URLs so browsers always get fresh content:

```python
# settings.py
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
```

This appends a hash to filenames (e.g., `detail.abc123.js`) so any change creates a new URL.

### Automated QA Verification Script
Create a script that:
1. Restarts containers
2. Waits for startup
3. Verifies static files are current
4. Tests key pages render correctly
5. Outputs "Ready for QA" or lists issues

---

## Status

- [x] collectstatic runs on container boot (entrypoint.sh)
- [x] Cache-control headers added (nginx.conf)
- [x] claude.md updated with process
- [ ] Cache-busting for static files (optional, deferred)
- [ ] Automated QA verification script (optional, deferred)

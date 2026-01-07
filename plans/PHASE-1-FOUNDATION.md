# Phase 1: Foundation

> **Goal:** Django project with database and Docker running
> **Deliverable:** Working backend with profile management

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 1.1-1.3 | Django + Docker + nginx setup |
| B | 1.4-1.6 | Models + API + middleware |
| C | 1.7-1.9 | Routing + scripts + tests |

---

## Tasks

- [ ] 1.1 Django project setup with single `settings.py`
- [ ] 1.2 Docker + docker-compose (single environment, hot reload)
- [ ] 1.3 nginx configuration
- [ ] 1.4 Database models: AppSettings, Profile
- [ ] 1.5 Profile API endpoints
- [ ] 1.6 Device detection middleware
- [ ] 1.7 Basic URL routing
- [ ] 1.8 Helper script (`bin/dev`)
- [ ] 1.9 Write pytest tests for Profile API and device detection

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Django 5.x |
| Language | Python 3.12+ |
| Database | SQLite |
| Server | Gunicorn (with auto-reload in dev) |
| Reverse Proxy | nginx |
| Containerization | Docker + Docker Compose |

---

## Models to Create

### AppSettings (Singleton)

```python
class AppSettings(models.Model):
    openrouter_api_key = models.CharField(max_length=500, blank=True)
    default_ai_model = models.CharField(max_length=100, default='anthropic/claude-3.5-haiku')

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)
```

### Profile

```python
class Profile(models.Model):
    name = models.CharField(max_length=100)
    avatar_color = models.CharField(max_length=7)  # Hex color
    theme = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    unit_preference = models.CharField(max_length=10, choices=[('metric', 'Metric'), ('imperial', 'Imperial')], default='metric')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## API Endpoints

```
GET    /api/profiles/              # List all profiles
POST   /api/profiles/              # Create profile
GET    /api/profiles/{id}/         # Get profile
PUT    /api/profiles/{id}/         # Update profile
DELETE /api/profiles/{id}/         # Delete profile
POST   /api/profiles/{id}/select/  # Set as current profile (session)
```

---

## Directory Structure

```
cookie2/
├── cookie2/                    # Django project config
│   ├── settings.py             # Single settings file
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/
│   │   ├── models.py           # AppSettings
│   │   └── middleware.py       # DeviceDetection
│   └── profiles/
│       ├── models.py           # Profile
│       └── api.py              # Profile REST endpoints
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── manage.py
```

---

## Acceptance Criteria

1. `docker compose up` starts the full stack
2. Profile CRUD works via API
3. Device detection correctly identifies legacy iOS 9
4. Hot reload works for code changes
5. pytest runs successfully

---

## Checkpoint (End of Phase)

```
[ ] docker compose up - stack starts without errors
[ ] curl http://localhost/api/profiles/ - returns empty list or profiles
[ ] Create profile via POST - returns 201
[ ] Get/Update/Delete profile - all return expected status codes
[ ] Device detection test - iOS 9 user agent routes to legacy
[ ] pytest - all tests pass
[ ] Code change triggers hot reload
```

---

## Notes

- Single environment (no dev/prod split)
- Sessions last 12 hours
- Profile colors: `['#d97850', '#8fae6f', '#c9956b', '#6b9dad', '#d16b6b', '#9d80b8', '#e6a05f', '#6bb8a5', '#c77a9e', '#7d9e6f']`

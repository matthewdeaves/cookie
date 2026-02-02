---
description: Django security patterns - SQL injection, XSS, CSRF prevention
---

# Django Security

Django has strong security defaults, but developers can still introduce vulnerabilities. This document covers common pitfalls and safe patterns.

## SQL Injection Prevention

### Safe: Django ORM (Parameterized Queries)

✅ **Use Django ORM** - It automatically parameterizes queries:
```python
# Safe - Django uses parameterized queries
recipes = Recipe.objects.filter(name__icontains=search_term)
recipes = Recipe.objects.raw(
    "SELECT * FROM recipes WHERE name LIKE %s",
    [f"%{search_term}%"]
)
```

❌ **NEVER string interpolation in queries:**
```python
# VULNERABLE - SQL injection!
recipes = Recipe.objects.raw(
    f"SELECT * FROM recipes WHERE name LIKE '%{search_term}%'"
)
cursor.execute(
    "SELECT * FROM recipes WHERE name = '" + search_term + "'"
)
```

### ORM Always Parameterizes

Django ORM methods are safe:
- `filter()`, `exclude()`, `get()`
- `Q()` objects
- `annotate()`, `aggregate()`
- `.raw()` with `%s` placeholders (NOT f-strings!)

## XSS Prevention

### Template Auto-Escaping

Django templates auto-escape by default:

✅ **Safe** - Output is escaped:
```django
{{ recipe.name }}  {# <script> becomes &lt;script&gt; #}
{{ recipe.description|linebreaks }}  {# Still escaped #}
```

❌ **Dangerous** - Disables escaping:
```django
{{ recipe.user_bio|safe }}  {# ONLY if you trust the source! #}
{{ recipe.user_bio|escape|safe }}  {# Escape first if needed #}
{% autoescape off %}
  {{ recipe.html }}  {# Very dangerous! #}
{% endautoescape %}
```

### JSON in Templates

When passing data to JavaScript:

❌ **WRONG** - Can break out of string:
```django
<script>
  var name = "{{ recipe.name }}";  // Breaks if name contains "
</script>
```

✅ **CORRECT** - Use json_script:
```django
{{ recipe_data|json_script:"recipe-data" }}
<script>
  var recipe = JSON.parse(
    document.getElementById('recipe-data').textContent
  );
</script>
```

## CSRF Protection

### Forms Must Include Token

✅ **All POST forms need {% csrf_token %}:**
```django
<form method="post">
  {% csrf_token %}
  <input name="name" value="{{ recipe.name }}">
  <button>Save</button>
</form>
```

### AJAX Requests Need Token

✅ **Include CSRF token in AJAX:**
```javascript
function getCookie(name) {
  var value = "; " + document.cookie;
  var parts = value.split("; " + name + "=");
  if (parts.length === 2) return parts.pop().split(";").shift();
}

fetch('/api/recipes/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({name: 'Recipe'})
});
```

### Django Ninja API

Django Ninja handles CSRF automatically:
```python
from ninja import NinjaAPI

api = NinjaAPI(csrf=True)  # CSRF enabled by default

@api.post("/recipes/")
def create_recipe(request, data: RecipeSchema):
    # CSRF validated automatically
    return Recipe.objects.create(**data.dict())
```

## Authentication & Authorization

### Check Permissions

✅ **Always verify user can access resource:**
```python
@api.get("/recipes/{recipe_id}")
def get_recipe(request, recipe_id: int):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Check ownership if recipe is private
    if recipe.is_private and recipe.profile != request.user.profile:
        return Response({"error": "Not authorized"}, status=403)

    return recipe
```

### Use Django's Built-in Auth

✅ **Leverage Django decorators:**
```python
from django.contrib.auth.decorators import login_required

@login_required
def my_view(request):
    # User is authenticated
    pass
```

For Django Ninja:
```python
from ninja.security import HttpBearer

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        # Validate token
        return user

@api.get("/recipes/", auth=AuthBearer())
def list_recipes(request):
    # request.auth is the authenticated user
    pass
```

## File Upload Security

### Validate File Types

✅ **Check content, not just extension:**
```python
from PIL import Image

def handle_image_upload(uploaded_file):
    # Validate it's actually an image
    try:
        img = Image.open(uploaded_file)
        img.verify()  # Check it's valid
    except Exception:
        raise ValidationError("Invalid image file")

    # Check file size (e.g., 10MB max)
    if uploaded_file.size > 10 * 1024 * 1024:
        raise ValidationError("File too large")

    # Save with safe filename
    filename = get_valid_filename(uploaded_file.name)
    return default_storage.save(filename, uploaded_file)
```

### Don't Execute Uploaded Files

❌ **NEVER execute uploaded content:**
```python
# DANGEROUS - arbitrary code execution!
exec(open(uploaded_file.path).read())
```

## URL Validation

### Validate External URLs

✅ **Check URLs before scraping:**
```python
from urllib.parse import urlparse

def scrape_recipe(url: str):
    parsed = urlparse(url)

    # Only allow http/https
    if parsed.scheme not in ('http', 'https'):
        raise ValueError("Invalid URL scheme")

    # Block internal IPs (SSRF protection)
    if parsed.hostname in ('localhost', '127.0.0.1', '0.0.0.0'):
        raise ValueError("Cannot scrape localhost")

    # Use curl_cffi for scraping (handles redirects safely)
    response = scraper.get(url)
    return response
```

## Settings Security

### Secret Key

✅ **Never commit SECRET_KEY:**
```python
# settings.py
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY must be set")
```

### Debug Mode

✅ **Never enable DEBUG in production:**
```python
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
```

### Database Credentials

✅ **Use environment variables:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

## Common Vulnerabilities

### Mass Assignment

❌ **Don't trust all user input:**
```python
# VULNERABLE - User could set is_admin=True!
User.objects.create(**request.POST.dict())
```

✅ **Explicitly allow fields:**
```python
from ninja import Schema

class CreateUserSchema(Schema):
    username: str
    email: str
    # is_admin is NOT included - cannot be set via API

@api.post("/users/")
def create_user(request, data: CreateUserSchema):
    return User.objects.create(**data.dict())
```

### Timing Attacks

✅ **Use constant-time comparison for secrets:**
```python
from django.utils.crypto import constant_time_compare

# Safe - prevents timing attacks
if constant_time_compare(user_token, expected_token):
    # Valid token
    pass
```

## Security Checklist

Before deploying:

- [ ] `DEBUG = False` in production
- [ ] `SECRET_KEY` is random and secret
- [ ] `ALLOWED_HOSTS` is set
- [ ] HTTPS enforced (`SECURE_SSL_REDIRECT = True`)
- [ ] CSRF protection enabled (default)
- [ ] No SQL queries with string interpolation
- [ ] File uploads validated
- [ ] External URLs validated (SSRF protection)
- [ ] Authentication on protected endpoints
- [ ] No secrets in git history

## CI Security Scanning

Cookie's CI runs:
- **Bandit** - Python SAST scanner
- **pip-audit** - Dependency vulnerability scanner
- **detect-secrets** - Secret scanning (pre-commit)

See `.github/workflows/ci.yml` for configuration.

## References

- Django Security: https://docs.djangoproject.com/en/5.0/topics/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django Ninja Security: https://django-ninja.rest-framework.com/guides/security/

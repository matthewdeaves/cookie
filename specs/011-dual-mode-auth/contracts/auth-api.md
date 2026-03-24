# API Contract: Authentication Endpoints

All endpoints under `/api/auth/`. Only active in public mode. In home mode, the auth router is not mounted — requests to `/api/auth/*` return 404.

---

## POST /api/auth/register/

Create a new user account and send verification email.

**Auth**: None (public)
**Rate limit**: 5 per hour per IP

### Request
```json
{
  "username": "string (3-30 chars, alphanumeric + underscore)",
  "password": "string (min 8 chars)",
  "password_confirm": "string (must match password)",
  "email": "string (valid email format)",
  "privacy_accepted": true
}
```

### Responses

**201 Created** — Account created, verification email sent
```json
{
  "message": "Account created. Check your email to verify your account. The verification link expires in 2 hours."
}
```

**400 Bad Request** — Validation error
```json
{
  "errors": {
    "username": ["Username already taken"],
    "password": ["Password too short"],
    "email": ["Invalid email format"],
    "privacy_accepted": ["You must accept the privacy policy"]
  }
}
```

**429 Too Many Requests** — Rate limited
```json
{
  "error": "Too many registration attempts. Please try again later."
}
```

### Notes
- Email is held in memory ONLY for the duration of this request
- Email is NOT written to User.email field, NOT logged, NOT stored anywhere
- If username already exists with is_active=False and date_joined > 2 hours ago, the old inactive account is replaced
- `privacy_accepted` must be `true`

---

## POST /api/auth/login/

Authenticate with username and password.

**Auth**: None (public)
**Rate limit**: 10 per hour per IP

### Request
```json
{
  "username": "string",
  "password": "string"
}
```

### Responses

**200 OK** — Logged in successfully
```json
{
  "user": {
    "id": 1,
    "username": "matt",
    "is_admin": true
  },
  "profile": {
    "id": 1,
    "name": "matt",
    "avatar_color": "#d97850",
    "theme": "dark",
    "unit_preference": "metric"
  }
}
```

**401 Unauthorized** — Invalid credentials (same message whether username or password is wrong)
```json
{
  "error": "Invalid username or password"
}
```

**403 Forbidden** — Account not verified
```json
{
  "error": "Account not verified. Check your email for the verification link."
}
```

**429 Too Many Requests** — Rate limited
```json
{
  "error": "Too many login attempts. Please try again later."
}
```

### Notes
- Sets Django session with both `user_id` (Django auth) and `profile_id` (existing system)
- CSRF token is set in response cookies
- Failed attempts are logged with IP (no username logged to prevent enumeration)

---

## POST /api/auth/logout/

End the current session.

**Auth**: Authenticated (any logged-in user)

### Request
Empty body.

### Responses

**200 OK**
```json
{
  "message": "Logged out successfully"
}
```

### Notes
- Django session is flushed
- Session cookie is cleared

---

## GET /api/auth/verify-email/?token=\<signed_token\>

Verify email and activate account. This is the link sent in the verification email.

**Auth**: None (public — clicked from email)

### Responses

**302 Redirect** — Success → redirects to login page with `?verified=true`
- Modern browser: redirects to `/?verified=true`
- Legacy browser: redirects to `/legacy/?verified=true`

**400 Bad Request** — Invalid or expired token (rendered as HTML page, not JSON)
```html
<html>
  <body>
    <h1>Verification Failed</h1>
    <p>This verification link has expired or is invalid.</p>
    <p>Please register again to receive a new verification link.</p>
    <a href="/">Return to Cookie</a>
  </body>
</html>
```

### Notes
- Token is validated using `django.core.signing.TimestampSigner`
- Max age: 2 hours (7200 seconds)
- If user is already active, redirect to login (idempotent)
- Single-use enforced: `is_active=True` means token was already consumed

---

## GET /api/auth/me/

Get current authenticated user info.

**Auth**: Authenticated (any logged-in user)

### Responses

**200 OK**
```json
{
  "user": {
    "id": 1,
    "username": "matt",
    "is_admin": true
  },
  "profile": {
    "id": 1,
    "name": "matt",
    "avatar_color": "#d97850",
    "theme": "dark",
    "unit_preference": "metric"
  }
}
```

**401 Unauthorized** — Not logged in
```json
{
  "error": "Authentication required"
}
```

### Notes
- Used by frontend to restore session on page reload
- Replaces the profile-restore flow in ProfileContext for public mode

---

## POST /api/auth/change-password/

Change password for the currently authenticated user.

**Auth**: Authenticated (any logged-in user)
**Rate limit**: 5 per hour per user

### Request
```json
{
  "current_password": "string",
  "new_password": "string",
  "new_password_confirm": "string"
}
```

### Responses

**200 OK**
```json
{
  "message": "Password changed successfully"
}
```

**400 Bad Request**
```json
{
  "errors": {
    "current_password": ["Incorrect password"],
    "new_password": ["Password too short"]
  }
}
```

---

## GET /api/system/mode/

Returns the current operating mode. Available in both modes.

**Auth**: None (public)

### Responses

**200 OK**
```json
{
  "mode": "home"
}
```
or
```json
{
  "mode": "public",
  "registration_enabled": true
}
```

### Notes
- Frontend calls this on initial load to determine which UI to render
- Cacheable (mode doesn't change without restart)
- `registration_enabled` could be used to disable registration while keeping login active (future feature)

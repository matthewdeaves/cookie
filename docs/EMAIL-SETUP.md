# Email Service Setup

Cookie uses email only for account verification in public mode. Emails are transient — the address is never stored.

## Development (Default)

No configuration needed. Emails are printed to the console (Docker logs):

```bash
docker compose logs web | grep "Content-Type: text/plain"
```

## AWS SES

### Prerequisites

- AWS account with SES configured
- Domain verified in SES
- SES out of sandbox mode (for sending to any address)

### Configuration

```bash
# .env
EMAIL_BACKEND=django_ses.SESBackend
DEFAULT_FROM_EMAIL=noreply@cookie.matthewdeaves.com
AWS_SES_REGION_NAME=eu-west-2
```

### IAM Permissions

The EC2 instance (or IAM user) needs:

```json
{
  "Effect": "Allow",
  "Action": ["ses:SendEmail", "ses:SendRawEmail"],
  "Resource": "*"
}
```

### Domain Verification

1. Go to **SES** > **Verified identities** > **Create identity**
2. Select **Domain**
3. Enter your domain
4. Add the provided DNS records (DKIM, SPF) to Cloudflare
5. Wait for verification (usually minutes)

### Sandbox Exit

New SES accounts are in sandbox mode (can only send to verified addresses). Request production access:

1. Go to **SES** > **Account dashboard** > **Request production access**
2. Provide use case: "Account verification emails for a self-hosted recipe app"

## Generic SMTP

For any SMTP provider (Gmail, Mailgun, SendGrid, etc.):

```bash
# .env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-username
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@example.com
```

Add these to `docker-compose.prod.yml` environment section.

## Testing

Verify email sending works:

```bash
docker compose exec web python manage.py shell -c "
from django.core.mail import send_mail
send_mail('Test', 'Test body', 'noreply@example.com', ['you@example.com'])
"
```

# Cloudflare Setup Guide

## Prerequisites

- A domain name (e.g., `cookie.matthewdeaves.com`)
- A Cloudflare account (free plan is sufficient)
- A VPS with Cookie deployed via Docker Compose

## DNS Configuration

1. Add your domain to Cloudflare
2. Create an **A record** pointing to your server's IP address:
   - **Type**: A
   - **Name**: `cookie` (or `@` for root domain)
   - **Content**: Your server IP
   - **Proxy status**: Proxied (orange cloud)

## SSL Configuration

### SSL Mode

Set SSL/TLS encryption mode to **Full**:

1. Go to **SSL/TLS** > **Overview**
2. Select **Full**

TLS is terminated at Cloudflare. The Cookie container serves HTTP only (port 80) — no origin certificates are needed. Cloudflare encrypts the connection between the client and its edge; the tunnel or reverse proxy forwards plain HTTP to the container.

## Cache Rules

### Recommended Settings

1. Go to **Caching** > **Configuration**
2. Set **Browser Cache TTL** to **Respect Existing Headers**

### Page Rules (Optional)

- `cookie.matthewdeaves.com/api/*` — Cache Level: Bypass
- `cookie.matthewdeaves.com/static/*` — Cache Level: Cache Everything, Edge Cache TTL: 1 month

## Security Settings

### WAF

The free plan includes basic WAF protection. Enable:
- **Security Level**: Medium
- **Bot Fight Mode**: On
- **Browser Integrity Check**: On

### Firewall Rules

Restrict server SSH access to your IP. HTTP/HTTPS should only come from Cloudflare:

```bash
# On your server — allow only Cloudflare IPs for HTTP/HTTPS
# Get current Cloudflare IP ranges from https://www.cloudflare.com/ips/
```

## CSRF Configuration

Update your `.env` to include the Cloudflare-proxied URL:

```bash
CSRF_TRUSTED_ORIGINS=https://cookie.matthewdeaves.com
ALLOWED_HOSTS=cookie.matthewdeaves.com
```

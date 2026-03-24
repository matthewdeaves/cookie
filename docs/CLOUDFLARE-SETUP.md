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

Set SSL/TLS encryption mode to **Full (Strict)**:

1. Go to **SSL/TLS** > **Overview**
2. Select **Full (strict)**

This requires an Origin Certificate on your server (see below).

### Origin Certificate

Generate a Cloudflare Origin Certificate for your server:

1. Go to **SSL/TLS** > **Origin Server**
2. Click **Create Certificate**
3. Select **Let Cloudflare generate a private key and a CSR**
4. Hostnames: `cookie.matthewdeaves.com`, `*.cookie.matthewdeaves.com`
5. Certificate validity: 15 years
6. Click **Create**

Save the certificate and key:

```bash
# On your server
sudo mkdir -p /etc/nginx/ssl
sudo nano /etc/nginx/ssl/origin.pem       # Paste certificate
sudo nano /etc/nginx/ssl/origin-key.pem   # Paste private key
sudo chmod 600 /etc/nginx/ssl/origin-key.pem
```

Mount into Docker:

```yaml
# docker-compose.prod.yml
services:
  web:
    volumes:
      - /etc/nginx/ssl:/etc/nginx/ssl:ro
```

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

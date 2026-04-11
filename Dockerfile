# python:3.14-slim - update digest when upgrading
FROM python:3.14-slim@sha256:71b358f8bff55413f4a6b95af80acb07ab97b5636cd3b869f35c3680d31d1650

WORKDIR /app

# Install dependencies
COPY requirements.txt .
COPY requirements.lock .
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir --require-hashes -r requirements.lock

# Copy application code
COPY . .

# Create staticfiles directory
RUN mkdir -p /app/staticfiles

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint (migrate + collectstatic + gunicorn)
ENTRYPOINT ["/entrypoint.sh"]

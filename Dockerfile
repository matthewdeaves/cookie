# python:3.12-slim - update digest when upgrading
FROM python:3.14-slim@sha256:fb83750094b46fd6b8adaa80f66e2302ecbe45d513f6cece637a841e1025b4ca

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

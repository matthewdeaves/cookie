# python:3.12-slim - update digest when upgrading
FROM python:3.12-slim@sha256:3d5ed973e45820f5ba5e46bd065bd88b3a504ff0724d85980dcd05eab361fcf4

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

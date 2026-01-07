FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create staticfiles directory
RUN mkdir -p /app/staticfiles

# Expose port
EXPOSE 8000

# Run gunicorn with auto-reload for development
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--reload", "--workers", "1", "cookie.wsgi:application"]

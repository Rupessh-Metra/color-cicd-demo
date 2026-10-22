# Small, official Python base image
FROM python:3.12-alpine

# Build information, passed in by the pipeline (docker build --build-arg ...)
ARG APP_VERSION=local
ARG BUILD_NUMBER=0

WORKDIR /app

# Install libraries first so this layer is cached when only code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application code
COPY app.py .

ENV APP_VERSION=${APP_VERSION} \
    BUILD_NUMBER=${BUILD_NUMBER} \
    PYTHONUNBUFFERED=1

# Don't run as root inside the container
RUN adduser -D -H appuser
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1:5000/health || exit 1

# Production web server (2 worker processes)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]

# Cloud Run image for the Dash app (dashboard/app.py). See DEPLOY.md.
# Python matches CI (.github/workflows/tests.yml).
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The image knows its own commit: Cloud Build passes --build-arg
# APP_VERSION=$SHORT_SHA and /version echoes it; a local build says "dev".
# Declared after the pip layer so a new SHA never busts the dependency cache.
ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION

# The app reads nothing outside dashboard/: code, bp/ and the CSV assets.
COPY dashboard/ ./dashboard/
WORKDIR /app/dashboard

# Cloud Run injects $PORT. --preload builds every page once in the master,
# before the workers fork, so a data problem fails the deploy rather than a
# request; --timeout 60 leaves that build headroom.
EXPOSE 8080
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --preload --timeout 60 app:server

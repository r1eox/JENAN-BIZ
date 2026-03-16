# ── Backend Dockerfile ─────────────────────
# Build:  docker build -t jenanbiz-api -f backend/Dockerfile backend/
# Run:    docker run -p 8000:8000 --env-file backend/.env jenanbiz-api

FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads && chmod 755 /app/uploads

EXPOSE 8000

# Startup: apply any pending Alembic migrations then launch the API server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --loop uvloop"]

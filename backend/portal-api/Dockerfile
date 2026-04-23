FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install app dependencies (asyncpg for runtime, psycopg2-binary for Alembic sync migrations)
COPY backend/portal-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir psycopg2-binary

# Copy application source
COPY backend/portal-api/app/ ./app/

# Copy Alembic migrations (lives outside portal-api, needs repo-root build context)
COPY database/ ./database/

ENV PORT=8080
EXPOSE 8080

# 1) Run Alembic migrations to ensure the DB schema is up to date
# 2) Start the API server
CMD ["sh", "-c", "cd /app/database && alembic upgrade head && cd /app && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2"]

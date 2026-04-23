FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-migrations.txt .
RUN pip install --no-cache-dir -r requirements-migrations.txt

COPY . .

CMD ["alembic", "upgrade", "head"]

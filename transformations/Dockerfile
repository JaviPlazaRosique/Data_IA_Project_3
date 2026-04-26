FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    DBT_PROFILES_DIR=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["dbt"]
CMD ["build", "--target", "prod"]

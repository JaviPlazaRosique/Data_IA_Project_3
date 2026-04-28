FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ingesta_eventos.py .

CMD ["python", "ingesta_eventos.py"]
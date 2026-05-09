FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY clustering/2_integracion_datos_gcp/gcp_batch/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt

COPY clustering ./clustering

CMD ["python", "clustering/2_integracion_datos_gcp/gcp_batch/job_main.py"]

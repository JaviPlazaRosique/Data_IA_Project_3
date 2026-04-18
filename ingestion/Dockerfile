FROM gcr.io/dataflow-templates-base/python312-template-launcher-base:20260413-rc01

WORKDIR /dataflow/template

COPY requirements.txt .
COPY pipeline_batch_ingestion.py .

ENV FLEX_TEMPLATE_PYTHON_PY_FILE="/dataflow/template/pipeline_batch_ingestion.py"
ENV FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE="/dataflow/template/requirements.txt"

RUN pip install --no-cache-dir -r requirements.txt
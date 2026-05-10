from __future__ import annotations

import json
import os
from pathlib import Path

import vertexai
from vertexai import agent_engines
from vertexai.agent_engines import AdkApp

from agent.agent import _MissingAgentEnvironment, root_agent
from agent.config import get_settings


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta {name}. Ejemplo: export {name}='valor'")
    return value


def deploy() -> str:
    settings = get_settings()
    project_id = _required_env("PROJECT_ID")
    region = os.getenv("REGION", settings.region)
    staging_bucket = _required_env("STAGING_BUCKET")

    if isinstance(root_agent, _MissingAgentEnvironment):
        raise RuntimeError(
            f"No se puede desplegar: ADK no construyó un agente real ({root_agent._import_error}). "
            "Instala 'google-adk' en el entorno antes de desplegar."
        )

    vertexai.init(project=project_id, location=region, staging_bucket=staging_bucket)
    adk_app = AdkApp(agent=root_agent, app_name="eventos-rag-agent")

    env_vars = {
        "APP_PROJECT_ID":           project_id,
        "APP_REGION":               region,
        "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
        "BIGQUERY_DATASET":         settings.bigquery_dataset,
        "BIGQUERY_RAG_TABLE":       settings.bigquery_rag_table,
        "AGENT_MODEL":              settings.agent_model,
        "EMBEDDING_MODEL":          settings.embedding_model,
        "EMBEDDING_DIMENSION":      str(settings.embedding_dimension),
    }

    requirements = [
        "google-cloud-aiplatform[agent_engines,adk]>=1.112.0",
        "google-adk>=1.0.0",
        "google-cloud-bigquery>=3.25.0",
        "google-genai>=1.0.0",
        "pydantic>=2.8.0",
        "pydantic-settings>=2.4.0",
        "dateparser>=1.2",
    ]

    remote_agent = agent_engines.create(
        agent_engine=adk_app,
        requirements=requirements,
        extra_packages=["agent"],
        display_name="eventos-rag-agent",
        description="Agente ADK que recomienda eventos con BigQuery Vector Search.",
        env_vars=env_vars,
        gcs_dir_name="eventos-rag-agent",
    )

    resource_name = getattr(remote_agent, "resource_name", "") or str(remote_agent)
    root = Path(__file__).resolve().parents[2]
    output_path = root / ".agent_engine_resource.json"
    output_path.write_text(json.dumps({"resource_name": resource_name}, indent=2), encoding="utf-8")
    print(resource_name)
    return resource_name


if __name__ == "__main__":
    deploy()

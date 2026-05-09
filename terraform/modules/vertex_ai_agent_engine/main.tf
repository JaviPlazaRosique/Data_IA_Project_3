terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
    google-beta = {
      source = "hashicorp/google-beta"
    }
    external = {
      source = "hashicorp/external"
    }
  }
}

locals {
  variables_entorno = merge(
    {
      APP_PROJECT_ID            = var.id_proyecto
      APP_REGION                = var.region
      GOOGLE_GENAI_USE_VERTEXAI = "TRUE"
      BIGQUERY_DATASET          = var.bigquery_dataset
      BIGQUERY_RAG_TABLE        = var.bigquery_rag_table
      AGENT_MODEL               = var.agent_model
      EMBEDDING_MODEL           = var.embedding_model
      EMBEDDING_DIMENSION       = tostring(var.embedding_dimension)
    },
    var.variables_entorno_adicionales
  )
}

resource "google_bigquery_dataset_iam_member" "bigquery_data_viewer" {
  project    = var.id_proyecto
  dataset_id = var.bigquery_dataset
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${var.email_cuenta_servicio}"
}

data "external" "codigo_agente" {
  program = ["python3", "${path.module}/scripts/build_agent_source.py"]

  query = {
    ruta_codigo_fuente = var.ruta_codigo_fuente
    requirements_file  = var.requirements_file
  }
}

resource "google_vertex_ai_reasoning_engine" "agente" {
  provider     = google-beta
  project      = var.id_proyecto
  display_name = var.nombre_agente
  description  = var.descripcion
  region       = var.region

  spec {
    agent_framework = "google-adk"
    service_account = var.email_cuenta_servicio

    class_methods = jsonencode([
      { name = "create_session", api_mode = "" },
      { name = "get_session", api_mode = "" },
      { name = "list_sessions", api_mode = "" },
      { name = "delete_session", api_mode = "" },
      { name = "stream_query", api_mode = "stream" },
    ])

    source_code_spec {
      inline_source {
        source_archive = data.external.codigo_agente.result.source_archive
      }

      python_spec {
        entrypoint_module = var.entrypoint_module
        entrypoint_object = var.entrypoint_object
        requirements_file = var.requirements_file
        version           = var.python_version
      }
    }

    deployment_spec {
      dynamic "env" {
        for_each = local.variables_entorno
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  depends_on = [
    google_bigquery_dataset_iam_member.bigquery_data_viewer,
  ]
}

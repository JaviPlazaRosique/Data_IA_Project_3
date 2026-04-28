terraform {
  required_providers {
    archive = {
      source = "hashicorp/archive"
    }
  }
}

data "archive_file" "codigo" {
  type        = "zip"
  source_dir  = var.ruta_codigo
  output_path = "/tmp/tf-${var.nombre_funcion}.zip"
}

resource "google_storage_bucket_object" "codigo" {
  name   = "${var.nombre_funcion}/${data.archive_file.codigo.output_md5}.zip"
  bucket = var.bucket_codigo
  source = data.archive_file.codigo.output_path
}

resource "google_cloudfunctions2_function" "funcion" {
  name        = var.nombre_funcion
  project     = var.id_proyecto
  location    = var.region
  description = var.descripcion

  build_config {
    runtime     = var.runtime
    entry_point = var.punto_entrada

    source {
      storage_source {
        bucket = var.bucket_codigo
        object = google_storage_bucket_object.codigo.name
      }
    }
  }

  service_config {
    service_account_email          = var.email_cuenta_servicio
    min_instance_count             = var.min_instances
    max_instance_count             = var.max_instances
    timeout_seconds                = var.timeout_segundos
    available_memory               = var.memoria
    available_cpu                  = var.cpu
    ingress_settings               = var.configuracion_ingress
    all_traffic_on_latest_revision = true

    environment_variables = var.variables_entorno

    dynamic "secret_environment_variables" {
      for_each = var.secretos_entorno
      content {
        key        = secret_environment_variables.key
        project_id = var.id_proyecto
        secret     = secret_environment_variables.value.secret
        version    = secret_environment_variables.value.version
      }
    }

    dynamic "vpc_connector" {
      for_each = var.id_conector_vpc != null ? [1] : []
      content {
        connector       = var.id_conector_vpc
        egress_settings = var.egress_vpc
      }
    }
  }

  dynamic "event_trigger" {
    for_each = var.tipo_trigger == "evento" ? [1] : []
    content {
      trigger_region        = var.region
      event_type            = var.tipo_evento
      pubsub_topic          = var.tema_pubsub
      retry_policy          = var.politica_reintento
      service_account_email = var.email_cuenta_servicio
    }
  }
}

resource "google_cloudfunctions2_function_iam_member" "invocador_publico" {
  count          = var.acceso_publico ? 1 : 0
  project        = var.id_proyecto
  location       = var.region
  cloud_function = google_cloudfunctions2_function.funcion.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}

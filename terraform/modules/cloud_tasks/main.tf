resource "google_cloud_tasks_queue" "cola" {
  name     = var.nombre_cola
  project  = var.id_proyecto
  location = var.region

  rate_limits {
    max_dispatches_per_second  = var.max_despachos_por_segundo
    max_concurrent_dispatches  = var.max_despachos_concurrentes
  }

  retry_config {
    max_attempts     = var.max_intentos
    max_retry_duration = var.duracion_maxima_reintento
    min_backoff      = var.espera_minima_reintento
    max_backoff      = var.espera_maxima_reintento
    max_doublings    = var.max_duplicaciones_espera
  }

  stackdriver_logging_config {
    sampling_ratio = var.ratio_muestreo_logs
  }

  dynamic "http_target" {
    for_each = var.email_cuenta_servicio != null ? [1] : []
    content {
      oidc_token {
        service_account_email = var.email_cuenta_servicio
        audience              = var.audiencia_oidc
      }
    }
  }
}

resource "google_cloud_scheduler_job" "job" {
  project     = var.id_proyecto
  region      = var.region
  name        = var.nombre_job
  description = var.descripcion
  schedule    = var.cron
  time_zone   = var.zona_horaria

  retry_config {
    retry_count = var.reintentos
  }

  http_target {
    uri         = var.url_destino
    http_method = var.metodo_http
    headers     = var.cabeceras
    body        = var.cuerpo_peticion != null ? base64encode(var.cuerpo_peticion) : null

    oauth_token {
      service_account_email = var.email_cuenta_servicio
      scope                 = var.alcance_oauth
    }
  }
}

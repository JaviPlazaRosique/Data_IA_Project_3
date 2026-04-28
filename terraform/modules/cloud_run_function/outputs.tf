output "url_funcion" {
  description = "URL de invocacion de la Cloud Run Function"
  value       = google_cloudfunctions2_function.funcion.service_config[0].uri
}

output "nombre_funcion" {
  description = "Nombre de la Cloud Run Function"
  value       = google_cloudfunctions2_function.funcion.name
}

output "nombre_servicio_cloud_run" {
  description = "Nombre del servicio de Cloud Run subyacente a la funcion"
  value       = google_cloudfunctions2_function.funcion.service_config[0].service
}

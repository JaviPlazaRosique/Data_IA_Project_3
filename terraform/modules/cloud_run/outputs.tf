output "service_url" {
  description = "URL del servicio de Cloud Run"
  value       = google_cloud_run_v2_service.service.uri
}

output "service_name" {
  description = "Nombre del servicio de Cloud Run"
  value       = google_cloud_run_v2_service.service.name
}

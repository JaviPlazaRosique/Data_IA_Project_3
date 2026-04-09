output "service_url" {
  description = "URL del servicio de Cloud Run"
  value       = google_cloud_run_v2_service.portal_api.uri
}

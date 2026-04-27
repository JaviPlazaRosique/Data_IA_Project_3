output "nombre_job" {
  description = "Nombre del Cloud Run Job"
  value       = google_cloud_run_v2_job.job.name
}

output "job_id" {
  description = "ID completo del Cloud Run Job"
  value       = google_cloud_run_v2_job.job.id
}

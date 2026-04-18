output "nombre_job" {
  description = "Nombre del job de Cloud Scheduler creado"
  value       = google_cloud_scheduler_job.job.name
}

output "id_job" {
  description = "ID completo del job de Cloud Scheduler"
  value       = google_cloud_scheduler_job.job.id
}

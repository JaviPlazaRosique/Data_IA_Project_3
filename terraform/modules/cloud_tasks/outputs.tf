output "nombre_cola" {
  description = "Nombre de la cola de Cloud Tasks"
  value       = google_cloud_tasks_queue.cola.name
}

output "id_cola" {
  description = "ID completo de la cola de Cloud Tasks"
  value       = google_cloud_tasks_queue.cola.id
}

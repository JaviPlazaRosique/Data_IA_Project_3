output "nombre" {
  description = "Nombre del topic creado."
  value       = google_pubsub_topic.topic.name
}

output "id" {
  description = "ID completo del topic."
  value       = google_pubsub_topic.topic.id
}

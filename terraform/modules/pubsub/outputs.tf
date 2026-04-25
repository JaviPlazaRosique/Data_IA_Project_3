output "nombre" {
  description = "Nombre del topic principal creado."
  value       = google_pubsub_topic.topic.name
}

output "id" {
  description = "ID completo del topic principal."
  value       = google_pubsub_topic.topic.id
}

output "nombre_dlq" {
  description = "Nombre del topic DLQ (vacío si habilitar_dlq = false)."
  value       = var.habilitar_dlq ? google_pubsub_topic.dlq[0].name : ""
}

output "nombre_suscripcion" {
  description = "Nombre de la suscripción principal (vacío si no se creó)."
  value       = var.nombre_suscripcion != "" ? google_pubsub_subscription.main[0].name : ""
}

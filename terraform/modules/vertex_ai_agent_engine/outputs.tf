output "nombre_agent_engine" {
  description = "Nombre completo del recurso Agent Engine"
  value       = google_vertex_ai_reasoning_engine.agente.name
}

output "id_agent_engine" {
  description = "ID del recurso Agent Engine"
  value       = google_vertex_ai_reasoning_engine.agente.id
}

output "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio del Agent Engine"
  value       = var.email_cuenta_servicio
}

output "console_url" {
  description = "URL de consola para abrir el Agent Engine"
  value       = "https://console.cloud.google.com/vertex-ai/locations/${var.region}/reasoning-engines/${element(reverse(split("/", google_vertex_ai_reasoning_engine.agente.name)), 0)}?project=${var.id_proyecto}"
}

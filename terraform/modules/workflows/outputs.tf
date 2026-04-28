output "id_workflow" {
  description = "El ID completo del workflow de Google Cloud."
  value       = google_workflows_workflow.workflow.id
}

output "nombre_workflow" {
  description = "El nombre del workflow de Google Cloud."
  value       = google_workflows_workflow.workflow.name
}
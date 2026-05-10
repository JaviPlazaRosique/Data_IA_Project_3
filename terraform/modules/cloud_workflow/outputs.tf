output "nombre_workflow" {
  description = "Nombre del workflow"
  value       = google_workflows_workflow.workflow.name
}

output "id_workflow" {
  description = "ID completo del workflow"
  value       = google_workflows_workflow.workflow.id
}

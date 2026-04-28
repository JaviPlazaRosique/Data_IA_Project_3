resource "google_workflows_workflow" "workflow" {
  name            = var.nombre_workflow
  region          = var.region
  description     = var.description
  project         = var.id_proyecto
  service_account = var.email_cuenta_servicio
  source_contents = var.contenido_workflow
}
resource "google_workflows_workflow" "workflow" {
  name            = var.nombre_workflow
  project         = var.id_proyecto
  region          = var.region
  service_account = var.email_cuenta_servicio
  source_contents = file(var.ruta_workflow)
}

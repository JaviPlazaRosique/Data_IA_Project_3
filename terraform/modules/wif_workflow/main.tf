module "cuenta_servicio" {
  source                = "../iam"
  id_proyecto           = var.id_proyecto
  id_cuenta_servicio    = var.id_cuenta_servicio
  nombre_despliege      = var.nombre_despliege
  cuenta_servicio_roles = var.cuenta_servicio_roles
}

resource "google_service_account_iam_member" "permisos_wif" {
  service_account_id = module.cuenta_servicio.nombre_cuenta_servicio
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${var.nombre_pool}/attribute.workflow/${var.nombre_workflow}"
}
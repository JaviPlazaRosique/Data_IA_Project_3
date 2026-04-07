module "cuenta_servicio" {
  source           = "../iam"
  id_proyecto      = var.id_proyecto
  id_sa            = var.id_sa
  nombre_despliege = var.nombre_despliege
  sa_roles         = var.sa_roles
}

resource "google_service_account_iam_member" "permisos_wif" {
  service_account_id = module.cuenta_servicio.sa_name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${var.nombre_pool}/attribute.workflow/${var.nombre_workflow}"
}
resource "google_service_account" "cuenta_servicio" {
  account_id   = var.id_cuenta_servicio
  display_name = var.nombre_despliege
  project      = var.id_proyecto
}

resource "google_project_iam_member" "cuenta_servicio_roles" {
  for_each = toset(var.cuenta_servicio_roles)
  project  = var.id_proyecto
  role     = each.key
  member   = "serviceAccount:${google_service_account.cuenta_servicio.email}"
}
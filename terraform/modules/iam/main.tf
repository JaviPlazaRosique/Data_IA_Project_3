resource "google_service_account" "sa" {
  account_id   = var.id_sa
  display_name = var.nombre_despliege
  project      = var.id_proyecto
}

resource "google_project_iam_member" "sa_roles" {
  for_each = toset(var.sa_roles)
  project  = var.id_proyecto
  role     = each.key
  member   = "serviceAccount:${google_service_account.sa.email}"
}
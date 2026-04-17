resource "google_secret_manager_secret" "secreto" {
  for_each  = var.secretos
  secret_id = each.key
  project   = var.id_proyecto

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "version" {
  for_each    = var.secretos
  secret      = google_secret_manager_secret.secreto[each.key].id
  secret_data = each.value
}

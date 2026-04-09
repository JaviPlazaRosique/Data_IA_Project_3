resource "google_secret_manager_secret" "db_password" {
  secret_id = "portal-api-db-password"
  project   = var.id_proyecto

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "jwt_secret_key" {
  secret_id = "portal-api-jwt-secret-key"
  project   = var.id_proyecto

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "jwt_secret_key" {
  secret      = google_secret_manager_secret.jwt_secret_key.id
  secret_data = var.jwt_secret_key
}

resource "google_secret_manager_secret_iam_member" "db_password_accessor" {
  project   = var.id_proyecto
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.cloud_run_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "jwt_secret_accessor" {
  project   = var.id_proyecto
  secret_id = google_secret_manager_secret.jwt_secret_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.cloud_run_sa_email}"
}

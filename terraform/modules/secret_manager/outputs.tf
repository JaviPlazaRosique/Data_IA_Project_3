output "db_password_secret_id" {
  description = "ID del secreto de la contrasena de la base de datos"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "jwt_secret_key_secret_id" {
  description = "ID del secreto de la clave JWT"
  value       = google_secret_manager_secret.jwt_secret_key.secret_id
}

output "ids_secretos" {
  description = "Mapa de secret_id por cada secreto creado (clave = nombre usado al crear, valor = secret_id en GCP)"
  value       = { for k, v in google_secret_manager_secret.secreto : k => v.secret_id }
}

output "google_places_key_string" {
  description = "Valor de la API Key de Google Places. Sensible — solo usar para almacenar en Secret Manager."
  value       = google_apikeys_key.google_places.key_string
  sensitive   = true
}

output "gemini_key_string" {
  description = "Valor de la API Key de Gemini. Sensible — solo usar para almacenar en Secret Manager."
  value       = google_apikeys_key.gemini.key_string
  sensitive   = true
}

output "nombre_pool" {
  description = "Nombre completo del pool"
  value       = google_iam_workload_identity_pool.github_pool.name
}

output "nombre_provider" {
  description = "Nombre completo del provider. Necesario para cada workflow de GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}
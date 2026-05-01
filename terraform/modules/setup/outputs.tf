output "google_places_key_string" {
  description = "Valor de la API Key de Google Places. Sensible — solo usar para almacenar en Secret Manager."
  value       = google_apikeys_key.google_places.key_string
  sensitive   = true
}

output "google_maps_key_string" {
  description = "Valor de la API Key de Google Maps JavaScript. Inyectar en public-config.json del frontend."
  value       = google_apikeys_key.google_maps.key_string
  sensitive   = true
}

output "firebase_api_key" {
  description = "API Key de la web app de Firebase."
  value       = data.google_firebase_web_app_config.portal.api_key
  sensitive   = true
}

output "firebase_auth_domain" {
  description = "Auth domain de Firebase (proyecto.firebaseapp.com)."
  value       = data.google_firebase_web_app_config.portal.auth_domain
}


output "nombre_pool" {
  description = "Nombre completo del pool"
  value       = google_iam_workload_identity_pool.github_pool.name
}

output "nombre_provider" {
  description = "Nombre completo del provider. Necesario para cada workflow de GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}
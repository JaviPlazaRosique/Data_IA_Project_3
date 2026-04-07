output "nombre_pool" {
  description = "Nombre completo del pool"
  value       = google_iam_workload_identity_pool.github_pool.name
}

output "nombre_provider" {
  description = "Nombre completo del provider. Necesario para cada workflow de GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}
output "nombre_repo_artifact" {
  description = "Nombre completo del repositorio de Artifact Registry"
  value       = google_artifact_registry_repository.repositorio_docker.name
}

output "id_repo_artifact" {
  description = "ID del repositorio de Artifact Registry"
  value       = google_artifact_registry_repository.repositorio_docker.repository_id
}
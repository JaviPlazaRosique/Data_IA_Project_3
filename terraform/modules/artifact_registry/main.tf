resource "google_artifact_registry_repository" "repositorio_docker" {
  project       = var.id_proyecto
  location      = var.region
  repository_id = var.id_repo_artifact
  format        = "DOCKER"
}
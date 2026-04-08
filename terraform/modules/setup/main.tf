resource "google_project_service" "apis" {
  for_each           = toset(var.servicios_gcp)
  service            = each.key
  disable_on_destroy = false
}

resource "google_iam_workload_identity_pool" "github_pool" {
  project                   = var.id_proyecto
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  project                            = var.id_proyecto
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.workflow"   = "assertion.workflow"
  }
  attribute_condition = "attribute.repository == '${var.usuario_github}/${var.repo_github}'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}
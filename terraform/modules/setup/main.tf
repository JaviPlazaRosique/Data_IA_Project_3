terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
    google-beta = {
      source = "hashicorp/google-beta"
    }
  }
}

resource "google_project_service" "apis" {
  for_each           = toset(var.servicios_gcp)
  service            = each.key
  disable_on_destroy = false
}

resource "google_apikeys_key" "google_places" {
  project      = var.id_proyecto
  name         = "places-api-key"
  display_name = "API Key para Google Places"

  restrictions {
    api_targets {
      service = "places.googleapis.com"
    }
  }

  depends_on = [
    google_project_service.apis
  ]
}

resource "google_apikeys_key" "google_maps" {
  project      = var.id_proyecto
  name         = "maps-js-api-key"
  display_name = "API Key para Google Maps JavaScript"

  restrictions {
    browser_key_restrictions {
      allowed_referrers = var.referidores_maps
    }
    api_targets {
      service = "maps-backend.googleapis.com"
    }
  }

  depends_on = [
    google_project_service.apis
  ]
}


resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.id_proyecto

  depends_on = [
    google_project_service.apis
  ]
}

resource "google_firebase_web_app" "portal" {
  provider     = google-beta
  project      = var.id_proyecto
  display_name = "Portal Usuarios"

  depends_on = [
    google_firebase_project.default
  ]
}

data "google_firebase_web_app_config" "portal" {
  provider   = google-beta
  web_app_id = google_firebase_web_app.portal.app_id
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
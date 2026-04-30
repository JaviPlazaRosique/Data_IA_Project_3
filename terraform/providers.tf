terraform {
  backend "gcs" {
    bucket = "backend-terraform-dataia-3-project3grupo3"
    prefix = "terraform/state"
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.21.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "2.8.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "4.1.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "2.7.0"
    }
  }
}

provider "google" {
  project               = var.id_proyecto
  region                = var.region
  user_project_override = true
}

data "google_client_config" "current" {}

provider "docker" {
  registry_auth {
    address  = "${var.region}-docker.pkg.dev"
    username = "oauth2accesstoken"
    password = data.google_client_config.current.access_token
  }
}

terraform {
  backend "gcs" {
    bucket = "estado-provisional-data-project-3"
    prefix = "terraform/state"
  }
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "7.21.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "2.8.0"
    }
  }
}

provider "google" {
  project               = var.id_proyecto
  region                = var.region
  user_project_override = true
}
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "7.21.0"
    }
  }
}

provider "google" {
  project               = var.id_proyecto
  region                = var.region
  user_project_override = true
}
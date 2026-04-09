resource "google_cloud_run_v2_service" "portal_api" {
  name                = var.service_name
  project             = var.id_proyecto
  location            = var.region
  deletion_protection = false

  template {
    service_account = var.service_account_email

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.image

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "CORS_ORIGINS"
        value = var.cors_origins
      }
      env {
        name  = "DB_HOST"
        value = var.db_private_ip
      }
      env {
        name  = "DB_NAME"
        value = var.db_name
      }
      env {
        name  = "DB_USER"
        value = var.db_user
      }
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = var.db_password_secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "JWT_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = var.jwt_secret_key_secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      # Image is managed by CI/CD after initial provisioning
      template[0].containers[0].image,
    ]
  }
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.id_proyecto
  location = var.region
  name     = google_cloud_run_v2_service.portal_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

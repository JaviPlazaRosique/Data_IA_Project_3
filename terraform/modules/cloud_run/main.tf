terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

resource "docker_image" "imagen" {
  name  = "${var.region}-docker.pkg.dev/${var.id_proyecto}/${var.nombre_repo_artifact}/api:latest"
  build {
    context    = var.ruta_contexto_docker
    dockerfile = "Dockerfile"
    platform   = "linux/amd64"
  }
}

resource "docker_registry_image" "push" {
  name          = docker_image.imagen.name
  keep_remotely = true

  lifecycle {
    ignore_changes = all
  }

  depends_on = [
    docker_image.imagen
  ]
}

resource "google_cloud_run_v2_service" "service" {
  name                = var.nombre_servicio
  project             = var.id_proyecto
  location            = var.region
  deletion_protection = var.proteccion_borrado

  template {
    service_account = var.email_cuenta_servicio

    dynamic "vpc_access" {
      for_each = var.id_conector_vpc != null ? [1] : []
      content {
        connector = var.id_conector_vpc
        egress    = var.egress_vpc
      }
    }

    containers {
      image = docker_registry_image.push.name

      dynamic "env" {
        for_each = var.variables_entorno
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secretos_entorno
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memoria
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count    = var.acceso_publico ? 1 : 0
  project  = var.id_proyecto
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

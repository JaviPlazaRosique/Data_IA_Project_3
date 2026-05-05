terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

resource "docker_image" "imagen" {
  name = "${var.region}-docker.pkg.dev/${var.id_proyecto}/${var.nombre_repo_artifact}/${var.nombre_imagen}:latest"
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

resource "google_cloud_run_v2_job" "job" {
  name                = var.nombre_job
  project             = var.id_proyecto
  location            = var.region
  deletion_protection = var.proteccion_borrado

  template {
    template {
      service_account = var.email_cuenta_servicio
      timeout         = var.timeout
      max_retries     = var.max_retries

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
  }

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
    ]
  }
}

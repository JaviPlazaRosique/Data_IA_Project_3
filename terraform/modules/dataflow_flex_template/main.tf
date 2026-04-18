terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

resource "docker_image" "launcher" {
  name = "${var.region}-docker.pkg.dev/${var.id_proyecto}/${var.nombre_repo_artifact}/${var.nombre_imagen}:latest"
  build {
    context    = var.ruta_contexto_docker
    dockerfile = "Dockerfile"
    platform   = "linux/amd64"
  }
}

resource "docker_registry_image" "push" {
  name          = docker_image.launcher.name
  keep_remotely = true

  lifecycle {
    ignore_changes = all
  }

  depends_on = [
    docker_image.launcher
  ]
}

resource "google_storage_bucket_object" "spec" {
  name    = var.ruta_spec
  bucket  = var.nombre_bucket_spec
  content = jsonencode({
    image = docker_image.launcher.name
    sdkInfo = {
      language = "PYTHON"
    }
    metadata = jsondecode(file(var.ruta_metadata))
  })
  content_type = "application/json"

  lifecycle {
    ignore_changes = all
  }

  depends_on = [
    docker_registry_image.push
  ]
}

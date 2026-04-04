resource "google_storage_bucket" "bucket_web" {
  name          = var.nombre_bucket
  location      = var.region
  force_destroy = true
  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}

resource "google_storage_bucket_iam_binding" "web_publica" {
  bucket  = google_storage_bucket.bucket_web.name
  role    = "roles/storage.objectViewer"
  members = ["allUsers"]
}

resource "null_resource" "compilar_web" {
  provisioner "local-exec" {
    command = <<-EOT
      cd ${var.ruta_recurso_web}
      npm install
      npm run build
    EOT
  }
  depends_on = [
    google_storage_bucket_iam_binding.web_publica
  ]
}

locals {
  tipos_archivos = {
    "html" = "text/html"
    "css"  = "text/css"
    "js"   = "application/javascript"
    "json" = "application/json"
    "png"  = "image/png"
    "jpg"  = "image/jpeg"
    "svg"  = "image/svg+xml"
    "ico"  = "image/x-icon"
    "txt"  = "text/plain"
  }
}

resource "google_storage_bucket_object" "subir_archivos" {
  for_each     = fileset("${var.ruta_recurso_web}/dist", "**")
  name         = each.value
  bucket       = google_storage_bucket.bucket_web.name
  source       = "${var.ruta_recurso_web}/dist/${each.value}"
  content_type = lookup(
    local.tipos_archivos,
    split(".", each.value)[length(split(".", each.value)) - 1],
    "application/octet-stream"
  )
  depends_on = [
    null_resource.compilar_web
  ]
}

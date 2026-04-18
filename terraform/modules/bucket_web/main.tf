resource "google_storage_bucket" "bucket_web" {
  name                        = var.nombre_bucket
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}

resource "google_storage_bucket_iam_binding" "web_publica" {
  bucket  = google_storage_bucket.bucket_web.name
  role    = "roles/storage.objectViewer"
  members = [
    "allUsers"
  ]
}

resource "null_resource" "compilar_subir_web" {
  provisioner "local-exec" {
    command = <<-EOT
      cd ${var.ruta_recurso_web}
      npm install
      npm run build
      gcloud config set project ${var.id_proyecto}
      gcloud storage rsync ./dist/ gs://${google_storage_bucket.bucket_web.name} --recursive
    EOT
  }
  depends_on = [
    google_storage_bucket_iam_binding.web_publica
  ]
}
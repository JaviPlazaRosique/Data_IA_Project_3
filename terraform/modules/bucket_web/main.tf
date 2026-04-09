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

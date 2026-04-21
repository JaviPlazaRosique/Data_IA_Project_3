output "url_web" {
  description = "Enlace en el que se encuentra alojada la web"
  value       = "https://${google_storage_bucket.bucket_web.name}.storage.googleapis.com"
}

output "nombre_bucket" {
  description = "Nombre del bucket de GCS"
  value       = google_storage_bucket.bucket_web.name
}
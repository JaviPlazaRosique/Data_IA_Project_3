output "url_web" {
  description = "Enlace en el que se encuentra alojada la web"
  value       = "http://${google_storage_bucket.bucket_web.name}.storage.googleapis.com"
}
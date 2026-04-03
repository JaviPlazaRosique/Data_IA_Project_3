output "url_web" {
  description = "Enlace en el que se encuentra alojada la web"
  value       = "https://storage.googleapis.com/${google_storage_bucket.bucket_web.name}/index.html"
}
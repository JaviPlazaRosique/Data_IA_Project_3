output "nombre" {
  description = "Nombre del bucket creado."
  value       = google_storage_bucket.bucket.name
}

output "url" {
  description = "URL del bucket en formato gs://nombre."
  value       = google_storage_bucket.bucket.url
}

output "id" {
  description = "ID del recurso del bucket."
  value       = google_storage_bucket.bucket.id
}

output "uri_imagen" {
  description = "URI completa de la imagen launcher en Artifact Registry"
  value       = docker_image.launcher.name
}

output "spec_gcs_path" {
  description = "Ruta gs:// al spec JSON del Flex Template"
  value       = "gs://${var.nombre_bucket_spec}/${var.ruta_spec}"
}

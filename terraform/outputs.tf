output "url_frontend_usuarios" {
  description = "URL de la aplicación web de los usuarios alojada en GCS."
  value       = module.frontend_usuarios.url_web
}

output "wif_provider" {
  description = "Provider común para todos los workflows"
  value       = module.setup.nombre_provider
}
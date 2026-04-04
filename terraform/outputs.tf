output "url_frontend_usuarios" {
  description = "URL de la aplicación web de los usuarios alojada en GCS."
  value       = module.frontend_usuarios.url_web
}

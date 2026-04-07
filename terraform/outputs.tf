output "url_frontend_usuarios" {
  description = "URL de la aplicación web de los usuarios alojada en GCS."
  value       = module.frontend_usuarios.url_web
}

output "wif_provider" {
  description = "Provider común para todos los workflows"
  value       = module.setup.nombre_provider
}

output "frontend_usuarios_cuenta_servicio" {
  description = "Cuenta de servicio del CI/CD del frontend de los usuarios"
  value       = module.cicd_frontend_usuarios.email_cuenta_servicio
}
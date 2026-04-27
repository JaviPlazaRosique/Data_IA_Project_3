output "url_frontend_usuarios" {
  description = "URL de la aplicación web de los usuarios alojada en GCS. Usar este valor como GitHub Secret CORS_ORIGINS."
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

output "portal_api_url" {
  description = "URL del Portal API en Cloud Run"
  value       = module.cloud_run_portal_api.service_url
}

output "cloudsql_connection_name" {
  description = "Nombre de conexion de CloudSQL (proyecto:region:instancia)"
  value       = module.cloudsql_portal.connection_name
}

output "cloudsql_private_ip" {
  description = "IP privada de CloudSQL"
  value       = module.cloudsql_portal.private_ip
}

output "backend_portal_api_cuenta_servicio" {
  description = "Cuenta de servicio del CI/CD del backend Portal API (GitHub Secret: BACKEND_PORTAL_API_CUENTA_SERVICIO)"
  value       = module.cicd_backend_portal_api.email_cuenta_servicio
}

output "ingesta_eventos_cuenta_servicio" {
  description = "Cuenta de servicio del CI/CD del job de ingestión de eventos (GitHub Secret: INGESTA_EVENTOS_CUENTA_SERVICIO)"
  value       = module.cicd_ingesta_eventos.email_cuenta_servicio
}

output "ingesta_eventos_job_id" {
  description = "ID completo del Cloud Run Job de ingestión de eventos"
  value       = module.ingesta_eventos_job.job_id
}

output "migrate_bd_cuenta_servicio" {
  description = "Cuenta de servicio del CI/CD de migraciones de base de datos (GitHub Secret: MIGRATE_BD_CUENTA_SERVICIO)"
  value       = module.cicd_migrate_bd.email_cuenta_servicio
}

output "host_bd" {
  description = "IP privada de CloudSQL (GitHub Secret: HOST_BD)"
  value       = module.cloudsql_portal.private_ip
}

output "nombre_bd" {
  description = "Nombre de la base de datos (GitHub Secret: NOMBRE_BD)"
  value       = module.cloudsql_portal.database_name
}

output "usuario_bd" {
  description = "Usuario de la base de datos (GitHub Secret: USUARIO_BD)"
  value       = module.cloudsql_portal.db_user
}
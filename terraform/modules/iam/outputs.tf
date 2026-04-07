output "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio creada"
  value       = google_service_account.cuenta_servicio.email
}

output "nombre_cuenta_servicio" {
  description = "Nombre de la cuenta de servicio creada"
  value       = google_service_account.cuenta_servicio.name
}
output "instance_name" {
  description = "Nombre de la instancia de CloudSQL"
  value       = google_sql_database_instance.instance.name
}

output "connection_name" {
  description = "Nombre de conexion de CloudSQL (proyecto:region:instancia)"
  value       = google_sql_database_instance.instance.connection_name
}

output "private_ip" {
  description = "IP privada de la instancia de CloudSQL"
  value       = google_sql_database_instance.instance.private_ip_address
}

output "database_name" {
  description = "Nombre de la base de datos"
  value       = google_sql_database.database.name
}

output "db_user" {
  description = "Usuario de la base de datos"
  value       = google_sql_user.api_user.name
}

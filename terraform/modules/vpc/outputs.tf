output "network_id" {
  description = "ID de la red VPC"
  value       = google_compute_network.vpc.id
}

output "network_name" {
  description = "Nombre de la red VPC"
  value       = google_compute_network.vpc.name
}

output "vpc_connector_id" {
  description = "ID del VPC Access Connector para Cloud Run"
  value       = google_vpc_access_connector.connector.id
}

output "private_vpc_connection" {
  description = "Conexion de peering privado con los servicios de Google"
  value       = google_service_networking_connection.private_vpc_connection.id
}

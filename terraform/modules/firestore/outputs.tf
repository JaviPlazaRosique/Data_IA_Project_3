output "nombre" {
  description = "Nombre de la base de datos de Firestore creada."
  value       = google_firestore_database.base_datos.name
}

output "id" {
  description = "ID completo del recurso de Firestore."
  value       = google_firestore_database.base_datos.id
}

output "ubicacion" {
  description = "Location donde está desplegada la base de datos."
  value       = google_firestore_database.base_datos.location_id
}

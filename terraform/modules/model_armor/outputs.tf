output "id_template" {
  description = "ID corto de la plantilla creada (lo que el backend consume como MODEL_ARMOR_TEMPLATE_ID)"
  value       = google_model_armor_template.plantilla.template_id
}

output "nombre_template" {
  description = "Resource name completo de la plantilla (projects/.../locations/.../templates/...)"
  value       = google_model_armor_template.plantilla.name
}

output "location" {
  description = "Región donde está creada la plantilla (lo que el backend consume como MODEL_ARMOR_LOCATION)"
  value       = google_model_armor_template.plantilla.location
}

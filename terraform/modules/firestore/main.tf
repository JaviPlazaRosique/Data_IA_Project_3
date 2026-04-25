resource "google_firestore_database" "base_datos" {
  project                 = var.id_proyecto
  name                    = var.nombre_base_datos
  location_id             = var.ubicacion
  type                    = "FIRESTORE_NATIVE"
  delete_protection_state = var.proteccion_borrado ? "DELETE_PROTECTION_ENABLED" : "DELETE_PROTECTION_DISABLED"
  deletion_policy         = var.politica_borrado_terraform
}

resource "google_firestore_index" "indices_compuestos" {
  for_each = {
    for idx in var.indices_compuestos :
    "${idx.coleccion}__${join("_", [for c in idx.campos : "${c.field_path}-${c.order}"])}" => idx
  }

  project    = var.id_proyecto
  database   = google_firestore_database.base_datos.name
  collection = each.value.coleccion

  dynamic "fields" {
    for_each = each.value.campos
    content {
      field_path = fields.value.field_path
      order      = fields.value.order
    }
  }

  depends_on = [
    google_firestore_database.base_datos
  ]
}

resource "google_firestore_field" "ttl" {
  for_each = {
    for politica in var.politicas_ttl :
    "${politica.coleccion}__${politica.campo_expiracion}" => politica
  }

  project    = var.id_proyecto
  database   = google_firestore_database.base_datos.name
  collection = each.value.coleccion
  field      = each.value.campo_expiracion

  ttl_config {}

  depends_on = [
    google_firestore_database.base_datos
  ]
}

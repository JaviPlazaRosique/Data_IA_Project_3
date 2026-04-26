resource "google_bigquery_dataset" "dataset" {
  project                    = var.id_proyecto
  dataset_id                 = var.id_dataset
  friendly_name              = var.nombre_dataset
  location                   = var.ubicacion
  delete_contents_on_destroy = var.eliminar_contenido_al_borrar
}

resource "google_bigquery_dataset_iam_member" "permisos" {
  for_each = { for b in var.iam_members : "${b.role}/${b.member}" => b }

  project    = var.id_proyecto
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  role       = each.value.role
  member     = each.value.member
}

resource "google_bigquery_table" "tabla" {
  for_each = { for tabla in var.tablas : tabla.id_tabla => tabla }

  project             = var.id_proyecto
  dataset_id          = google_bigquery_dataset.dataset.dataset_id
  table_id            = each.value.id_tabla
  schema              = each.value.schema_json
  deletion_protection = var.proteccion_borrado

  dynamic "time_partitioning" {
    for_each = each.value.campo_particion != null ? [1] : []
    content {
      type  = "DAY"
      field = each.value.campo_particion
    }
  }
}

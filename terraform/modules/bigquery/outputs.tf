output "id_dataset" {
  description = "ID del dataset de BigQuery creado."
  value       = google_bigquery_dataset.dataset.dataset_id
}

output "ids_tablas" {
  description = "Mapa de id_tabla → table_id para cada tabla creada."
  value       = { for k, v in google_bigquery_table.tabla : k => v.table_id }
}

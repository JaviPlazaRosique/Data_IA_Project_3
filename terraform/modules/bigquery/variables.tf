variable "id_proyecto" {
  description = "ID del proyecto de GCP."
  type        = string
}

variable "id_dataset" {
  description = "ID del dataset de BigQuery (sin espacios ni guiones)."
  type        = string
}

variable "nombre_dataset" {
  description = "Nombre descriptivo del dataset visible en la consola de GCP."
  type        = string
  default     = ""
}

variable "ubicacion" {
  description = "Ubicación del dataset (ej: EU, US, europe-west1)."
  type        = string
  default     = "EU"
}

variable "proteccion_borrado" {
  description = "Protege las tablas de eliminación accidental desde Terraform."
  type        = bool
  default     = false
}

variable "eliminar_contenido_al_borrar" {
  description = "Permite eliminar el dataset aunque contenga tablas al ejecutar 'terraform destroy'."
  type        = bool
  default     = false
}

variable "tablas" {
  description = <<-EOT
    Lista de tablas a crear en el dataset. Cada tabla admite:
      - id_tabla         (string,  requerido): identificador de la tabla.
      - schema_json      (string,  requerido): schema en formato JSON (usar jsonencode o file()).
      - campo_particion  (string,  opcional):  campo DATE/TIMESTAMP para particionar por día. null para desactivar.
  EOT
  type = list(object({
    id_tabla        = string
    schema_json     = string
    campo_particion = optional(string, null)
  }))
  default = []
}


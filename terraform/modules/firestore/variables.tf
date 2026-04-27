variable "id_proyecto" {
  description = "ID del proyecto de GCP."
  type        = string
}

variable "nombre_base_datos" {
  description = "Nombre de la base de datos de Firestore. Usar '(default)' para la base de datos principal del proyecto."
  type        = string
  default     = "(default)"
}

variable "ubicacion" {
  description = <<-EOT
    Location ID de Firestore. Multirregionales recomendadas:
      - "eur3"  → Europa (Bélgica + Países Bajos)
      - "nam5"  → EE.UU. (Iowa + Carolina del Sur)
    Regiones simples también válidas, ej: "europe-west1".
  EOT
  type        = string
  default     = "eur3"
}

variable "proteccion_borrado" {
  description = "Activa la protección de borrado en GCP para evitar eliminar la base de datos accidentalmente."
  type        = bool
  default     = false
}

variable "politica_borrado_terraform" {
  description = <<-EOT
    Comportamiento de Terraform al ejecutar 'destroy':
      - "DELETE"  → Terraform elimina la base de datos (requiere proteccion_borrado = false).
      - "ABANDON" → Terraform elimina el recurso del estado pero no lo borra en GCP.
  EOT
  type        = string
  default     = "DELETE"

  validation {
    condition     = contains(["DELETE", "ABANDON"], var.politica_borrado_terraform)
    error_message = "El valor debe ser 'DELETE' o 'ABANDON'."
  }
}

variable "indices_compuestos" {
  description = <<-EOT
    Lista de índices compuestos de Firestore.
    Cada entrada admite:
      - coleccion (string, requerido): nombre de la colección.
      - campos    (list, requerido): lista de campos en orden, cada uno con
          - field_path (string)
          - order      (string: "ASCENDING" | "DESCENDING")
    Ejemplo:
      indices_compuestos = [
        {
          coleccion = "eventos"
          campos = [
            { field_path = "fecha",     order = "ASCENDING" },
            { field_path = "fecha_utc", order = "ASCENDING" },
          ]
        }
      ]
  EOT
  type = list(object({
    coleccion = string
    campos = list(object({
      field_path = string
      order      = string
    }))
  }))
  default = []
}

variable "politicas_ttl" {
  description = <<-EOT
    Lista de políticas TTL para borrado automático de documentos por colección.
    Firestore elimina cada documento cuando el campo timestamp indicado vence.
    Cada entrada admite:
      - coleccion          (string, requerido): nombre de la colección.
      - campo_expiracion   (string, requerido): campo timestamp del documento con la fecha de expiración.
    Ejemplo:
      politicas_ttl = [
        { coleccion = "recintos", campo_expiracion = "fecha_expiracion" }
      ]
  EOT
  type = list(object({
    coleccion        = string
    campo_expiracion = string
  }))
  default = []
}

variable "nombre" {
  description = "Nombre único global del bucket de GCS."
  type        = string
}

variable "id_proyecto" {
  description = "ID del proyecto de GCP donde se creará el bucket."
  type        = string
}

variable "ubicacion" {
  description = "Ubicación del bucket (ej: EU, US, EUROPE-WEST1)."
  type        = string
  default     = "EU"
}

variable "clase_almacenamiento" {
  description = "Clase de almacenamiento del bucket (STANDARD, NEARLINE, COLDLINE, ARCHIVE)."
  type        = string
  default     = "STANDARD"

  validation {
    condition     = contains(["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"], var.clase_almacenamiento)
    error_message = "La clase de almacenamiento debe ser STANDARD, NEARLINE, COLDLINE o ARCHIVE."
  }
}

variable "versionado" {
  description = "Activa el versionado de objetos en el bucket."
  type        = bool
  default     = false
}

variable "forzar_eliminacion" {
  description = "Permite eliminar el bucket aunque contenga objetos (útil en entornos no productivos)."
  type        = bool
  default     = true
}

variable "reglas_ciclo_vida" {
  description = <<-EOT
    Lista de reglas de ciclo de vida. Cada regla admite:
      - tipo_accion       (string, requerido): "Delete" o "SetStorageClass"
      - clase_destino     (string, opcional): clase destino si tipo_accion es "SetStorageClass"
      - edad_dias         (number, opcional): días de antigüedad del objeto
      - versiones_recientes (number, opcional): número de versiones más recientes a conservar
      - estado_objeto     (string, opcional): "LIVE", "ARCHIVED" o "ANY"
  EOT
  type        = list(map(string))
  default     = []
}

variable "periodo_retencion_segundos" {
  description = "Periodo mínimo de retención de objetos en segundos. null para desactivar."
  type        = number
  default     = null
}

variable "etiquetas" {
  description = "Mapa de etiquetas (labels) a aplicar al bucket."
  type        = map(string)
  default     = {}
}

variable "id_proyecto" {
  description = "ID del proyecto de GCP donde se crea el topic."
  type        = string
}

variable "nombre_topic" {
  description = "Nombre del topic de Pub/Sub."
  type        = string
}

variable "publicadores" {
  description = <<-EOT
    Lista de service accounts (email) a los que se les concede roles/pubsub.publisher
    sobre este topic. Ejemplo: ["portal-api-sa@proyecto.iam.gserviceaccount.com"].
  EOT
  type        = list(string)
  default     = []
}

variable "etiquetas" {
  description = "Labels opcionales aplicadas al topic."
  type        = map(string)
  default     = {}
}

variable "duracion_retencion" {
  description = <<-EOT
    Tiempo de retención de mensajes en el topic (formato duración Go, ej: "604800s" para 7 días).
    Cadena vacía deja el valor por defecto del proveedor (sin retención persistente).
  EOT
  type        = string
  default     = ""
}

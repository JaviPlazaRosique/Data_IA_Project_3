variable "id_proyecto" {
  description = "ID del proyecto de GCP donde se crean los recursos."
  type        = string
}

variable "nombre_topic" {
  description = "Nombre del topic principal de Pub/Sub."
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
    Tiempo de retención de mensajes en el topic principal (formato duración Go, ej: "604800s").
    Cadena vacía deja el valor por defecto del proveedor.
  EOT
  type        = string
  default     = ""
}

variable "habilitar_dlq" {
  description = "Si true, crea el topic DLQ, sus suscripciones y la política de dead-letter."
  type        = bool
  default     = false
}

variable "duracion_retencion_dlq" {
  description = "Tiempo de retención del topic DLQ (formato duración Go, ej: '604800s' para 7 días)."
  type        = string
  default     = "604800s"
}

variable "nombre_suscripcion" {
  description = "Nombre de la suscripción principal. Si está vacío no se crea suscripción."
  type        = string
  default     = ""
}

variable "ack_deadline_seconds" {
  description = "Tiempo máximo de acknowledgement en segundos para las suscripciones."
  type        = number
  default     = 60
}

variable "message_retention_duration_suscripcion" {
  description = "Duración de retención de mensajes en la suscripción principal (formato duración Go)."
  type        = string
  default     = "604800s"
}

variable "minimum_backoff" {
  description = "Backoff mínimo del retry policy de la suscripción principal."
  type        = string
  default     = "10s"
}

variable "maximum_backoff" {
  description = "Backoff máximo del retry policy de la suscripción principal."
  type        = string
  default     = "600s"
}

variable "max_delivery_attempts" {
  description = "Número máximo de intentos de entrega antes de enviar al DLQ."
  type        = number
  default     = 5
}

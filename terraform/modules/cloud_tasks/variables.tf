variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP donde se crea la cola"
  type        = string
}

variable "nombre_cola" {
  description = "Nombre de la cola de Cloud Tasks"
  type        = string
}

variable "max_despachos_por_segundo" {
  description = "Maximo de tareas despachadas por segundo desde la cola"
  type        = number
  default     = 500
}

variable "max_despachos_concurrentes" {
  description = "Maximo de tareas ejecutandose en paralelo en cualquier momento"
  type        = number
  default     = 1000
}

variable "max_intentos" {
  description = "Numero maximo de intentos por tarea. Usa -1 para intentos ilimitados."
  type        = number
  default     = 5
}

variable "duracion_maxima_reintento" {
  description = "Tiempo maximo total que se reintentara una tarea (formato Duration, p.ej. 3600s)"
  type        = string
  default     = "3600s"
}

variable "espera_minima_reintento" {
  description = "Espera minima entre reintentos (formato Duration, p.ej. 10s)"
  type        = string
  default     = "10s"
}

variable "espera_maxima_reintento" {
  description = "Espera maxima entre reintentos (formato Duration, p.ej. 300s)"
  type        = string
  default     = "300s"
}

variable "max_duplicaciones_espera" {
  description = "Numero maximo de veces que se duplica la espera entre reintentos (backoff exponencial)"
  type        = number
  default     = 4
}

variable "ratio_muestreo_logs" {
  description = "Proporcion de tareas cuyos logs se envian a Cloud Logging (0.0 a 1.0)"
  type        = number
  default     = 1.0
  validation {
    condition     = var.ratio_muestreo_logs >= 0 && var.ratio_muestreo_logs <= 1
    error_message = "El ratio de muestreo debe estar entre 0.0 y 1.0."
  }
}

variable "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio usada para autenticar las tareas HTTP mediante OIDC. Si es null, no se configura autenticacion a nivel de cola."
  type        = string
  default     = null
}

variable "audiencia_oidc" {
  description = "Audiencia del token OIDC. Normalmente la URL base del servicio destino."
  type        = string
  default     = null
}

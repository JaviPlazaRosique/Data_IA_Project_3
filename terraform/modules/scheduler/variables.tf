variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Región del job de Cloud Scheduler y del endpoint HTTP destino"
  type        = string
}

variable "nombre_job" {
  description = "Nombre del job de Cloud Scheduler"
  type        = string
}

variable "descripcion" {
  description = "Descripción del job de Cloud Scheduler"
  type        = string
  default     = ""
}

variable "cron" {
  description = "Expresión cron (formato unix-cron) que define cuándo se dispara el job"
  type        = string
}

variable "zona_horaria" {
  description = "Zona horaria para interpretar la expresión cron (ej: Europe/Madrid)"
  type        = string
  default     = "Europe/Madrid"
}

variable "url_destino" {
  description = "URL HTTP/HTTPS que dispara el job"
  type        = string
}

variable "metodo_http" {
  description = "Método HTTP usado al disparar el job (GET, POST, PUT, PATCH, DELETE)"
  type        = string
  default     = "POST"
}

variable "cuerpo_peticion" {
  description = "Cuerpo de la petición HTTP. Se codifica en base64 automáticamente."
  type        = string
  default     = null
}

variable "cabeceras" {
  description = "Cabeceras HTTP adicionales"
  type        = map(string)
  default     = {}
}

variable "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio usada para autenticar la petición mediante OAuth"
  type        = string
}

variable "alcance_oauth" {
  description = "Scope OAuth que se pide al generar el token para la petición"
  type        = string
  default     = "https://www.googleapis.com/auth/cloud-platform"
}

variable "reintentos" {
  description = "Número de reintentos ante error"
  type        = number
  default     = 1
}

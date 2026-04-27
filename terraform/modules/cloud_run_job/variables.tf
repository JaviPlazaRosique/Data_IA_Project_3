variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type        = string
}

variable "nombre_job" {
  description = "Nombre del Cloud Run Job"
  type        = string
}

variable "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio que ejecutara el job"
  type        = string
}

variable "nombre_repo_artifact" {
  description = "Nombre del repositorio de Artifact Registry"
  type        = string
}

variable "nombre_imagen" {
  description = "Nombre de la imagen del job dentro del repositorio"
  type        = string
}

variable "ruta_contexto_docker" {
  description = "Ruta al contexto de build de Docker"
  type        = string
}

variable "variables_entorno" {
  description = "Variables de entorno en texto plano para el contenedor"
  type        = map(string)
  default     = {}
}

variable "secretos_entorno" {
  description = "Variables de entorno cuyo valor proviene de Secret Manager"
  type = map(object({
    secret  = string
    version = string
  }))
  default = {}
}

variable "cpu" {
  description = "Limite de CPU para el contenedor"
  type        = string
  default     = "1"
}

variable "memoria" {
  description = "Limite de memoria para el contenedor"
  type        = string
  default     = "512Mi"
}

variable "timeout" {
  description = "Timeout maximo de ejecucion (formato Duration, p.ej. 3600s)"
  type        = string
  default     = "3600s"
}

variable "max_retries" {
  description = "Numero maximo de reintentos por ejecucion"
  type        = number
  default     = 1
}

variable "proteccion_borrado" {
  description = "Habilita proteccion contra borrado del job"
  type        = bool
  default     = false
}

variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region en la que se despliegan los recursos dentro de GCP"
  type        = string
  default     = "europe-west1"
}

variable "repo_github" {
  description = "Repositorio de GitHub"
  type        = string
}

variable "usuario_github" {
  description = "Usuario de GitHub (debe tener permisos sobre el repo)"
  type        = string
}

variable "nivel_bd" {
  description = "Tier de la maquina de CloudSQL"
  type        = string
  default     = "db-f1-micro"
}

variable "tipo_disponibilidad_bd" {
  description = "Tipo de disponibilidad de CloudSQL: ZONAL o REGIONAL"
  type        = string
  default     = "ZONAL"
}

variable "proteccion_borrado" {
  description = "Proteger CloudSQL de eliminacion accidental"
  type        = bool
  default     = false
}

variable "contrasena_bd" {
  description = "Contraseña del usuario api_user en CloudSQL"
  type        = string
  sensitive   = true
}

variable "clave_jwt" {
  description = "Clave secreta para firmar tokens JWT (minimo 32 caracteres)"
  type        = string
  sensitive   = true
}

variable "ticketmaster_apikey" {
  description = "API-Key de la API de TicketMaster"
  type        = string
  sensitive   = true
}

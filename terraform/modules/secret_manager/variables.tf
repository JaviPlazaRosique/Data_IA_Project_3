variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "db_password" {
  description = "Contrasena de la base de datos"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "Clave secreta para firmar los tokens JWT"
  type        = string
  sensitive   = true
}

variable "cloud_run_sa_email" {
  description = "Email de la cuenta de servicio de Cloud Run que necesita acceder a los secretos"
  type        = string
}

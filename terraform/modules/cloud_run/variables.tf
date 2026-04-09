variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type        = string
}

variable "service_name" {
  description = "Nombre del servicio de Cloud Run"
  type        = string
  default     = "portal-api"
}

variable "image" {
  description = "Imagen Docker del contenedor"
  type        = string
}

variable "service_account_email" {
  description = "Email de la cuenta de servicio que ejecutara el servicio Cloud Run"
  type        = string
}

variable "vpc_connector_id" {
  description = "ID del VPC Access Connector"
  type        = string
}

variable "db_private_ip" {
  description = "IP privada de CloudSQL"
  type        = string
}

variable "db_name" {
  description = "Nombre de la base de datos"
  type        = string
}

variable "db_user" {
  description = "Usuario de la base de datos"
  type        = string
}

variable "db_password_secret_id" {
  description = "ID del secreto de Secret Manager con la contrasena de la BD"
  type        = string
  default     = "portal-api-db-password"
}

variable "jwt_secret_key_secret_id" {
  description = "ID del secreto de Secret Manager con la clave JWT"
  type        = string
  default     = "portal-api-jwt-secret-key"
}

variable "cors_origins" {
  description = "Origenes permitidos para CORS (separados por comas)"
  type        = string
}

variable "environment" {
  description = "Entorno de ejecucion (development/production)"
  type        = string
  default     = "production"
}

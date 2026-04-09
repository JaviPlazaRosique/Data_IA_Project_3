variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type        = string
}

variable "network_id" {
  description = "ID de la red VPC privada"
  type        = string
}

variable "private_vpc_connection" {
  description = "Dependencia de la conexion de peering privado"
  type        = string
}

variable "db_instance_name" {
  description = "Nombre de la instancia de CloudSQL"
  type        = string
  default     = "electric-curator-db"
}

variable "db_tier" {
  description = "Tier de la maquina de CloudSQL"
  type        = string
  default     = "db-f1-micro"
}

variable "db_availability_type" {
  description = "ZONAL o REGIONAL"
  type        = string
  default     = "ZONAL"
}

variable "deletion_protection" {
  description = "Proteger la instancia de eliminacion accidental"
  type        = bool
  default     = false
}

variable "database_name" {
  description = "Nombre de la base de datos"
  type        = string
  default     = "electric_curator"
}

variable "db_user" {
  description = "Usuario de la base de datos para la API"
  type        = string
  default     = "api_user"
}

variable "db_password" {
  description = "Contrasena del usuario de la base de datos"
  type        = string
  sensitive   = true
}

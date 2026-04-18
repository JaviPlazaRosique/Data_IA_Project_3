variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type        = string
}

variable "id_red" {
  description = "ID de la red VPC privada"
  type        = string
}

variable "conexion_vpc_privada" {
  description = "Dependencia de la conexion de peering privado (fuerza el orden de creacion)"
  type        = string
}

variable "nombre_instancia_bd" {
  description = "Nombre de la instancia de CloudSQL"
  type        = string
}

variable "nombre_base_datos" {
  description = "Nombre de la base de datos"
  type        = string
}

variable "usuario_bd" {
  description = "Usuario de la base de datos"
  type        = string
  default     = "app_user"
}

variable "contrasena_bd" {
  description = "Contrasena del usuario de la base de datos"
  type        = string
  sensitive   = true
}

variable "version_bd" {
  description = "Version del motor de base de datos (e.g. POSTGRES_15, MYSQL_8_0)"
  type        = string
  default     = "POSTGRES_15"
}

variable "nivel_bd" {
  description = "Tier de la maquina de CloudSQL"
  type        = string
  default     = "db-f1-micro"
}

variable "tipo_disponibilidad_bd" {
  description = "Tipo de disponibilidad: ZONAL o REGIONAL"
  type        = string
  default     = "ZONAL"
}

variable "proteccion_borrado" {
  description = "Proteger la instancia de eliminacion accidental"
  type        = bool
  default     = false
}

variable "ipv4_habilitado" {
  description = "Habilita IP publica en la instancia de CloudSQL"
  type        = bool
  default     = false
}

variable "backup_habilitado" {
  description = "Habilita las copias de seguridad automaticas"
  type        = bool
  default     = true
}

variable "hora_inicio_backup" {
  description = "Hora de inicio de las copias de seguridad (formato HH:MM)"
  type        = string
  default     = "03:00"
}

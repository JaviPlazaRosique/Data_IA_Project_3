variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "secretos" {
  description = "Mapa de secretos a crear: clave = secret_id, valor = contenido del secreto"
  type        = map(string)
}

variable "cuentas_servicio_acceso" {
  description = "Lista de emails de cuentas de servicio con acceso de lectura a todos los secretos"
  type        = list(string)
  default     = []
}

variable "nombres_cuentas_servicio" {
  description = "Lista de identificadores estaticos de cuentas de servicio (para claves de for_each)"
  type        = list(string)
  default     = []
}

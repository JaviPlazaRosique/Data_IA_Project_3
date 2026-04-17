variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "secretos" {
  description = "Mapa de secretos a crear: clave = secret_id, valor = contenido del secreto"
  type        = map(string)
}


variable "id_sa" {
  description = "ID de la cuenta de servicio"
  type        = string
}

variable "nombre_despliege" {
  description = "Nombre de despliegue de la cuenta de servicio"
  type        = string
}

variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "sa_roles" {
  description = "Roles de IAM, que tendrá la cuenta de servicio"
  type        = list(string)
  default = []
}
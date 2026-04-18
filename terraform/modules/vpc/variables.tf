variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type        = string
}

variable "nombre_vpc" {
  description = "Nombre de la red VPC"
  type        = string
  default     = "vpc-portal"
}

variable "nombre_conector" {
  description = "Nombre del VPC Access Connector para Cloud Run"
  type        = string
  default     = "vpc-connector"
}

variable "cidr_conector" {
  description = "CIDR del rango IP del conector (debe ser /28, fuera del rango de la VPC)"
  type        = string
  default     = "10.8.0.0/28"
}

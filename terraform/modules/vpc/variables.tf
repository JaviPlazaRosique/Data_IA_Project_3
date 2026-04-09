variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type        = string
}

variable "vpc_name" {
  description = "Nombre de la red VPC"
  type        = string
  default     = "electric-curator-vpc"
}

variable "connector_name" {
  description = "Nombre del VPC Access Connector para Cloud Run"
  type        = string
  default     = "portal-api-connector"
}

variable "connector_cidr" {
  description = "CIDR del rango IP del conector (debe ser /28, fuera del rango de la VPC)"
  type        = string
  default     = "10.8.0.0/28"
}

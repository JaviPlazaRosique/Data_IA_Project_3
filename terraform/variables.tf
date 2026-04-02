variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region en la que se despliegan los recursos dentro de GCP"
  type        = string
  default     = "europe-west1"
}
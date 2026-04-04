variable "nombre_bucket" {
  description = "Nombre del bucket, en el que se alojará la web"
  type        = string
}

variable "region" {
  description = "Region en la que se despliegan los recursos dentro de GCP"
  type        = string
  default     = "europe-west1"
}

variable "ruta_recurso_web" {
  description = "Ruta a la carpeta donde se encuentra el frontend de la web"
  type        = string
}
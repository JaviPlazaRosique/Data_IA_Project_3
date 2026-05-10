variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Región donde se despliega el workflow"
  type        = string
}

variable "nombre_workflow" {
  description = "Nombre del workflow"
  type        = string
}

variable "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio que ejecuta el workflow"
  type        = string
}

variable "ruta_workflow" {
  description = "Ruta al fichero YAML con la definición del workflow"
  type        = string
}

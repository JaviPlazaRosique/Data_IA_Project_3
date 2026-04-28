variable "nombre_workflow" {
  description = "Nombre del workflow de Google Cloud"
  type        = string
}

variable "region" {
  description = "Region de GCP donde se desplegara el workflow"
  type        = string
}

variable "description" {
  description = "Descripcion del workflow"
  type        = string
  default     = "Workflow generado por Terraform"
}

variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio que utilizara el workflow"
  type        = string
}

variable "contenido_workflow" {
  description = "Contenido YAML o JSON del workflow"
  type        = string
}

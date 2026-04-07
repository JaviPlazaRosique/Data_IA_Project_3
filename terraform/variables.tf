variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region en la que se despliegan los recursos dentro de GCP"
  type        = string
  default     = "europe-west1"
}

variable "repo_github" {
  description = "Repositorio de GitHub"
  type        = string
}

variable "usuario_github" {
  description = "Usuario de GitHub (debe tener permisos sobre el repo)"
  type        = string
}
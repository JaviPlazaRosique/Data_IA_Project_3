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

variable "db_tier" {
  description = "Tier de la maquina de CloudSQL"
  type        = string
  default     = "db-f1-micro"
}

variable "db_availability_type" {
  description = "Tipo de disponibilidad de CloudSQL: ZONAL o REGIONAL"
  type        = string
  default     = "ZONAL"
}

variable "deletion_protection" {
  description = "Proteger CloudSQL de eliminacion accidental"
  type        = bool
  default     = false
}

variable "db_password" {
  description = "Contrasena del usuario api_user en CloudSQL"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "Clave secreta para firmar tokens JWT (minimo 32 caracteres)"
  type        = string
  sensitive   = true
}

variable "cors_origins" {
  description = "Origenes CORS permitidos para el Portal API (separados por comas)"
  type        = string
  default     = ""
}

variable "portal_api_image" {
  description = "Imagen Docker del Portal API (europe-west1-docker.pkg.dev/...)"
  type        = string
  default     = "europe-west1-docker.pkg.dev/PROJECT/repo-data-ia-project3/portal-api:latest"
}
variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Región de GCP donde está el repositorio de Artifact Registry"
  type        = string
}

variable "nombre_repo_artifact" {
  description = "Nombre del repositorio de Artifact Registry donde se publica la imagen launcher"
  type        = string
}

variable "nombre_imagen" {
  description = "Nombre de la imagen launcher dentro del repositorio"
  type        = string
}

variable "ruta_contexto_docker" {
  description = "Ruta al contexto de build (debe contener Dockerfile, requirements.txt y el .py del pipeline)"
  type        = string
}

variable "ruta_metadata" {
  description = "Ruta al fichero metadata.json con la definición de parámetros del template"
  type        = string
}

variable "nombre_bucket_spec" {
  description = "Nombre del bucket de GCS donde se publica el spec JSON del Flex Template"
  type        = string
}

variable "ruta_spec" {
  description = "Ruta (key) dentro del bucket para el spec JSON del Flex Template"
  type        = string
  default     = "templates/flex-template.json"
}

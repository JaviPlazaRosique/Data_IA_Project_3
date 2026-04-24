variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type        = string
}

variable "nombre_servicio" {
  description = "Nombre del servicio de Cloud Run"
  type        = string
}

variable "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio que ejecutara el servicio Cloud Run"
  type        = string
}

variable "id_conector_vpc" {
  description = "ID del VPC Access Connector. Si es null, no se configura VPC access."
  type        = string
  default     = null
}

variable "egress_vpc" {
  description = "Modo de egress del VPC connector"
  type        = string
  default     = "PRIVATE_RANGES_ONLY"
}

variable "variables_entorno" {
  description = "Variables de entorno en texto plano para el contenedor"
  type        = map(string)
  default     = {}
}

variable "secretos_entorno" {
  description = "Variables de entorno cuyo valor proviene de Secret Manager"
  type = map(object({
    secret  = string
    version = string
  }))
  default = {}
}

variable "cpu" {
  description = "Limite de CPU para el contenedor"
  type        = string
  default     = "1"
}

variable "memoria" {
  description = "Limite de memoria para el contenedor"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "Minimo de instancias Cloud Run"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximo de instancias Cloud Run"
  type        = number
  default     = 100
}

variable "proteccion_borrado" {
  description = "Habilita proteccion contra borrado del servicio"
  type        = bool
  default     = false
}

variable "acceso_publico" {
  description = "Permite invocacion publica del servicio (allUsers)"
  type        = bool
  default     = true
}

variable "ruta_contexto_docker" {
  description = "Ruta al contexto de build de Docker para el primer push"
  type        = string
}

variable "nombre_repo_artifact" {
  description = "Nombre del repositorio donde se guardan las imagenes de Docker en Artifact Registry"
  type        = string
}
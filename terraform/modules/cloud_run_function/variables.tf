variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type        = string
}

variable "nombre_funcion" {
  description = "Nombre de la Cloud Run Function"
  type        = string
}

variable "descripcion" {
  description = "Descripcion de la Cloud Run Function"
  type        = string
  default     = ""
}

variable "runtime" {
  description = "Runtime de ejecucion (p.ej. python312, nodejs20, go122)"
  type        = string
  validation {
    condition     = contains(["python312", "python311", "python310", "nodejs20", "nodejs18", "go122", "go121", "java21", "java17", "ruby33", "dotnet8"], var.runtime)
    error_message = "Runtime no soportado. Usa python312, nodejs20, go122, java21, ruby33 o dotnet8 entre otros."
  }
}

variable "punto_entrada" {
  description = "Nombre de la funcion o metodo que sirve como punto de entrada"
  type        = string
}

variable "ruta_codigo" {
  description = "Ruta local al directorio con el codigo fuente de la funcion"
  type        = string
}

variable "bucket_codigo" {
  description = "Nombre del bucket de GCS donde se subira el ZIP del codigo fuente"
  type        = string
}

variable "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio que ejecutara la funcion"
  type        = string
}

variable "variables_entorno" {
  description = "Variables de entorno en texto plano para la funcion"
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

variable "memoria" {
  description = "Memoria disponible para la funcion (p.ej. 256Mi, 512Mi, 1Gi)"
  type        = string
  default     = "256Mi"
}

variable "cpu" {
  description = "CPU disponible para la funcion (p.ej. 0.1666, 1, 2)"
  type        = string
  default     = "0.1666"
}

variable "timeout_segundos" {
  description = "Tiempo maximo de ejecucion de la funcion en segundos"
  type        = number
  default     = 60
}

variable "min_instances" {
  description = "Numero minimo de instancias activas"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Numero maximo de instancias concurrentes"
  type        = number
  default     = 10
}

variable "configuracion_ingress" {
  description = "Configuracion de ingress de la funcion"
  type        = string
  default     = "ALLOW_ALL"
  validation {
    condition     = contains(["ALLOW_ALL", "ALLOW_INTERNAL_ONLY", "ALLOW_INTERNAL_AND_GCLB"], var.configuracion_ingress)
    error_message = "El valor debe ser ALLOW_ALL, ALLOW_INTERNAL_ONLY o ALLOW_INTERNAL_AND_GCLB."
  }
}

variable "acceso_publico" {
  description = "Permite la invocacion publica de la funcion (allUsers)"
  type        = bool
  default     = false
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

variable "tipo_trigger" {
  description = "Tipo de disparador de la funcion: http o evento"
  type        = string
  default     = "http"
  validation {
    condition     = contains(["http", "evento"], var.tipo_trigger)
    error_message = "El tipo de trigger debe ser http o evento."
  }
}

variable "tipo_evento" {
  description = "Tipo de evento de Eventarc (p.ej. google.cloud.pubsub.topic.v1.messagePublished). Solo aplica cuando tipo_trigger es evento."
  type        = string
  default     = null
}

variable "tema_pubsub" {
  description = "Recurso completo del tema de Pub/Sub (p.ej. projects/mi-proyecto/topics/mi-tema). Solo aplica cuando tipo_trigger es evento."
  type        = string
  default     = null
}

variable "politica_reintento" {
  description = "Politica de reintento ante fallos del trigger de evento"
  type        = string
  default     = "RETRY_POLICY_RETRY"
  validation {
    condition     = contains(["RETRY_POLICY_UNSPECIFIED", "RETRY_POLICY_DO_NOT_RETRY", "RETRY_POLICY_RETRY"], var.politica_reintento)
    error_message = "La politica de reintento debe ser RETRY_POLICY_UNSPECIFIED, RETRY_POLICY_DO_NOT_RETRY o RETRY_POLICY_RETRY."
  }
}

variable "proteccion_borrado" {
  description = "Habilita proteccion contra borrado de la funcion"
  type        = bool
  default     = false
}

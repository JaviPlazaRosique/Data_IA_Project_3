variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP donde se despliega Vertex AI Agent Engine"
  type        = string
}

variable "nombre_agente" {
  description = "Nombre visible del Agent Engine"
  type        = string
}

variable "descripcion" {
  description = "Descripcion del Agent Engine"
  type        = string
  default     = "Agente ADK que recomienda eventos con BigQuery Vector Search."
}

variable "email_cuenta_servicio" {
  description = "Email de la cuenta de servicio que ejecuta el Agent Engine"
  type        = string
}

variable "ruta_codigo_fuente" {
  description = "Ruta raiz del repositorio que contiene el paquete agent"
  type        = string
}

variable "entrypoint_module" {
  description = "Modulo Python usado como entrypoint del Agent Engine"
  type        = string
  default     = "agent.agent"
}

variable "entrypoint_object" {
  description = "Objeto Python usado como entrypoint del Agent Engine"
  type        = string
  default     = "agent_engine"
}

variable "requirements_file" {
  description = "Ruta del requirements.txt relativa a ruta_codigo_fuente"
  type        = string
  default     = "agent/requirements.txt"
}

variable "python_version" {
  description = "Version de Python usada por Agent Engine"
  type        = string
  default     = "3.12"
}

variable "bigquery_dataset" {
  description = "Dataset de BigQuery que contiene la tabla RAG"
  type        = string
}

variable "bigquery_rag_table" {
  description = "Tabla de BigQuery que contiene los eventos y embeddings del RAG"
  type        = string
}

variable "agent_model" {
  description = "Modelo generativo usado por el agente"
  type        = string
  default     = "gemini-2.5-flash"
}

variable "embedding_model" {
  description = "Modelo de embeddings usado por el RAG"
  type        = string
  default     = "gemini-embedding-001"
}

variable "embedding_dimension" {
  description = "Dimension de salida de los embeddings"
  type        = number
  default     = 3072
}

variable "variables_entorno_adicionales" {
  description = "Variables de entorno adicionales para el runtime del Agent Engine"
  type        = map(string)
  default     = {}
}

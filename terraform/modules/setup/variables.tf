variable "servicios_gcp" {
  description = "Lista de los servicios de GCP para activar"
  type        = list(string)
  default = [
    "run.googleapis.com",                 
    "apigateway.googleapis.com",          
    "dataflow.googleapis.com",           
    "iam.googleapis.com",                 
    "compute.googleapis.com",             
    "firestore.googleapis.com",         
    "cloudresourcemanager.googleapis.com", 
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "sql-component.googleapis.com",
    "servicenetworking.googleapis.com",
    "vpcaccess.googleapis.com"
  ]
} 

variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "usuario_github" {
  description = "Usuario de GitHub"
  type        = string
}

variable "repo_github" {
  description = "Repositorio de GitHub, en el que se encuentran los workflows"
  type        = string
}
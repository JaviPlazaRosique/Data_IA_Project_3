variable "gcp_services" {
  description = "A list of GCP services to enable."
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
    "storage.googleapis.com"
  ]
} 
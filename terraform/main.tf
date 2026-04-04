module "setup" {
  source = "./modules/setup"
}

module "frontend_usuarios" {
  source           = "./modules/bucket_web"
  nombre_bucket    = "bucket-prueba-dataiaproject3-app-recomendacion-eventos"
  ruta_recurso_web = "../frontend/portal"
}
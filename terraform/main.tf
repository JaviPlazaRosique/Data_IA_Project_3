module "setup" {
  source         = "./modules/setup"
  id_proyecto    = var.id_proyecto
  repo_github    = var.repo_github
  usuario_github = var.usuario_github
}

module "frontend_usuarios" {
  source           = "./modules/bucket_web"
  nombre_bucket    = "bucket-prueba-dataiaproject3-app-recomendacion-eventos"
  ruta_recurso_web = "../frontend/portal"
  id_proyecto      = var.id_proyecto
  depends_on = [
    module.setup
  ]
}
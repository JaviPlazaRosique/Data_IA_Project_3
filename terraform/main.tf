module "setup" {
  source         = "./modules/setup"
  id_proyecto    = var.id_proyecto
  repo_github    = var.repo_github
  usuario_github = var.usuario_github
}

module "cicd_frontend_usuarios" {
  source             = "./modules/wif_workflow"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "cicd-frontend-usuarios"
  nombre_despliege   = "Cuenta de servicio para el CI/CD del frontend de la web de los usuarios"
  cuenta_servicio_roles = [
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.writer"
  ]
  nombre_pool     = module.setup.nombre_pool
  nombre_workflow = "cicd_frontend_usuarios"
  depends_on = [
    module.setup
  ]
}

module "repo_artifact" {
  source           = "./modules/artifact_registry"
  id_proyecto      = var.id_proyecto
  id_repo_artifact = "repo-data-ia-project3"
  depends_on = [
    module.setup
  ]
}
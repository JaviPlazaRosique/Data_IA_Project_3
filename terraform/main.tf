locals {
  cors_origins = module.frontend_usuarios.url_web
}

module "setup" {
  source         = "./modules/setup"
  id_proyecto    = var.id_proyecto
  repo_github    = var.repo_github
  usuario_github = var.usuario_github
}

module "frontend_usuarios" {
  source           = "./modules/bucket_web"
  nombre_bucket    = "bucket-prueba-dataiaproject3-app-recomendacion-eventos-v2"
  ruta_recurso_web = "../frontend/portal"
  id_proyecto      = var.id_proyecto
  depends_on = [
    module.setup
  ]
}

resource "google_storage_bucket_object" "public_config" {
  name         = "public-config.json"
  bucket       = module.frontend_usuarios.nombre_bucket
  content      = jsonencode({ backendUrl = module.cloud_run_portal_api.service_url })
  content_type = "application/json"
  cache_control = "no-cache"
}


module "cicd_frontend_usuarios" {
  source             = "./modules/wif_workflow"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "cicd-frontend-usuarios"
  nombre_despliege   = "Cuenta de servicio para el CI/CD del frontend de la web de los usuarios"
  cuenta_servicio_roles = [
    "roles/storage.admin"
  ]
  nombre_pool     = module.setup.nombre_pool
  nombre_workflow = "cicd_frontend_usuarios"
  depends_on = [
    module.setup
  ]
}

module "cicd_backend_portal_api" {
  source             = "./modules/wif_workflow"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "cicd-backend-portal-api"
  nombre_despliege   = "Cuenta de servicio para el CI/CD del backend Portal API"
  cuenta_servicio_roles = [
    "roles/artifactregistry.writer",
    "roles/run.developer",
    "roles/iam.serviceAccountUser",
  ]
  nombre_pool     = module.setup.nombre_pool
  nombre_workflow = "cicd_backend_portal_api"
  depends_on = [
    module.setup
  ]
}

resource "google_storage_bucket_iam_member" "backend_cicd_config_writer" {
  bucket = module.frontend_usuarios.nombre_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${module.cicd_backend_portal_api.email_cuenta_servicio}"
}

module "cicd_terraform" {
  source             = "./modules/wif_workflow"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "cicd-terraform"
  nombre_despliege   = "Cuenta de servicio para aplicar Terraform desde GitHub Actions"
  cuenta_servicio_roles = [
    "roles/editor",
    "roles/iam.securityAdmin",
  ]
  nombre_pool     = module.setup.nombre_pool
  nombre_workflow = "cicd_terraform"
  depends_on = [
    module.setup
  ]
}

module "repo_artifact" {
  source         = "./modules/artifact_registry"
  id_proyecto    = var.id_proyecto
  id_repositorio = "repo-data-ia-project3"
  depends_on = [
    module.setup
  ]
}

module "vpc_portal" {
  source      = "./modules/vpc"
  id_proyecto = var.id_proyecto
  region      = var.region
  depends_on = [
    module.setup
  ]
}

module "cloudsql_portal" {
  source                 = "./modules/cloudsql"
  id_proyecto            = var.id_proyecto
  region                 = var.region
  id_red                 = module.vpc_portal.network_id
  conexion_vpc_privada   = module.vpc_portal.private_vpc_connection
  nombre_instancia_bd    = "portal-api-db"
  nombre_base_datos      = "portal_api"
  usuario_bd             = "api_user"
  nivel_bd               = var.nivel_bd
  tipo_disponibilidad_bd = var.tipo_disponibilidad_bd
  proteccion_borrado     = var.proteccion_borrado
  contrasena_bd          = var.contrasena_bd
  depends_on = [
    module.vpc_portal
  ]
}

module "portal_api_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "portal-api-sa"
  nombre_despliege   = "Cuenta de servicio del Portal API en Cloud Run"
  cuenta_servicio_roles = [
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
  ]
  depends_on = [
    module.setup
  ]
}

module "secrets_portal_api" {
  source      = "./modules/secret_manager"
  id_proyecto = var.id_proyecto
  secretos = {
    "portal-api-db-password"    = var.contrasena_bd
    "portal-api-jwt-secret-key" = var.clave_jwt
  }
  cuentas_servicio_acceso = [
    module.portal_api_sa.email_cuenta_servicio
  ]
  nombres_cuentas_servicio = [
    "portal-api-sa"
  ]
  depends_on = [
    module.setup, 
    module.portal_api_sa
  ]
}

module "cloud_run_portal_api" {
  source                = "./modules/cloud_run"
  id_proyecto           = var.id_proyecto
  region                = var.region
  nombre_servicio      = "portal-api"
  nombre_repo_artifact = "repo-data-ia-project3"
  ruta_contexto_docker = "${path.root}/../backend/portal-api"
  email_cuenta_servicio = module.portal_api_sa.email_cuenta_servicio
  id_conector_vpc       = module.vpc_portal.vpc_connector_id

  variables_entorno = {
    ENVIRONMENT  = "production"
    CORS_ORIGINS = local.cors_origins
    DB_HOST      = module.cloudsql_portal.private_ip
    DB_NAME      = module.cloudsql_portal.database_name
    DB_USER      = module.cloudsql_portal.db_user
  }

  secretos_entorno = {
    DB_PASSWORD = {
      secret  = module.secrets_portal_api.ids_secretos["portal-api-db-password"]
      version = "latest"
    }
    JWT_SECRET_KEY = {
      secret  = module.secrets_portal_api.ids_secretos["portal-api-jwt-secret-key"]
      version = "latest"
    }
  }

  depends_on = [
    module.cloudsql_portal,
    module.secrets_portal_api,
    module.portal_api_sa
  ]
}
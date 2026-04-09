locals {
  # Frontend bucket URL is the only allowed CORS origin for the backend API
  cors_origins = module.frontend_usuarios.url_web
  # Image URI computed from project ID — can be overridden via var.portal_api_image
  # Uses a public placeholder on first apply; CI/CD replaces it with the real image on first push
  portal_api_image = var.portal_api_image != "" ? var.portal_api_image : "us-docker.pkg.dev/cloudrun/container/hello:latest"
}

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

module "cicd_frontend_usuarios" {
  source                = "./modules/wif_workflow"
  id_proyecto           = var.id_proyecto
  id_cuenta_servicio    = "cicd-frontend-usuarios"
  nombre_despliege      = "Cuenta de servicio para el CI/CD del frontend de la web de los usuarios"
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
  depends_on      = [module.setup]
}

# Scoped write access: backend CI/CD can only create/delete objects in the frontend bucket
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
  depends_on      = [module.setup]
}

module "repo_artifact" {
  source           = "./modules/artifact_registry"
  id_proyecto      = var.id_proyecto
  id_repo_artifact = "repo-data-ia-project3"
  depends_on = [
    module.setup
  ]
}

# ── Backend infrastructure ────────────────────────────────────────────────────

module "vpc_portal" {
  source      = "./modules/vpc"
  id_proyecto = var.id_proyecto
  region      = var.region
  depends_on  = [module.setup]
}

module "cloudsql_portal" {
  source                 = "./modules/cloudsql"
  id_proyecto            = var.id_proyecto
  region                 = var.region
  network_id             = module.vpc_portal.network_id
  private_vpc_connection = module.vpc_portal.private_vpc_connection
  db_tier                = var.db_tier
  db_availability_type   = var.db_availability_type
  deletion_protection    = var.deletion_protection
  db_password            = var.db_password
  depends_on             = [module.vpc_portal]
}

# Service account for Cloud Run — created independently so its email
# can be passed to both secrets and cloud_run without circular deps.
resource "google_service_account" "portal_api_sa" {
  account_id   = "portal-api-sa"
  display_name = "Cuenta de servicio del Portal API en Cloud Run"
  project      = var.id_proyecto
  depends_on   = [module.setup]
}

resource "google_project_iam_member" "portal_api_sa_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
  ])
  project = var.id_proyecto
  role    = each.value
  member  = "serviceAccount:${google_service_account.portal_api_sa.email}"
}

module "secrets_portal_api" {
  source             = "./modules/secret_manager"
  id_proyecto        = var.id_proyecto
  db_password        = var.db_password
  jwt_secret_key     = var.jwt_secret_key
  cloud_run_sa_email = google_service_account.portal_api_sa.email
  depends_on         = [module.setup, google_service_account.portal_api_sa]
}

module "cloud_run_portal_api" {
  source                = "./modules/cloud_run"
  id_proyecto           = var.id_proyecto
  region                = var.region
  image                 = local.portal_api_image
  service_account_email = google_service_account.portal_api_sa.email
  vpc_connector_id      = module.vpc_portal.vpc_connector_id
  db_private_ip         = module.cloudsql_portal.private_ip
  db_name               = module.cloudsql_portal.database_name
  db_user               = module.cloudsql_portal.db_user
  cors_origins          = local.cors_origins
  depends_on            = [module.cloudsql_portal, module.secrets_portal_api, google_project_iam_member.portal_api_sa_roles]
}

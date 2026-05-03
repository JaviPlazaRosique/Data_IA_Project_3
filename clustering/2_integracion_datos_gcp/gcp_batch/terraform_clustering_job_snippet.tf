module "clustering_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "clustering-train-sa"
  nombre_despliege   = "Cuenta de servicio para el job de clustering"
  cuenta_servicio_roles = [
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/bigquery.dataEditor",
    "roles/artifactregistry.reader",
  ]
}

module "cicd_clustering_train_assign" {
  source             = "./modules/wif_workflow"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "cicd-clustering-train"
  nombre_despliege   = "Cuenta de servicio para el CI/CD del job de clustering"
  cuenta_servicio_roles = [
    "roles/artifactregistry.writer",
    "roles/run.developer",
    "roles/iam.serviceAccountUser",
  ]
  nombre_pool     = module.setup.nombre_pool
  nombre_workflow = "cicd_clustering_train"
}

module "clustering_train_assign_job" {
  source                = "./modules/cloud_run_job"
  id_proyecto           = var.id_proyecto
  region                = var.region
  nombre_job            = "clustering-train-assign"
  nombre_repo_artifact  = module.repo_artifact.id_repo_artifact
  nombre_imagen         = "clustering-train-assign"
  ruta_contexto_docker  = "${path.root}/.."
  ruta_dockerfile       = "clustering/2_integracion_datos_gcp/gcp_batch/Dockerfile"
  email_cuenta_servicio = module.clustering_sa.email_cuenta_servicio

  cpu     = "1"
  memoria = "2Gi"

  variables_entorno = {
    GCP_PROJECT                  = var.id_proyecto
    BQ_RAW_DATASET               = module.bigquery.id_dataset
    BQ_MARTS_DATASET             = "${module.bigquery.id_dataset}_marts"
    BQ_FEATURE_DATASET           = "${module.bigquery.id_dataset}_marts"
    BQ_SOURCE_FEATURE_TABLE      = "dim_user_cluster_features_current"
    BQ_LOCATION                  = "EU"
    LOCAL_WORKDIR                = "/tmp/clustering_job"
    MODEL_RUN_ID_PREFIX          = "weekly_clustering"
    K_VALUES                     = "4,5,6,7,8"
    MIN_SWIPES_30D               = "8"
    MIN_SWIPES_90D               = "24"
    LOOKBACK_DAYS                = "90"
    NEIGHBOR_COUNT               = "2"
    MAX_RECOMMENDATIONS_PER_USER = "30"
  }
}

module "scheduler_clustering_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "scheduler-clustering-sa"
  nombre_despliege   = "Cuenta de servicio para lanzar el job de clustering"
  cuenta_servicio_roles = [
    "roles/run.invoker"
  ]
}

module "scheduler_clustering_weekly" {
  source       = "./modules/scheduler"
  id_proyecto  = var.id_proyecto
  region       = var.region
  nombre_job   = "clustering-train-assign-lunes-01h"
  descripcion  = "Lanza el Cloud Run Job de clustering una vez por semana"
  cron         = "0 1 * * 1"
  zona_horaria = "Europe/Madrid"
  url_destino  = "https://${var.region}-run.googleapis.com/v2/projects/${var.id_proyecto}/locations/${var.region}/jobs/${module.clustering_train_assign_job.nombre_job}:run"
  metodo_http  = "POST"
  cabeceras    = { "Content-Type" = "application/json" }

  email_cuenta_servicio = module.scheduler_clustering_sa.email_cuenta_servicio
}

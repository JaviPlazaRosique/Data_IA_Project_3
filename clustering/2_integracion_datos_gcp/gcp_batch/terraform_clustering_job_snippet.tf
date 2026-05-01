module "clustering_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "clustering-train-sa"
  nombre_despliege   = "Cuenta de servicio para el job de clustering"
  cuenta_servicio_roles = [
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/bigquery.dataEditor",
    "roles/storage.objectAdmin",
  ]
}

module "clustering_train_assign_job" {
  source                = "./modules/cloud_run_job"
  id_proyecto           = var.id_proyecto
  region                = var.region
  nombre_job            = "clustering-train-assign"
  nombre_repo_artifact  = module.repo_artifact.id_repo_artifact
  nombre_imagen         = "clustering-train-assign"
  ruta_contexto_docker  = "${path.root}/.."
  email_cuenta_servicio = module.clustering_sa.email_cuenta_servicio

  cpu     = "1"
  memoria = "2Gi"

  variables_entorno = {
    GCP_PROJECT            = var.id_proyecto
    BQ_SOURCE_DATASET      = module.bigquery.id_dataset
    BQ_SOURCE_FEATURE_TABLE = "dim_user_cluster_features_current"
    LOCAL_WORKDIR          = "/tmp/clustering_job"
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

module "scheduler_clustering_daily" {
  source       = "./modules/scheduler"
  id_proyecto  = var.id_proyecto
  region       = var.region
  nombre_job   = "clustering-train-assign-daily"
  descripcion  = "Lanza el Cloud Run Job de clustering una vez al dia"
  cron         = "0 2 * * *"
  zona_horaria = "Europe/Madrid"
  url_destino  = "https://${var.region}-run.googleapis.com/v2/projects/${var.id_proyecto}/locations/${var.region}/jobs/${module.clustering_train_assign_job.nombre_job}:run"
  metodo_http  = "POST"
  cabeceras    = { "Content-Type" = "application/json" }

  email_cuenta_servicio = module.scheduler_clustering_sa.email_cuenta_servicio
}

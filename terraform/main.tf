locals {
  cors_origins = "https://storage.googleapis.com,${module.frontend_usuarios.url_web}"

  flex_template_launch_url = "https://dataflow.googleapis.com/v1b3/projects/${var.id_proyecto}/locations/${var.region}/flexTemplates:launch"

  flex_template_parametros = {
    id_proyecto                  = var.id_proyecto
    coleccion_firestore_eventos  = "eventos"
    coleccion_firestore_recintos = "recintos"
    coleccion_gemini_cache       = "gemini_cache"
    dataset_bigquery             = module.bigquery.id_dataset
    tabla_eventos_bigquery       = "eventos"
    bucket_gcs                   = "${module.bucket_eventos_raw.url}/eventos"
    id_secreto_ticketmaster      = "api-key-ticketmaster"
    id_secreto_google_places     = "api-key-google-places"
  }

  flex_template_body = {
    launchParameter = {
      containerSpecGcsPath = module.batch_ingesta_template.spec_gcs_path
      parameters           = local.flex_template_parametros
      environment = {
        serviceAccountEmail = module.dataflow_sa.email_cuenta_servicio
        tempLocation        = "${module.bucket_ejecucion_dataflow.url}/temp"
        stagingLocation     = "${module.bucket_ejecucion_dataflow.url}/staging"
      }
    }
  }
}

module "setup" {
  source         = "./modules/setup"
  id_proyecto    = var.id_proyecto
  repo_github    = var.repo_github
  usuario_github = var.usuario_github
}

module "frontend_usuarios" {
  source           = "./modules/bucket_web"
  nombre_bucket    = "app-recomendacion-eventos-${var.id_proyecto}"
  ruta_recurso_web = "../frontend/portal"
  id_proyecto      = var.id_proyecto
  depends_on = [
    module.setup
  ]
}

resource "google_storage_bucket_object" "public_config" {
  name          = "public-config.json"
  bucket        = module.frontend_usuarios.nombre_bucket
  content       = jsonencode({ backendUrl = module.cloud_run_portal_api.service_url })
  content_type  = "application/json"
  cache_control = "no-cache"
}

module "cicd_frontend_usuarios" {
  source             = "./modules/wif_workflow"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "cicd-frontend-usuarios"
  nombre_despliege   = "Cuenta de servicio para el CI/CD del frontend de la web de los usuarios"
  cuenta_servicio_roles = [
    "roles/storage.objectAdmin",
    "roles/run.viewer",
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

module "migrate_bd_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "migrate-bd-sa"
  nombre_despliege   = "Cuenta de servicio para el job de migraciones de base de datos"
  cuenta_servicio_roles = [
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
  ]
  depends_on = [
    module.setup
  ]
}

module "cicd_migrate_bd" {
  source             = "./modules/wif_workflow"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "cicd-migrate-bd"
  nombre_despliege   = "Cuenta de servicio para el CI/CD de migraciones de base de datos"
  cuenta_servicio_roles = [
    "roles/artifactregistry.writer",
    "roles/run.developer",
    "roles/iam.serviceAccountUser",
  ]
  nombre_pool     = module.setup.nombre_pool
  nombre_workflow = "cicd_migrate_bd"
  depends_on = [
    module.setup
  ]
}

resource "google_storage_bucket_iam_member" "cicd_backend_public_config" {
  bucket = module.frontend_usuarios.nombre_bucket
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${module.cicd_backend_portal_api.email_cuenta_servicio}"
}

module "repo_artifact" {
  source         = "./modules/artifact_registry"
  id_proyecto    = var.id_proyecto
  id_repositorio = "repo-recomendador-eventos"
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
    "roles/datastore.user",
    "roles/cloudtasks.enqueuer",
  ]
  depends_on = [
    module.setup
  ]
}

module "bucket_avatares" {
  source      = "./modules/bucket"
  nombre      = "avatares-usuarios-${var.id_proyecto}"
  id_proyecto = var.id_proyecto
  ubicacion   = upper(var.region)
  depends_on = [
    module.setup
  ]
}

resource "google_storage_bucket_iam_member" "portal_api_sa_avatares" {
  bucket = module.bucket_avatares.nombre
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${module.portal_api_sa.email_cuenta_servicio}"
}

data "google_project" "actual" {
  project_id = var.id_proyecto
}

locals {
  pubsub_service_agent = "service-${data.google_project.actual.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

module "pubsub_swipe_events" {
  source                  = "./modules/pubsub"
  id_proyecto             = var.id_proyecto
  nombre_topic            = "swipe-events"
  publicadores            = [module.portal_api_sa.email_cuenta_servicio]
  habilitar_dlq           = true
  nombre_suscripcion      = "swipe-events-sub"
  tipo_suscripcion        = "bigquery"
  bigquery_table          = "${var.id_proyecto}.${module.bigquery.id_dataset}.swipes_raw"
  bigquery_write_metadata = true
  depends_on = [
    module.portal_api_sa,
    module.bigquery
  ]
}

module "secretos_proyecto" {
  source      = "./modules/secret_manager"
  id_proyecto = var.id_proyecto
  secretos = {
    "portal-api-db-password"    = var.contrasena_bd
    "portal-api-jwt-secret-key" = var.clave_jwt
    "api-key-ticketmaster"      = var.ticketmaster_apikey
    "api-key-google-places"     = module.setup.google_places_key_string
    "sendgrid-api-key"          = var.sendgrid_api_key
  }
  depends_on = [
    module.setup
  ]
}

module "cloud_run_portal_api" {
  source                = "./modules/cloud_run"
  id_proyecto           = var.id_proyecto
  region                = var.region
  nombre_servicio       = "portal-api"
  nombre_repo_artifact  = module.repo_artifact.id_repo_artifact
  ruta_contexto_docker  = "${path.root}/../backend/portal-api"
  email_cuenta_servicio = module.portal_api_sa.email_cuenta_servicio
  id_conector_vpc       = module.vpc_portal.vpc_connector_id

  cpu           = "1"
  memoria       = "1Gi"
  min_instances = 0
  max_instances = 5

  variables_entorno = {
    ENVIRONMENT               = "production"
    CORS_ORIGINS              = local.cors_origins
    DB_HOST                   = module.cloudsql_portal.private_ip
    DB_NAME                   = module.cloudsql_portal.database_name
    DB_USER                   = module.cloudsql_portal.db_user
    GOOGLE_CLOUD_PROJECT      = var.id_proyecto
    PUBSUB_TOPIC_SWIPE_EVENTS = module.pubsub_swipe_events.nombre
    AVATAR_BUCKET_NAME        = module.bucket_avatares.nombre
    CLOUD_TASKS_QUEUE_PATH      = module.cola_valoracion_emails.id_cola
    RATING_EMAIL_FUNCTION_URL   = module.fn_envio_email.url_funcion
    RATING_FUNCTION_SA_EMAIL    = module.rating_functions_sa.email_cuenta_servicio
  }

  secretos_entorno = {
    DB_PASSWORD = {
      secret  = module.secretos_proyecto.ids_secretos["portal-api-db-password"]
      version = "latest"
    }
    JWT_SECRET_KEY = {
      secret  = module.secretos_proyecto.ids_secretos["portal-api-jwt-secret-key"]
      version = "latest"
    }
  }

  depends_on = [
    module.cloudsql_portal,
    module.secretos_proyecto,
    module.portal_api_sa,
    module.pubsub_swipe_events
  ]
}

module "dataflow_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "dataflow-ingestion-sa"
  nombre_despliege   = "Cuenta de servicio para el pipeline de ingestión de Dataflow"
  cuenta_servicio_roles = [
    "roles/dataflow.worker",
    "roles/storage.objectAdmin",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/datastore.user",
    "roles/secretmanager.secretAccessor",
    "roles/artifactregistry.reader",
    "roles/aiplatform.user",
  ]
  depends_on = [
    module.setup,
    module.secretos_proyecto
  ]
}

module "firestore" {
  source             = "./modules/firestore"
  id_proyecto        = var.id_proyecto
  nombre_base_datos  = "(default)"
  ubicacion          = "eur3"
  proteccion_borrado = var.proteccion_borrado

  politicas_ttl = [
    {
      coleccion        = "recintos",
      campo_expiracion = "fecha_expiracion"
    },
    {
      coleccion        = "eventos",
      campo_expiracion = "fecha_utc"
    }
  ]

  indices_compuestos = [
    {
      coleccion = "eventos"
      campos = [
        { field_path = "fecha", order = "ASCENDING" },
        { field_path = "fecha_utc", order = "ASCENDING" },
      ]
    },
    {
      coleccion = "eventos"
      campos = [
        { field_path = "ciudad", order = "ASCENDING" },
        { field_path = "fecha_utc", order = "ASCENDING" },
      ]
    },
    {
      coleccion = "eventos"
      campos = [
        { field_path = "segmento", order = "ASCENDING" },
        { field_path = "fecha_utc", order = "ASCENDING" },
      ]
    },
    {
      coleccion = "eventos"
      campos = [
        { field_path = "fecha", order = "ASCENDING" },
        { field_path = "ciudad", order = "ASCENDING" },
        { field_path = "fecha_utc", order = "ASCENDING" },
      ]
    },
    {
      coleccion = "eventos"
      campos = [
        { field_path = "fecha", order = "ASCENDING" },
        { field_path = "segmento", order = "ASCENDING" },
        { field_path = "fecha_utc", order = "ASCENDING" },
      ]
    },
  ]

  depends_on = [
    module.setup
  ]
}

module "bigquery" {
  source             = "./modules/bigquery"
  id_proyecto        = var.id_proyecto
  id_dataset         = "recomendacion_planes"
  nombre_dataset     = "Dataset analítico de la app de recomendación de planes"
  ubicacion          = "EU"
  proteccion_borrado = var.proteccion_borrado

  tablas = [
    {
      id_tabla        = "eventos"
      campo_particion = "fecha_utc"
      schema_json = jsonencode([
        {
          name = "id",
          type = "STRING",
          mode = "REQUIRED"
        },
        {
          name = "nombre",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "url",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "fecha",
          type = "DATE",
          mode = "NULLABLE"
        },
        {
          name = "hora",
          type = "TIME",
          mode = "NULLABLE"
        },
        {
          name = "fecha_utc",
          type = "TIMESTAMP",
          mode = "NULLABLE"
        },
        {
          name = "estado",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "venta_inicio",
          type = "TIMESTAMP",
          mode = "NULLABLE"
        },
        {
          name = "venta_fin",
          type = "TIMESTAMP",
          mode = "NULLABLE"
        },
        {
          name = "segmento",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "genero",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "subgenero",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "recinto_id",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "recinto_nombre",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "ciudad",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "direccion",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "codigo_postal",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "latitud",
          type = "FLOAT64",
          mode = "NULLABLE"
        },
        {
          name = "longitud",
          type = "FLOAT64",
          mode = "NULLABLE"
        },
        {
          name = "artista_id",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "artista_nombre",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "promotor",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "descripcion",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "antelacion_recomendada",
          type = "RECORD",
          mode = "NULLABLE",
          fields = [
            { name = "minutos_antelacion", type = "INTEGER", mode = "NULLABLE" },
            { name = "motivo", type = "STRING", mode = "NULLABLE" },
          ]
        },
        {
          name = "vibra",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "etiquetas_ocasion",
          type = "STRING",
          mode = "REPEATED"
        },
        {
          name = "banda_precio",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "interior_exterior",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "franja_horaria",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "puntuacion_romantica",
          type = "INTEGER",
          mode = "NULLABLE"
        },
        {
          name = "puntuacion_familiar",
          type = "INTEGER",
          mode = "NULLABLE"
        },
        {
          name = "puntuacion_grupo",
          type = "INTEGER",
          mode = "NULLABLE"
        },
        {
          name = "puntuacion_turista",
          type = "INTEGER",
          mode = "NULLABLE"
        },
        {
          name = "duracion_minutos_estimada",
          type = "INTEGER",
          mode = "NULLABLE"
        },
        {
          name = "maridajes_plan",
          type = "STRING",
          mode = "REPEATED"
        },
        {
          name = "categoria",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "subcategoria",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "tiempo",
          type = "RECORD",
          mode = "NULLABLE",
          fields = [
            { name = "temp_max", type = "FLOAT64", mode = "NULLABLE" },
            { name = "temp_min", type = "FLOAT64", mode = "NULLABLE" },
            { name = "precipitacion_mm", type = "FLOAT64", mode = "NULLABLE" },
            { name = "codigo_wmo", type = "INTEGER", mode = "NULLABLE" },
            { name = "descripcion", type = "STRING", mode = "NULLABLE" },
            { name = "viento_max_kmh", type = "FLOAT64", mode = "NULLABLE" },
          ]
        }
      ])
    },
    {
      id_tabla        = "valoraciones_eventos"
      campo_particion = "fecha_valoracion"
      schema_json = jsonencode([
        {
          name = "id_usuario",
          type = "STRING",
          mode = "REQUIRED"
        },
        {
          name = "id_evento",
          type = "STRING",
          mode = "REQUIRED"
        },
        {
          name = "nombre_evento",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "valoracion",
          type = "STRING",
          mode = "REQUIRED"
        },
        {
          name = "fecha_valoracion",
          type = "TIMESTAMP",
          mode = "REQUIRED"
        }
      ])
    },
    {
      id_tabla        = "swipes_raw"
      campo_particion = "publish_time"
      schema_json = jsonencode([
        {
          name = "subscription_name",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "message_id",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "publish_time",
          type = "TIMESTAMP",
          mode = "NULLABLE"
        },
        {
          name = "data",
          type = "STRING",
          mode = "NULLABLE"
        },
        {
          name = "attributes",
          type = "STRING",
          mode = "NULLABLE"
        }
      ])
    }
  ]

  iam_members = [
    {
      role   = "roles/bigquery.dataEditor"
      member = "serviceAccount:${local.pubsub_service_agent}"
    },
    {
      role   = "roles/bigquery.metadataViewer"
      member = "serviceAccount:${local.pubsub_service_agent}"
    }
  ]

  depends_on = [
    module.setup
  ]
}

module "bucket_ejecucion_dataflow" {
  source      = "./modules/bucket"
  nombre      = "ejecucion-dataflow-${var.id_proyecto}"
  id_proyecto = var.id_proyecto
  ubicacion   = upper(var.region)
  depends_on = [
    module.setup
  ]
}

module "bucket_eventos_raw" {
  source      = "./modules/bucket"
  nombre      = "copia-eventos-raw-${var.id_proyecto}"
  id_proyecto = var.id_proyecto
  ubicacion   = upper(var.region)

  reglas_ciclo_vida = [
    {
      tipo_accion   = "SetStorageClass"
      clase_destino = "NEARLINE"
      edad_dias     = "30"
    },
    {
      tipo_accion   = "SetStorageClass"
      clase_destino = "COLDLINE"
      edad_dias     = "90"
    },
  ]

  depends_on = [
    module.setup
  ]
}

module "scheduler_ingesta_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "scheduler-ingesta-sa"
  nombre_despliege   = "Cuenta de servicio para el scheduler del batch de ingestión en Dataflow"
  cuenta_servicio_roles = [
    "roles/dataflow.admin",
    "roles/iam.serviceAccountUser"
  ]
  depends_on = [
    module.setup
  ]
}

module "cicd_batch_ingesta" {
  source             = "./modules/wif_workflow"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "cicd-batch-ingesta"
  nombre_despliege   = "Cuenta de servicio para el CI/CD del batch de ingestión"
  cuenta_servicio_roles = [
    "roles/artifactregistry.writer",
    "roles/storage.objectAdmin",
  ]
  nombre_pool     = module.setup.nombre_pool
  nombre_workflow = "cicd_batch_ingesta"
  depends_on = [
    module.setup
  ]
}

module "batch_ingesta_template" {
  source               = "./modules/dataflow_flex_template"
  id_proyecto          = var.id_proyecto
  region               = var.region
  nombre_repo_artifact = module.repo_artifact.id_repo_artifact
  nombre_imagen        = "batch-ingesta"
  ruta_contexto_docker = "${path.root}/../ingestion"
  ruta_metadata        = "${path.root}/../ingestion/metadata.json"
  nombre_bucket_spec   = module.bucket_ejecucion_dataflow.nombre
  ruta_spec            = "templates/batch-ingesta.json"

  depends_on = [
    module.repo_artifact,
    module.bucket_ejecucion_dataflow
  ]
}

module "scheduler_ingesta_media_noche" {
  source       = "./modules/scheduler"
  id_proyecto  = var.id_proyecto
  region       = var.region
  nombre_job   = "ingesta-eventos-00h"
  descripcion  = "Lanza el batch de ingestión de eventos a las 00:00h (Europe/Madrid)"
  cron         = "0 0 * * *"
  zona_horaria = "Europe/Madrid"
  url_destino  = local.flex_template_launch_url
  metodo_http  = "POST"
  cabeceras    = { "Content-Type" = "application/json" }
  cuerpo_peticion = jsonencode(merge(local.flex_template_body, {
    launchParameter = merge(local.flex_template_body.launchParameter, {
      jobName = "ingesta-eventos-00h"
    })
  }))
  email_cuenta_servicio = module.scheduler_ingesta_sa.email_cuenta_servicio
  depends_on = [
    module.scheduler_ingesta_sa,
    module.dataflow_sa,
    module.bucket_ejecucion_dataflow,
    module.bucket_eventos_raw,
    module.bigquery,
    module.firestore,
    module.secretos_proyecto,
    module.batch_ingesta_template
  ]
}

module "scheduler_ingesta_medio_dia" {
  source       = "./modules/scheduler"
  id_proyecto  = var.id_proyecto
  region       = var.region
  nombre_job   = "ingesta-eventos-12h"
  descripcion  = "Lanza el batch de ingestión de eventos a las 12:00h (Europe/Madrid)"
  cron         = "0 12 * * *"
  zona_horaria = "Europe/Madrid"
  url_destino  = local.flex_template_launch_url
  metodo_http  = "POST"
  cabeceras    = { "Content-Type" = "application/json" }
  cuerpo_peticion = jsonencode(merge(local.flex_template_body, {
    launchParameter = merge(local.flex_template_body.launchParameter, {
      jobName = "ingesta-eventos-12h"
    })
  }))
  email_cuenta_servicio = module.scheduler_ingesta_sa.email_cuenta_servicio
  depends_on = [
    module.scheduler_ingesta_sa,
    module.dataflow_sa,
    module.bucket_ejecucion_dataflow,
    module.bucket_eventos_raw,
    module.bigquery,
    module.firestore,
    module.secretos_proyecto,
    module.batch_ingesta_template
  ]
}

module "dbt_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "dbt-transformations-sa"
  nombre_despliege   = "Cuenta de servicio para el Cloud Run Job de dbt"
  cuenta_servicio_roles = [
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/artifactregistry.reader",
  ]
  depends_on = [
    module.setup
  ]
}

module "dbt_transformations_job" {
  source                = "./modules/cloud_run_job"
  id_proyecto           = var.id_proyecto
  region                = var.region
  nombre_job            = "dbt-transformations"
  nombre_repo_artifact  = module.repo_artifact.id_repo_artifact
  nombre_imagen         = "dbt-transformations"
  ruta_contexto_docker  = "${path.root}/../transformations"
  email_cuenta_servicio = module.dbt_sa.email_cuenta_servicio

  cpu     = "1"
  memoria = "1Gi"

  variables_entorno = {
    GCP_PROJECT = var.id_proyecto
    DBT_DATASET = "recomendacion_planes"
  }

  depends_on = [
    module.repo_artifact,
    module.dbt_sa,
    module.bigquery
  ]
}

module "scheduler_dbt_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "scheduler-dbt-sa"
  nombre_despliege   = "Cuenta de servicio para el scheduler del Cloud Run Job de dbt"
  cuenta_servicio_roles = [
    "roles/run.invoker"
  ]
  depends_on = [
    module.setup
  ]
}

module "scheduler_dbt_lunes_jueves_media_noche" {
  source       = "./modules/scheduler"
  id_proyecto  = var.id_proyecto
  region       = var.region
  nombre_job   = "dbt-transformations-lunes-jueves-00h"
  descripcion  = "Lanza dbt build (Cloud Run Job) lunes y jueves a las 00:00h (Europe/Madrid)"
  cron         = "0 0 * * 1,4"
  zona_horaria = "Europe/Madrid"
  url_destino  = "https://${var.region}-run.googleapis.com/v2/projects/${var.id_proyecto}/locations/${var.region}/jobs/${module.dbt_transformations_job.nombre_job}:run"
  metodo_http  = "POST"
  cabeceras    = { "Content-Type" = "application/json" }

  email_cuenta_servicio = module.scheduler_dbt_sa.email_cuenta_servicio
  depends_on = [
    module.scheduler_dbt_sa,
    module.dbt_transformations_job
  ]
}

module "cola_valoracion_emails" {
  source      = "./modules/cloud_tasks"
  id_proyecto = var.id_proyecto
  region      = var.region
  nombre_cola = "email-valoracion-queue"

  max_despachos_por_segundo  = 10
  max_despachos_concurrentes = 5
  max_intentos               = 3
  espera_minima_reintento    = "30s"
  espera_maxima_reintento    = "600s"

  email_cuenta_servicio = module.rating_functions_sa.email_cuenta_servicio
  audiencia_oidc        = module.fn_envio_email.url_funcion

  depends_on = [
    module.setup, 
    module.rating_functions_sa, 
    module.fn_envio_email
  ]
}

module "rating_functions_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "rating-functions-sa"
  nombre_despliege   = "Cuenta de servicio para las Cloud Functions de valoración de eventos"
  cuenta_servicio_roles = [
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
    "roles/cloudfunctions.invoker",
    "roles/bigquery.dataEditor",
  ]
  depends_on = [module.setup]
}

module "fn_envio_email" {
  source                = "./modules/cloud_run_function"
  id_proyecto           = var.id_proyecto
  region                = var.region
  nombre_funcion        = "envio-email-valoracion"
  descripcion           = "Envía el email de valoración de un evento al usuario al día siguiente de visitar su página"
  runtime               = "python312"
  punto_entrada         = "enviar_email_valoracion"
  ruta_codigo           = "${path.root}/../backend/valoracion/envio_email"
  bucket_codigo         = module.bucket_ejecucion_dataflow.nombre
  email_cuenta_servicio = module.rating_functions_sa.email_cuenta_servicio
  id_conector_vpc       = module.vpc_portal.vpc_connector_id

  configuracion_ingress = "ALLOW_INTERNAL_ONLY"
  acceso_publico        = false

  variables_entorno = {
    DB_HOST                      = module.cloudsql_portal.private_ip
    DB_NAME                      = module.cloudsql_portal.database_name
    DB_USER                      = module.cloudsql_portal.db_user
    SENDGRID_FROM_EMAIL          = var.sendgrid_from_email
    RECEPCION_EMAIL_FUNCTION_URL = module.fn_recepcion_email.url_funcion
  }

  secretos_entorno = {
    DB_PASSWORD      = { secret = module.secretos_proyecto.ids_secretos["portal-api-db-password"], version = "latest" }
    JWT_SECRET_KEY   = { secret = module.secretos_proyecto.ids_secretos["portal-api-jwt-secret-key"], version = "latest" }
    SENDGRID_API_KEY = { secret = module.secretos_proyecto.ids_secretos["sendgrid-api-key"], version = "latest" }
  }

  depends_on = [
    module.rating_functions_sa,
    module.vpc_portal,
    module.cloudsql_portal,
    module.secretos_proyecto,
    module.frontend_usuarios,
  ]
}

module "fn_recepcion_email" {
  source                = "./modules/cloud_run_function"
  id_proyecto           = var.id_proyecto
  region                = var.region
  nombre_funcion        = "recepcion-valoracion-email"
  descripcion           = "Recibe la valoración de un evento desde el email y la guarda en BigQuery"
  runtime               = "python312"
  punto_entrada         = "recibir_valoracion"
  ruta_codigo           = "${path.root}/../backend/valoracion/recepcion_email"
  bucket_codigo         = module.bucket_ejecucion_dataflow.nombre
  email_cuenta_servicio = module.rating_functions_sa.email_cuenta_servicio

  configuracion_ingress = "ALLOW_ALL"
  acceso_publico        = true

  variables_entorno = {
    GOOGLE_CLOUD_PROJECT = var.id_proyecto
    BQ_DATASET_ID        = module.bigquery.id_dataset
    BQ_TABLE_ID          = "valoraciones_eventos"
  }

  secretos_entorno = {
    JWT_SECRET_KEY = { secret = module.secretos_proyecto.ids_secretos["portal-api-jwt-secret-key"], version = "latest" }
  }

  depends_on = [
    module.rating_functions_sa,
    module.bigquery,
    module.secretos_proyecto,
  ]
}
resource "google_pubsub_topic" "topic" {
  project                    = var.id_proyecto
  name                       = var.nombre_topic
  labels                     = var.etiquetas
  message_retention_duration = var.duracion_retencion == "" ? null : var.duracion_retencion
}

resource "google_pubsub_topic_iam_member" "publicadores" {
  for_each = toset(var.publicadores)

  project = var.id_proyecto
  topic   = google_pubsub_topic.topic.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${each.value}"
}

data "google_project" "current" {
  count      = var.habilitar_dlq ? 1 : 0
  project_id = var.id_proyecto
}

locals {
  pubsub_service_agent   = var.habilitar_dlq ? "service-${data.google_project.current[0].number}@gcp-sa-pubsub.iam.gserviceaccount.com" : ""
  nombre_dlq             = "${var.nombre_topic}-dlq"
  nombre_suscripcion_dlq = "${var.nombre_topic}-dlq-sub"
}

resource "google_pubsub_topic" "dlq" {
  count = var.habilitar_dlq ? 1 : 0

  project                    = var.id_proyecto
  name                       = local.nombre_dlq
  message_retention_duration = var.duracion_retencion_dlq
}

resource "google_pubsub_topic_iam_member" "dlq_publisher" {
  count = var.habilitar_dlq ? 1 : 0

  project = var.id_proyecto
  topic   = google_pubsub_topic.dlq[0].name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${local.pubsub_service_agent}"
}

resource "google_pubsub_subscription" "main" {
  count = var.nombre_suscripcion != "" ? 1 : 0

  project                    = var.id_proyecto
  name                       = var.nombre_suscripcion
  topic                      = google_pubsub_topic.topic.name
  ack_deadline_seconds       = var.ack_deadline_seconds
  message_retention_duration = var.message_retention_duration_suscripcion

  dynamic "retry_policy" {
    for_each = var.habilitar_dlq ? [1] : []
    content {
      minimum_backoff = var.minimum_backoff
      maximum_backoff = var.maximum_backoff
    }
  }

  dynamic "dead_letter_policy" {
    for_each = var.habilitar_dlq ? [1] : []
    content {
      dead_letter_topic     = google_pubsub_topic.dlq[0].id
      max_delivery_attempts = var.max_delivery_attempts
    }
  }

  depends_on = [
    google_pubsub_topic_iam_member.dlq_publisher
  ]
}

resource "google_pubsub_subscription_iam_member" "main_subscriber" {
  count = var.habilitar_dlq && var.nombre_suscripcion != "" ? 1 : 0

  project      = var.id_proyecto
  subscription = google_pubsub_subscription.main[0].name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${local.pubsub_service_agent}"
}

resource "google_pubsub_subscription" "dlq" {
  count = var.habilitar_dlq ? 1 : 0

  project                    = var.id_proyecto
  name                       = local.nombre_suscripcion_dlq
  topic                      = google_pubsub_topic.dlq[0].name
  ack_deadline_seconds       = var.ack_deadline_seconds
  message_retention_duration = var.duracion_retencion_dlq
}

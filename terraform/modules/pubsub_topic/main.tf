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

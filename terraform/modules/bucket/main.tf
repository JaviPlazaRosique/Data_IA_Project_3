resource "google_storage_bucket" "bucket" {
  name                        = var.nombre
  project                     = var.id_proyecto
  location                    = var.ubicacion
  storage_class               = var.clase_almacenamiento
  uniform_bucket_level_access = true
  force_destroy               = var.forzar_eliminacion

  versioning {
    enabled = var.versionado
  }

  dynamic "lifecycle_rule" {
    for_each = var.reglas_ciclo_vida
    content {
      action {
        type          = lifecycle_rule.value.tipo_accion
        storage_class = lookup(lifecycle_rule.value, "clase_destino", null)
      }
      condition {
        age                = lookup(lifecycle_rule.value, "edad_dias", null)
        num_newer_versions = lookup(lifecycle_rule.value, "versiones_recientes", null)
        with_state         = lookup(lifecycle_rule.value, "estado_objeto", null)
      }
    }
  }

  dynamic "retention_policy" {
    for_each = var.periodo_retencion_segundos != null ? [1] : []
    content {
      retention_period = var.periodo_retencion_segundos
    }
  }

  labels = var.etiquetas
}

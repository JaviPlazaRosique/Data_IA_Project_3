resource "google_secret_manager_secret" "secreto" {
  for_each  = var.secretos
  secret_id = each.key
  project   = var.id_proyecto

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "version" {
  for_each    = var.secretos
  secret      = google_secret_manager_secret.secreto[each.key].id
  secret_data = each.value
}

locals {
  accesos = {
    for pair in setproduct(keys(var.secretos), var.nombres_cuentas_servicio) :
    "${pair[0]}--${pair[1]}" => { secret_id = pair[0], index = index(var.nombres_cuentas_servicio, pair[1]) }
  }
}

resource "google_secret_manager_secret_iam_member" "acceso" {
  for_each  = local.accesos
  project   = var.id_proyecto
  secret_id = google_secret_manager_secret.secreto[each.value.secret_id].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.cuentas_servicio_acceso[each.value.index]}"
}

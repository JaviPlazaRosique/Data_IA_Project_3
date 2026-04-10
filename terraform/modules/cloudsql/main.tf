resource "google_sql_database_instance" "instance" {
  name                = var.nombre_instancia_bd
  project             = var.id_proyecto
  region              = var.region
  database_version    = var.version_bd
  deletion_protection = var.proteccion_borrado

  depends_on = [
    var.conexion_vpc_privada
  ]

  settings {
    tier              = var.nivel_bd
    availability_type = var.tipo_disponibilidad_bd

    ip_configuration {
      ipv4_enabled    = var.ipv4_habilitado
      private_network = var.id_red
    }

    backup_configuration {
      enabled    = var.backup_habilitado
      start_time = var.hora_inicio_backup
    }
  }
}

resource "google_sql_database" "database" {
  name     = var.nombre_base_datos
  project  = var.id_proyecto
  instance = google_sql_database_instance.instance.name
}

resource "google_sql_user" "db_user" {
  name     = var.usuario_bd
  project  = var.id_proyecto
  instance = google_sql_database_instance.instance.name
  password = var.contrasena_bd
}

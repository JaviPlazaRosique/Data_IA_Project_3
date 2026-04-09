resource "google_sql_database_instance" "instance" {
  name             = var.db_instance_name
  project          = var.id_proyecto
  region           = var.region
  database_version = "POSTGRES_15"
  deletion_protection = var.deletion_protection

  depends_on = [var.private_vpc_connection]

  settings {
    tier              = var.db_tier
    availability_type = var.db_availability_type

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
    }

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }
  }
}

resource "google_sql_database" "database" {
  name     = var.database_name
  project  = var.id_proyecto
  instance = google_sql_database_instance.instance.name
}

resource "google_sql_user" "api_user" {
  name     = var.db_user
  project  = var.id_proyecto
  instance = google_sql_database_instance.instance.name
  password = var.db_password
}

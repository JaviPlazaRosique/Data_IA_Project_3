resource "google_project_service" "apis" {
  for_each           = toset(var.gcp_services)
  service            = each.key
  disable_on_destroy = false
}
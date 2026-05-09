terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}

resource "google_model_armor_template" "plantilla" {
  project     = var.id_proyecto
  location    = var.region
  template_id = var.id_template

  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = var.confianza_pi_jailbreak
    }

    rai_settings {
      rai_filters {
        filter_type      = "DANGEROUS"
        confidence_level = var.confianza_rai
      }
      rai_filters {
        filter_type      = "HARASSMENT"
        confidence_level = var.confianza_rai
      }
      rai_filters {
        filter_type      = "HATE_SPEECH"
        confidence_level = var.confianza_rai
      }
      rai_filters {
        filter_type      = "SEXUALLY_EXPLICIT"
        confidence_level = var.confianza_rai
      }
    }

    sdp_settings {
      basic_config {
        filter_enforcement = var.habilitar_sdp ? "ENABLED" : "DISABLED"
      }
    }

    malicious_uri_filter_settings {
      filter_enforcement = var.habilitar_uri_malicioso ? "ENABLED" : "DISABLED"
    }
  }
}

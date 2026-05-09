variable "id_proyecto" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Región donde crear la plantilla de Model Armor (debe coincidir con la región del backend que la consume)"
  type        = string
}

variable "id_template" {
  description = "ID de la plantilla de Model Armor a crear"
  type        = string
}

variable "confianza_pi_jailbreak" {
  description = "Nivel de confianza mínimo para bloquear prompt injection y jailbreak. Valores válidos: LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH"
  type        = string
  default     = "MEDIUM_AND_ABOVE"

  validation {
    condition     = contains(["LOW_AND_ABOVE", "MEDIUM_AND_ABOVE", "HIGH"], var.confianza_pi_jailbreak)
    error_message = "confianza_pi_jailbreak debe ser uno de: LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH."
  }
}

variable "confianza_rai" {
  description = "Nivel de confianza mínimo para los filtros de Responsible AI (toxicidad, acoso, odio, contenido sexual). Valores válidos: LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH"
  type        = string
  default     = "MEDIUM_AND_ABOVE"

  validation {
    condition     = contains(["LOW_AND_ABOVE", "MEDIUM_AND_ABOVE", "HIGH"], var.confianza_rai)
    error_message = "confianza_rai debe ser uno de: LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH."
  }
}

variable "habilitar_sdp" {
  description = "Habilitar el filtro de Sensitive Data Protection (detecta y bloquea PII básica como emails, teléfonos, IBAN…)"
  type        = bool
  default     = true
}

variable "habilitar_uri_malicioso" {
  description = "Habilitar el filtro de URIs maliciosos (URLs catalogadas como phishing/malware)"
  type        = bool
  default     = true
}

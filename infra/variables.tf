variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "zone" {
  type = string
}

variable "service_account_email" {
  description = "Compte de service Compute par défaut, utilisé par la VM, Cloud Run et Cloud Scheduler"
  type        = string
  default     = "531392170598-compute@developer.gserviceaccount.com"
}

variable "vm_name" {
  description = "Nom de la VM du projet"
  type        = string
  default     = "liora-airline-de-sep26"
}

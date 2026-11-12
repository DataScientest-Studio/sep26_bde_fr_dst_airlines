# Rattache les ressources GCP déjà existantes (export) à cette configuration.
# Sans état Terraform, `terraform plan` afficherait tout en "création" : ces blocs permettent de
# comparer le code avec l'infra réelle (le plan reste en lecture seule tant qu'on ne fait pas `apply`).
# Une fois l'import appliqué, ce fichier peut être supprimé.

# Formats d'identifiant d'import (piégeux) :
# - IAM member : TROIS valeurs séparées par des ESPACES : "<ressource> <rôle> <membre>" (pas des "/").
# - Cloud Run v2 / Scheduler : projects/<p>/locations/<région>/... ; VM : projects/<p>/zones/<zone>/instances/<nom>.
# - Si la ressource n'existe pas (ou si la liaison IAM n'existe pas), le plan échoue : "Cannot find binding".
# Un import ne modifie RIEN dans GCP : il rattache seulement la ressource à l'état Terraform.
locals {
  sa_member = "serviceAccount:${var.service_account_email}"
  run_name  = "liora-airline-project-sep26-airlabs-collect"
}

# --- VM ---
import {
  to = module.vm.google_compute_instance.liora_airline_de_sep26
  id = "projects/${var.project_id}/zones/${var.zone}/instances/${var.vm_name}"
}

# --- Cloud Run ---
import {
  to = module.cloud_run.google_cloud_run_v2_service.airlabs_collect
  id = "projects/${var.project_id}/locations/${var.region}/services/${local.run_name}"
}

# --- Cloud Scheduler ---
import {
  to = module.scheduler.google_cloud_scheduler_job.collect_airlabs
  id = "projects/${var.project_id}/locations/${var.region}/jobs/Collect-AirLabs"
}

import {
  to = module.scheduler.google_cloud_scheduler_job.start_vm
  id = "projects/${var.project_id}/locations/${var.region}/jobs/Start_VM"
}

import {
  to = module.scheduler.google_cloud_scheduler_job.stop_vm
  id = "projects/${var.project_id}/locations/${var.region}/jobs/Stop_VM"
}

# --- Secret Manager ---
import {
  to = module.secrets.google_secret_manager_secret.airlabs_api_keys
  id = "projects/${var.project_id}/secrets/airlabs-api-keys"
}

import {
  to = module.secrets.google_secret_manager_secret.airlinebucket_credentials
  id = "projects/${var.project_id}/secrets/AIRLINEBUCKET_CREDENTIALS"
}

import {
  to = module.secrets.google_secret_manager_secret.airlinedb_password
  id = "projects/${var.project_id}/secrets/AIRLINEDB_PASSWORD"
}

import {
  to = module.secrets.google_secret_manager_secret_iam_member.airlabs_secret_access
  id = "projects/${var.project_id}/secrets/airlabs-api-keys roles/secretmanager.secretAccessor ${local.sa_member}"
}

# --- Pare-feu (id = projects/<p>/global/firewalls/<nom>) ---
import {
  to = module.networking.google_compute_firewall.default_allow_http
  id = "projects/${var.project_id}/global/firewalls/default-allow-http"
}

import {
  to = module.networking.google_compute_firewall.default_allow_https
  id = "projects/${var.project_id}/global/firewalls/default-allow-https"
}

import {
  to = module.networking.google_compute_firewall.default_allow_icmp
  id = "projects/${var.project_id}/global/firewalls/default-allow-icmp"
}

import {
  to = module.networking.google_compute_firewall.default_allow_internal
  id = "projects/${var.project_id}/global/firewalls/default-allow-internal"
}

import {
  to = module.networking.google_compute_firewall.default_allow_rdp
  id = "projects/${var.project_id}/global/firewalls/default-allow-rdp"
}

import {
  to = module.networking.google_compute_firewall.default_allow_ssh
  id = "projects/${var.project_id}/global/firewalls/default-allow-ssh"
}

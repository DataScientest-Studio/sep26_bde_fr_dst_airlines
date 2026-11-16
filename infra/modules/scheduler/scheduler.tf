resource "google_cloud_scheduler_job" "collect_airlabs" {
  name   = "Collect-AirLabs"
  region = var.region

  # Cron évalué dans time_zone (heure de Paris, le passage heure d'été/hiver est géré par GCP).
  schedule  = "0 1,3,7,9,11,13,15,17,19,21,23 * * *"
  time_zone = "Europe/Paris"

  attempt_deadline = "180s"

  retry_config {
    min_backoff_duration = "5s"
    max_backoff_duration = "3600s"
    max_doublings        = 5
    # "0s" = AUCUNE limite de durée de retry (seul le backoff est plafonné à 3600 s). Pas "0 retry" comme on pourrait le croire.
    max_retry_duration = "0s"
  }

  http_target {
    http_method = "POST"

    uri = "https://liora-airline-project-sep26-airlabs-collect-531392170598.europe-west1.run.app/"

    oidc_token {
      service_account_email = var.service_account_email

      # Doit être l'URL du service SANS chemin ni "/" final : Cloud Run compare l'audience du jeton OIDC à l'identique.
      # (l'URI ci-dessus, elle, finit par "/").
      audience = "https://liora-airline-project-sep26-airlabs-collect-531392170598.europe-west1.run.app"
    }
  }
}
# VM allumée de 8h à 21h (Paris) uniquement, pour limiter le coût. Les DAGs Airflow (8:30, 14:30, 20:30) doivent donc
# rester dans cette fenêtre. Les jobs appellent directement l'API Compute (POST .../start et .../stop).
resource "google_cloud_scheduler_job" "start_vm" {
  name   = "Start_VM"
  region = var.region

  schedule  = "0 8 * * *"
  time_zone = "Europe/Paris"

  attempt_deadline = "180s"

  retry_config {
    min_backoff_duration = "5s"
    max_backoff_duration = "3600s"
    max_doublings        = 5
    max_retry_duration   = "0s"
  }

  http_target {
    http_method = "POST"

    uri = "https://compute.googleapis.com/compute/v1/projects/${var.project_id}/zones/${var.zone}/instances/${var.vm_name}/start"

    # oauth_token (et non oidc_token) : l'API Compute est une API Google. L'OIDC ne sert que pour Cloud Run/Functions
    # ou un endpoint à nous. Le compte de service doit avoir le rôle compute.instanceAdmin (non géré ici).
    oauth_token {
      service_account_email = var.service_account_email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}
resource "google_cloud_scheduler_job" "stop_vm" {
  name   = "Stop_VM"
  region = var.region

  schedule  = "0 21 * * *"
  time_zone = "Europe/Paris"

  attempt_deadline = "180s"

  retry_config {
    min_backoff_duration = "5s"
    max_backoff_duration = "3600s"
    max_doublings        = 5
    max_retry_duration   = "0s"
  }

  http_target {
    http_method = "POST"

    uri = "https://compute.googleapis.com/compute/v1/projects/${var.project_id}/zones/${var.zone}/instances/${var.vm_name}/stop"

    oauth_token {
      service_account_email = var.service_account_email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}
resource "google_cloud_scheduler_job" "collect_airlabs" {
  name        = "Collect-AirLabs"
  description = "Trigger Cloud Run AirLabs collect"
  region      = "europe-west1"

  schedule  = "0 1,3,7,9,11,13,15,17,19,21,23 * * *"
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

    uri = "https://liora-airline-project-sep26-airlabs-collect-531392170598.europe-west1.run.app/"

    oidc_token {
      service_account_email = "531392170598-compute@developer.gserviceaccount.com"

      audience = "https://liora-airline-project-sep26-airlabs-collect-531392170598.europe-west1.run.app"
    }
  }
}
resource "google_cloud_scheduler_job" "start_vm" {
  name      = "Start_VM"
  region    = "europe-west1"

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

    uri = "https://compute.googleapis.com/compute/v1/projects/project-0845983d-30e1-47a7-a62/zones/europe-west1-c/instances/liora-airline-de-sep26/start"

    oauth_token {
      service_account_email = "531392170598-compute@developer.gserviceaccount.com"
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}
resource "google_cloud_scheduler_job" "stop_vm" {
  name      = "Stop_VM"
  region    = "europe-west1"

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

    uri = "https://compute.googleapis.com/compute/v1/projects/project-0845983d-30e1-47a7-a62/zones/europe-west1-c/instances/liora-airline-de-sep26/stop"

    oauth_token {
      service_account_email = "531392170598-compute@developer.gserviceaccount.com"
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}
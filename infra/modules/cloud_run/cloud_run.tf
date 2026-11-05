resource "google_cloud_run_v2_service" "airlabs_collect" {
  name     = "liora-airline-project-sep26-airlabs-collect"
  location = "europe-west1"

  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = "531392170598-compute@developer.gserviceaccount.com"

    timeout = "300s"

    scaling {
      min_instance_count = 0
      max_instance_count = 12
    }

    max_instance_request_concurrency = 1

    containers {
      image = "europe-west1-docker.pkg.dev/project-0845983d-30e1-47a7-a62/airline/airlabs-collect:31845cb298bc34d06cda3c661ca3e0a6060561eb"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }

        startup_cpu_boost = true
      }

      env {
        name = "AIRLABS_API_KEYS"

        value_source {
          secret_key_ref {
            secret  = "airlabs-api-keys"
            version = "latest"
          }
        }
      }

      startup_probe {
        failure_threshold = 1
        timeout_seconds   = 240
        period_seconds    = 240

        tcp_socket {
          port = 8080
        }
      }
    }

    labels = {
      "commit-sha" = "31845cb298bc34d06cda3c661ca3e0a6060561eb"
      "managed-by" = "github-actions"
    }

    annotations = {
      "run.googleapis.com/cpu-throttling"    = "true"
      "run.googleapis.com/sessionAffinity"   = "false"
      "run.googleapis.com/startup-cpu-boost" = "true"
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  labels = {
    "commit-sha" = "31845cb298bc34d06cda3c661ca3e0a6060561eb"
    "managed-by" = "github-actions"
  }
}
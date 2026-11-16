resource "google_cloud_run_v2_service" "airlabs_collect" {
  # deletion_protection vaut true par défaut (provider 6.x) : `terraform destroy` échouera tant qu'on ne le passe pas
  # à false ET qu'on n'a pas appliqué.
  name     = "liora-airline-project-sep26-airlabs-collect"
  location = var.region

  # INGRESS_TRAFFIC_ALL = joignable depuis Internet, mais PAS public : aucune liaison run.invoker pour allUsers n'existe
  # (vérifié par le plan). Ne JAMAIS en ajouter une : l'endpoint consomme le quota payant AirLabs.
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.service_account_email

    # Durée max d'une requête. La collecte pagine avec time.sleep(10) entre chaque page : ce délai doit rester
    # supérieur au temps de collecte, sinon Cloud Run coupe la requête.
    timeout = "300s"

    scaling {
      min_instance_count = 0
      max_instance_count = 12
    }

    # 1 requête à la fois par instance : le handler est synchrone et long (pagination + pauses), inutile d'en partager une.
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

        # true = CPU facturé/alloué seulement pendant les requêtes (équivalent de l'annotation cpu-throttling).
        # Ne pas remettre l'annotation run.googleapis.com/cpu-throttling : le provider v2 utilise cet attribut.
        cpu_idle          = true # CPU alloué uniquement pendant les requêtes
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
        # Sonde TCP très tolérante : 1 seul essai mais 240 s de délai, pour laisser le temps au démarrage à froid.
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
  }

  # Le workflow GitHub Actions (deploy-airlabs.yml) redéploie l'image et réécrit les labels à chaque push, et le déploiement
  # "source" a laissé build_config/scaling/nom de conteneur. On les ignore, sinon chaque déploiement créerait un écart.
  # Conséquence : l'image n'est PAS pilotée par Terraform.
  lifecycle {
    # Image et labels sont mis à jour par le workflow GitHub Actions (deploy-airlabs.yml)
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].name,
      template[0].containers[0].base_image_uri,
      build_config,
      scaling,
      template[0].labels,
      labels,
      client,
      client_version,
    ]
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
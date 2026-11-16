# Les secrets sont créés SANS google_secret_manager_secret_version : les valeurs ne sont donc jamais dans le state Terraform
# (qui est en clair). On les alimente à la main (console ou `gcloud secrets versions add`).
# replication auto {} = répliqué automatiquement par Google dans plusieurs régions.
resource "google_secret_manager_secret" "airlabs_api_keys" {
  secret_id = "airlabs-api-keys"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "airlinebucket_credentials" {
  secret_id = "AIRLINEBUCKET_CREDENTIALS"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "airlinedb_password" {
  secret_id = "AIRLINEDB_PASSWORD"

  replication {
    auto {}
  }
}

# _iam_member est ADDITIF : il ajoute un compte sans toucher aux autres. _iam_binding / _iam_policy sont AUTORITAIRES
# et retireraient tous les accès non déclarés ici : à éviter sur une infra importée.
resource "google_secret_manager_secret_iam_member" "airlabs_secret_access" {
  secret_id = google_secret_manager_secret.airlabs_api_keys.id

  role   = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:${var.service_account_email}"
}

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
resource "google_secret_manager_secret_iam_member" "airlabs_secret_access" {
  secret_id = google_secret_manager_secret.airlabs_api_keys.id

  role   = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:531392170598-compute@developer.gserviceaccount.com"
}
resource "google_secret_manager_secret_iam_member" "airlinebucket_secret_access" {
  secret_id = google_secret_manager_secret.airlinebucket_credentials.id

  role   = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:531392170598-compute@developer.gserviceaccount.com"
}

resource "google_secret_manager_secret_iam_member" "db_password_secret_access" {
  secret_id = google_secret_manager_secret.airlinedb_password.id

  role   = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:531392170598-compute@developer.gserviceaccount.com"
}
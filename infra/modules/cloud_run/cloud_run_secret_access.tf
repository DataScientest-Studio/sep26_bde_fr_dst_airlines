resource "google_secret_manager_secret_iam_member" "cloud_run_secret_access" {
  secret_id = google_secret_manager_secret.airlabs_api_keys.id

  role = "roles/secretmanager.secretAccessor"

  member = "serviceAccount:531392170598-compute@developer.gserviceaccount.com"
}
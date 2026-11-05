resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = "europe-west1"

  name = google_cloud_run_v2_service.airlabs_collect.name

  role   = "roles/run.invoker"
  member = "allUsers"
}
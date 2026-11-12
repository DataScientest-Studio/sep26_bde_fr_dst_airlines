output "url" {
  description = "URL du service de collecte AirLabs (non publique : appel authentifié uniquement)"
  value       = google_cloud_run_v2_service.airlabs_collect.uri
}

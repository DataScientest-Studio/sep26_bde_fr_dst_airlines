# Valeurs affichées à la fin d'un `terraform apply` (ou avec `terraform output`).

output "vm_external_ip" {
  description = "IP publique de la VM"
  value       = module.vm.external_ip
}

output "cloud_run_url" {
  description = "URL du service Cloud Run de collecte AirLabs"
  value       = module.cloud_run.url
}

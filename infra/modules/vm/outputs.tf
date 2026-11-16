output "instance_name" {
  description = "Nom de la VM (utilisé par le module scheduler pour la démarrer/l'arrêter)"
  value       = google_compute_instance.liora_airline_de_sep26.name
}

output "external_ip" {
  description = "IP publique de la VM. Change si la VM est recréée (pas d'IP statique réservée)."
  value       = google_compute_instance.liora_airline_de_sep26.network_interface[0].access_config[0].nat_ip
}

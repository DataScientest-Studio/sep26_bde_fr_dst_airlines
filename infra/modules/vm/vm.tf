resource "google_compute_instance" "liora_airline_de_sep26" {
  name         = var.vm_name
  machine_type = "e2-standard-2"
  zone         = var.zone

  description    = ""
  can_ip_forward = false
  # À GARDER à "NONE" : sans cette ligne Terraform veut le remettre à null, ce qui FORCE le remplacement de la VM
  # (détruite puis recréée). Détecté par `terraform plan`.
  key_revocation_action_type = "NONE"
  # false : on peut supprimer la VM d'un clic ou d'un apply. À passer à true une fois l'infra stabilisée.
  deletion_protection = false

  labels = {
    goog-ops-agent-policy = "v2-template-1-7-0"
  }

  boot_disk {
    # false = le disque SURVIT à la suppression de la VM (données PostgreSQL/Docker). Ne pas passer à true.
    auto_delete = false

    initialize_params {
      # GCP renvoie l'URL complète de l'image, d'où un écart cosmétique avec cette forme courte. boot_disk est dans
      # ignore_changes (voir plus bas) : ne pas "corriger" ça, Terraform voudrait recréer la VM.
      image = "debian-cloud/debian-13-trixie-v20261006"
      size  = 150
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = "default"

    access_config {
      network_tier = "PREMIUM"
    }
  }

  service_account {
    email = var.service_account_email

    # Scope cloud-platform = tous les services Google ; ce sont les rôles IAM du compte de service qui limitent réellement.
    scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }

  metadata = {
    enable-osconfig = "TRUE"
  }

  # Ces tags activent les règles de pare-feu default-allow-http (80) et default-allow-https (443), voir firewall.tf.
  # Sans tag, la VM n'est joignable que par SSH/ICMP/réseau interne.
  tags = [
    "http-server",
    "https-server"
  ]

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
    provisioning_model  = "STANDARD"
  }

  shielded_instance_config {
    enable_secure_boot          = false
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  lifecycle {
    # Les clés SSH (metadata.ssh-keys) sont gérées dans GCP, pas ici : on ne les écrase jamais.
    ignore_changes = [metadata, boot_disk, labels]
  }

  confidential_instance_config {
    enable_confidential_compute = false
  }
}
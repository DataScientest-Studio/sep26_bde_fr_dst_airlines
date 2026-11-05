resource "google_compute_instance" "liora_airline_de_sep26" {
  name         = "liora-airline-de-sep26"
  machine_type = "e2-standard-2"
  zone         = "europe-west1-c"

  description         = ""
  can_ip_forward      = false
  deletion_protection = false

  labels = {
    goog-ops-agent-policy = "v2-template-1-7-0"
  }

  boot_disk {
    auto_delete = false

    initialize_params {
      image = "debian-cloud/debian-13-trixie-v20261006"
      size = 150
      type = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = "default"

    access_config {
      network_tier = "PREMIUM"
    }
  }

  service_account {
    email = "531392170598-compute@developer.gserviceaccount.com"

    scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }

  metadata = {
    enable-osconfig = "TRUE"

    ssh-keys = <<EOT
herve_cyr:ssh-rsa AAAAB3Nza...
github-deploy:ssh-rsa AAAAB3Nza...
pascal:ssh-ed25519 AAAAC3Nz...
EOT
  }

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
    enable_vtpm                = true
    enable_integrity_monitoring = true
  }

  confidential_instance_config {
    enable_confidential_compute = false
  }
}
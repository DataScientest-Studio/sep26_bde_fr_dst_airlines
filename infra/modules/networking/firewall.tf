# Règles de pare-feu du réseau "default", exportées telles quelles depuis GCP (aucun changement).
#
# À savoir :
# - Seuls les ports 80 et 443 sont ouverts à Internet, et UNIQUEMENT pour les VM portant les tags
#   "http-server" / "https-server" (c'est le cas de la VM liora-airline-de-sep26, voir modules/vm).
# - Airflow (8080), JupyterHub (8888), Streamlit (8501), l'API (8000) et PostgreSQL (5432) n'ont AUCUNE
#   règle : ils ne sont joignables que depuis l'intérieur du VPC ou par tunnel SSH.
# - Priorité : plus le nombre est petit, plus la règle passe en premier. 1000 = règles métier,
#   65534 = règles par défaut de GCP.

resource "google_compute_firewall" "default_allow_http" {
  name        = "default-allow-http"
  network     = "default"
  direction   = "INGRESS"
  priority    = 1000
  description = ""

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server"] # ne s'applique qu'aux VM taguées

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
}

resource "google_compute_firewall" "default_allow_https" {
  name        = "default-allow-https"
  network     = "default"
  direction   = "INGRESS"
  priority    = 1000
  description = ""

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["https-server"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

resource "google_compute_firewall" "default_allow_icmp" {
  name        = "default-allow-icmp"
  network     = "default"
  direction   = "INGRESS"
  priority    = 65534
  description = "Allow ICMP from anywhere"

  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "icmp"
  }
}

resource "google_compute_firewall" "default_allow_internal" {
  name        = "default-allow-internal"
  network     = "default"
  direction   = "INGRESS"
  priority    = 65534
  description = "Allow internal traffic on the default network"

  # 10.128.0.0/9 = tous les sous-réseaux auto-créés du réseau "default" (toutes régions)
  source_ranges = ["10.128.0.0/9"]

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }
}

# ATTENTION : RDP (3389) ouvert à tout Internet alors que la VM est un Debian (pas de RDP).
# Règle inutile et à risque : candidate à la suppression (supprimer le bloc puis terraform apply).
resource "google_compute_firewall" "default_allow_rdp" {
  name        = "default-allow-rdp"
  network     = "default"
  direction   = "INGRESS"
  priority    = 65534
  description = "Allow RDP from anywhere"

  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["3389"]
  }
}

# ATTENTION : SSH (22) ouvert à tout Internet. Les clés SSH protègent l'accès, mais on peut restreindre
# à l'IP du groupe, ou passer par IAP (plage 35.235.240.0/20 + `gcloud compute ssh --tunnel-through-iap`).
resource "google_compute_firewall" "default_allow_ssh" {
  name        = "default-allow-ssh"
  network     = "default"
  direction   = "INGRESS"
  priority    = 65534
  description = "Allow SSH from anywhere"

  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

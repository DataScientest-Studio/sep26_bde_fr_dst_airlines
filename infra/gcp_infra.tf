#
# Code Terraform pour creation de la VM GCP
#
###########################################################################
# Terraform 4.25.0


resource "google_compute_instance" "liora-airline-de-sep26" {
  boot_disk {
    device_name = "liora-airline-de-sep26"
  }
  confidential_instance_config {
    enable_confidential_compute = false
  }
  description = ""
  instance_encryption_key {
  }
  key_revocation_action_type = "NONE"
  machine_type               = "e2-standard-2"
  name                       = "liora-airline-de-sep26"
  network_interface {
    access_config {
      network_tier = "PREMIUM"
    }
    stack_type         = "IPV4_ONLY"
    subnetwork         = "projects/project-0845983d-30e1-47a7-a62/regions/europe-west1/subnetworks/default"
    subnetwork_project = "project-0845983d-30e1-47a7-a62"
  }
  reservation_affinity {
    type = "ANY_RESERVATION"
  }
  scheduling {
    on_host_maintenance = "MIGRATE"
    provisioning_model  = "STANDARD"
  }
  service_account {
    email  = "531392170598-compute@developer.gserviceaccount.com"
    scopes = ["https://www.googleapis.com/auth/devstorage.read_only", "https://www.googleapis.com/auth/logging.write", "https://www.googleapis.com/auth/monitoring.write", "https://www.googleapis.com/auth/service.management.readonly", "https://www.googleapis.com/auth/servicecontrol", "https://www.googleapis.com/auth/trace.append"]
  }
  tags = []
  zone = "europe-west1-c"
}

module "ops_agent_policy" {
  source          = "github.com/terraform-google-modules/terraform-google-cloud-operations/modules/ops-agent-policy"
  project         = "project-0845983d-30e1-47a7-a62"
  zone            = "europe-west1-c"
  assignment_id   = "goog-ops-agent-v2-template-1-7-0-europe-west1-c"
  agents_rule = {
    package_state = "installed"
    version = "latest"
  }
  instance_filter = {
    all = false
    inclusion_labels = [{
      labels = {
        goog-ops-agent-policy = "v2-template-1-7-0"
      }
    }]
  }
}

terraform {
  # Les blocs import {} avec identifiants dynamiques (voir imports.tf) exigent Terraform >= 1.6.
  required_version = ">= 1.10"

  required_providers {
    google = {
      source = "hashicorp/google"
      # ~> 6.0 = toute version 6.x (jamais 7). La version exacte est figée dans .terraform.lock.hcl : commiter ce fichier.
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
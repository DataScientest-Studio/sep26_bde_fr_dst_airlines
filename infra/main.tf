module "networking" {
  source = "./modules/networking"
}

module "secrets" {
  source = "./modules/secrets"

  service_account_email = var.service_account_email
}

module "vm" {
  source = "./modules/vm"

  vm_name               = var.vm_name
  zone                  = var.zone
  service_account_email = var.service_account_email
}

module "cloud_run" {
  source = "./modules/cloud_run"

  project_id            = var.project_id
  region                = var.region
  service_account_email = var.service_account_email
}

module "scheduler" {
  source = "./modules/scheduler"

  project_id            = var.project_id
  region                = var.region
  zone                  = var.zone
  vm_name               = module.vm.instance_name
  service_account_email = var.service_account_email
}

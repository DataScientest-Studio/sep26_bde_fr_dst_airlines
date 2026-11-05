module "vm" {
  source = "./modules/vm"
}

module "cloud_run" {
  source = "./modules/cloud_run"
}

module "scheduler" {
  source = "./modules/scheduler"
}
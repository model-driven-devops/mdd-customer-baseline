terraform {
  source = "../../../modules/cisco_router"
}

inputs = {
  subnet_id     = "subnet-0a6b13464deb98b0a"
  router_name   = "uno-dev-us-battalion-router"
  environment   = "battalion"
  primary_private_ip  = "172.23.2.4"
  secondary_private_ip = "172.23.2.5"
}
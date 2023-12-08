terraform {
  source = "../../../modules/cisco_router"
}

inputs = {
  subnet_id     = "subnet-09e66852c1b3f5178"
  router_name   = "uno-dev-uk-battalion-router"
  environment   = "battalion"
  primary_private_ip  = "172.23.3.4"
  secondary_private_ip = "172.23.3.5"
}
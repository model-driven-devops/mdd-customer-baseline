terraform {
  source = "../../../modules/cisco_router"
}

inputs = {
  subnet_id     = "subnet-0a6b13464deb98b0a"
  router_name   = "uno-dev-uk-battalion-router"
  environment   = "battalion"
}
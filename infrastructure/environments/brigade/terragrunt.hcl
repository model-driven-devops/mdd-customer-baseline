terraform {
  source = "../../modules/cisco_router"
}

inputs = {
  subnet_id     = "subnet-0e250717ed0506b1f"
  router_name   = "uno-dev-brigade-router"
  environment   = "brigade"
}
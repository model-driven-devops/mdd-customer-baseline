terraform {
  source = "../../modules/cisco_router"
}
inputs = {
    subnet_id   = "subnet-03f0165177077bde3"
    router_name = "uno-dev-division-router"
    environment = "division"
    primary_private_ip  = "172.23.0.4"
    secondary_private_ip = "172.23.0.5"
  }

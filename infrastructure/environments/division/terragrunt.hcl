terraform {
  source = "../../modules/cisco_router"
}
inputs = {
    subnet_id   = "subnet-03f0165177077bde3"
    router_name = "uno-dev-division-router"
    environment = "division"
  }

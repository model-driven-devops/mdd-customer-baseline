terraform {
  source = "../../../modules/cisco_router"
}

inputs = {
  subnet_id     = "subnet-00799ac62a3cb6d86"
	router_name   = "uno-dev-us-company-router"
  environment   = "company"
  primary_private_ip  = "172.23.4.4"
  secondary_private_ip = "172.23.4.5"
}
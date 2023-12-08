terraform {
  source = "../../../modules/cisco_router"
}

inputs = {
  subnet_id     = "subnet-0d10067812c364e81"
	router_name   = "uno-dev-uk-company-router"
  environment   = "company"
  primary_private_ip  = "172.23.5.4"
  secondary_private_ip = "172.23.5.5"
}
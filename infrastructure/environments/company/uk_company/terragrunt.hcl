terraform {
  source = "../../../modules/cisco_router"
}

inputs = {
  subnet_id     = "subnet-09e66852c1b3f5178"
	router_name   = "uno-dev-uk-company-router"
  environment   = "company"
}
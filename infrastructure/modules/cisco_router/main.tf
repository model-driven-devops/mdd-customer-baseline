resource "aws_instance" "cisco_router" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id
  key_name      = var.key_name
  vpc_security_group_ids = ["sg-0e8ceb25d639b99e0"]

  user_data = file("${path.cwd}/user_data.txt")

metadata_options {
  http_endpoint = "enabled"
  http_tokens   = "optional"
  http_put_response_hop_limit = 1
}

tags = {
    Name = var.router_name
  }
}
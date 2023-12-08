resource "aws_instance" "cisco_router" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id
  key_name      = var.key_name
  vpc_security_group_ids = ["sg-0e8ceb25d639b99e0"]

  private_ip = var.primary_private_ip  # Static private IP for the primary interface

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

# Secondary Network Interface Resource
resource "aws_network_interface" "secondary_nic" {
  subnet_id       = var.subnet_id
  private_ips     = [var.secondary_private_ip]
  security_groups = ["sg-0e8ceb25d639b99e0"]

  tags = {
    Name = "${var.router_name}-mgmt-int"
  }
}

# Attachment of the Secondary Network Interface to the Cisco Router Instance
resource "aws_network_interface_attachment" "secondary_nic_attachment" {
  instance_id          = aws_instance.cisco_router.id
  network_interface_id = aws_network_interface.secondary_nic.id
  device_index         = 1
}
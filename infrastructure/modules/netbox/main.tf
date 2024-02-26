resource "aws_instance" "ubuntu" {
  count         = var.instance_count
  ami           = var.ami
  instance_type = var.instance_type
  subnet_id     = var.subnet_id
  key_name      = var.key_name # This uses the variable

   vpc_security_group_ids  = var.security_group_ids

  root_block_device {
    volume_size = 30
  }

  tags = {
    Name = var.instance_name
  }
}

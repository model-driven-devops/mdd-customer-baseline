module "ec2" {
  source = "./modules/ec2"

  ami              = "ami-0a6b0c60f2476df25"
  instance_type    = "t3.medium"
  key_name         = "lee.vanginkel.uno.key"
  subnet_id        = "subnet-00d6843b742a58e8c"
  security_group_id = "sg-08ef4beced03030ff"
}

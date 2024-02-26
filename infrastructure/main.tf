terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
    }
    http = {
      source  = "hashicorp/http"
    }
  }
  required_version = ">= 0.14"

	backend "s3" {
    bucket         = "mdd-terraform-state"
    key            = "state/terraform.tfstate"
    region         = "us-gov-west-1" # Ensure this matches the region where you've created your S3 bucket
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

module "s3" {
  source = "./modules/s3"
}

module "nso" {
 	source         = "./modules/nso"
  instance_count = 1
  ami            = "ami-0535f9626f79a1689"
  instance_type  = "t3.large"
  subnet_id      = "subnet-68debf1e" # Replace with your actual subnet ID
	key_name       = "lvangink_army_key"
	instance_name  = "nso.army"
  security_group_ids = ["sg-0361251d34fcf0587"]
}

module "netbox" {
 	source         = "./modules/netbox"
  instance_count = 1
  ami            = "ami-0535f9626f79a1689"
  instance_type  = "t3.large"
  subnet_id      = "subnet-68debf1e" # Replace with your actual subnet ID
	key_name       = "lvangink_army_key"
	instance_name  = "netbox.army"
	security_group_ids = ["sg-0361251d34fcf0587"]
}


variable "ami_id" {
  description = "The AMI ID for the Cisco router"
  type        = string
  default     = "ami-08d5339b04462f800"
}

variable "instance_type" {
  description = "The instance type for the Cisco router"
  type        = string
	default     = "t3.medium"
}

variable "key_name" {
  description = "The key name of the AWS Key Pair"
  type        = string
  default     = "lee.vanginkel.uno.key"
}

# environment specefic inputs

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "subnet_id" {
  description = "The subnet ID where the Cisco router will be deployed"
  type        = string
}

variable "router_name" {
  description = "The name of the Cisco router"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-gov-west-1" 
}

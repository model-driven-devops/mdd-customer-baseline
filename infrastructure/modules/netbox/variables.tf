# variables.tf in your EC2 module directory

variable "instance_count" {
  description = "Number of instances to launch"
  type        = number
}

variable "ami" {
  description = "The AMI ID to use for the instances"
  type        = string
}

variable "instance_type" {
  description = "The instance type of the EC2 instance"
  type        = string
}

variable "subnet_id" {
  description = "The VPC Subnet ID to launch the instances in"
  type        = string
}

variable "key_name" {
  description = "The key name of the SSH key to attach to the instances"
  type        = string
}

variable "instance_name" {
  description = "The key name of the SSH key to attach to the instances"
  type        = string
}

variable "security_group_ids" {
  description = "A list of security group IDs to associate with the EC2 instance"
  type        = list(string)
}


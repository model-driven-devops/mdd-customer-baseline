subnet_id           = "subnet-03f0165177077bde3"
key_name            = "lee.vanginkel.uno.key"
security_group_id   = "sg-0949c533f887482b8"

instances = {
  "uno.cisco.nso" = {
    ami          = "ami-0a6b0c60f2476df25",
    instance_type= "t3.medium",
    volume_size  = 20
		private_ip	 = "172.23.0.40" 
  },
  "uno.cisco.netbox" = {
    ami          = "ami-0535f9626f79a1689",
    instance_type= "t3.large",
    volume_size  = 50
		private_ip	 = "172.23.0.41" 
  }
}
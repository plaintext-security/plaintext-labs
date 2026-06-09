# terraform.tfvars — Meridian infrastructure variables
# NOTE: Contains a deliberately planted FAKE private key for security training.
# This is not a real key and has no access to any system.

environment = "production"
region      = "us-east-1"

# MISCONFIGURATION: private key hardcoded in variables file
# This should reference a Vault path or AWS Secrets Manager ARN
db_admin_private_key = <<EOT
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xHn/ygWep4PAtEsHAMcBWFJKBqgBXIQkXmPY
nSxPBbCxCVNnFDN0iBTYfNbr5eXNOmBFMuIHIsBuMk0YnvVFaqPQ9RQYAAAAAA
BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
EXAMPLE-FAKE-KEY-FOR-TRAINING-PURPOSES-ONLY-NOT-A-REAL-PRIVATE-KEY=
-----END RSA PRIVATE KEY-----
EOT

db_instance_class = "db.t3.medium"

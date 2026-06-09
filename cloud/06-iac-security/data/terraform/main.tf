# Meridian Financial — legacy infrastructure module
# INTENTIONALLY MISCONFIGURED for security training.
# These misconfigurations represent real-world findings.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

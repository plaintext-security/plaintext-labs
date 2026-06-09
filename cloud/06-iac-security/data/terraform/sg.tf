# Security Groups — MISCONFIGURED: overly permissive ingress rules
# CIS AWS 5.2: Ensure no security groups allow ingress from 0.0.0.0/0 to port 22 (FAIL)
# CIS AWS 5.3: Ensure no security groups allow ingress from 0.0.0.0/0 to port 3389 (FAIL)
# checkov: CKV_AWS_24, CKV_AWS_25

resource "aws_security_group" "meridian_app" {
  name        = "meridian-app-sg"
  description = "Application security group"
  vpc_id      = "vpc-00000000"

  # MISCONFIGURED: SSH open to the world
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH — needs to be locked down to bastion CIDR"
  }

  # MISCONFIGURED: RDP open to the world
  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "RDP — legacy Windows instances, not yet migrated"
  }

  # Intentional: HTTPS to internet-facing ALB — justified suppression candidate
  # checkov:skip=CKV_AWS_260: Public HTTPS ingress is required for internet-facing ALB
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from internet — public ALB, intentional"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "meridian_db" {
  name        = "meridian-db-sg"
  description = "Database security group"
  vpc_id      = "vpc-00000000"

  # MISCONFIGURED: database port open to all
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "PostgreSQL — should be restricted to app-tier CIDR only"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

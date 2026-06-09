# EBS — MISCONFIGURED: no encryption
# CIS AWS 2.2.1: Ensure EBS volume encryption is enabled (FAIL)
# checkov: CKV_AWS_8, CKV_AWS_189

resource "aws_ebs_volume" "meridian_data_vol" {
  availability_zone = "us-east-1a"
  size              = 500
  type              = "gp3"

  # MISCONFIGURED: encryption not enabled
  encrypted = false

  tags = {
    Name = "meridian-data-volume"
  }
}

resource "aws_instance" "meridian_app_server" {
  ami           = "ami-0c02fb55956c7d316"  # Amazon Linux 2
  instance_type = "t3.medium"

  # MISCONFIGURED: no IMDSv2 enforcement
  metadata_options {
    http_endpoint = "enabled"
    # http_tokens = "required"  # IMDSv2 — should be required
  }

  # MISCONFIGURED: root volume not encrypted
  root_block_device {
    volume_size = 50
    encrypted   = false
  }

  vpc_security_group_ids = [aws_security_group.meridian_app.id]

  tags = {
    Name = "meridian-app-server"
  }
}

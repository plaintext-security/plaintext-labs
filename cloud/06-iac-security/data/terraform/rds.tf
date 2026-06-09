# RDS — MISCONFIGURED: no encryption, public accessibility
# CIS AWS 2.3.1: Ensure that encryption is enabled for RDS Instances (FAIL)
# checkov: CKV_AWS_17, CKV_AWS_133, CKV_AWS_157, CKV2_AWS_60

resource "aws_db_instance" "meridian_postgres" {
  identifier        = "meridian-app-db"
  engine            = "postgres"
  engine_version    = "15.3"
  instance_class    = "db.t3.medium"
  allocated_storage = 100
  db_name           = "meridianapp"
  username          = "dbadmin"
  password          = "changeme-before-deploy"  # placeholder, should come from Secrets Manager

  # MISCONFIGURED: no storage encryption
  storage_encrypted = false

  # MISCONFIGURED: publicly accessible
  publicly_accessible = true

  # MISCONFIGURED: no deletion protection
  deletion_protection = false

  # MISCONFIGURED: no backup retention
  backup_retention_period = 0

  # MISCONFIGURED: no multi-AZ
  multi_az = false

  # MISCONFIGURED: no enhanced monitoring
  # monitoring_interval = 0 (default)

  vpc_security_group_ids = [aws_security_group.meridian_db.id]

  skip_final_snapshot = true
}

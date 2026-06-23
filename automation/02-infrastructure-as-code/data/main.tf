terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
  required_version = ">= 1.6"
}

variable "env_name" {
  type        = string
  default     = "staging"
  description = "The environment name (staging, production, dev)."
}

resource "local_file" "environment_config" {
  filename = "${path.module}/output/environment.txt"
  content  = "env=${var.env_name}\nmanaged_by=opentofu\n"
}

resource "local_file" "asset_manifest" {
  filename = "${path.module}/output/assets.txt"
  content  = "# asset manifest\nenv=${var.env_name}\ngenerated=true\n"
}

output "config_path" {
  value       = local_file.environment_config.filename
  description = "Path to the generated environment config file."
}

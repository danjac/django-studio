# Hetzner Object Storage - database backups
#
# Provisions a private S3-compatible bucket for PostgreSQL backups.
# Uses the same project-level S3 credentials as terraform/storage/.
# The bucket is private — objects are not publicly accessible.
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply

terraform {
  required_version = ">= 1.0"

  required_providers {
    minio = {
      source  = "aminueza/minio"
      version = "~> 3.3"
    }
  }
}

provider "minio" {
  minio_server   = "${var.location}.your-objectstorage.com"
  minio_user     = var.access_key
  minio_password = var.secret_key
  minio_region   = var.location
  minio_ssl      = true
}

resource "minio_s3_bucket" "backups" {
  bucket = var.bucket_name
  acl    = "private"
}

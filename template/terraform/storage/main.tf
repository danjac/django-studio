# Hetzner Object Storage - media files
#
# Provisions an S3-compatible bucket for Django media uploads using the
# MinIO provider (Hetzner Object Storage is S3-compatible but not managed
# via the hcloud provider).
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

resource "minio_s3_bucket" "media" {
  bucket = var.bucket_name
  acl    = "public-read"

  lifecycle {
    prevent_destroy = true
  }
}

# Hetzner Object Storage - media files
#
# Provisions an S3-compatible bucket for Django media uploads using the
# MinIO provider (Hetzner Object Storage is S3-compatible but not managed
# via the hcloud provider).
#
# Usage:
#   terraform init
#   terraform apply
#
# Prerequisites: Create S3 credentials in the Hetzner console first:
#   Cloud > Security > S3 credentials
# Then export:
#   export TF_VAR_access_key=<your-access-key>
#   export TF_VAR_secret_key=<your-secret-key>
#
# After apply, set in your production environment:
#   HETZNER_STORAGE_ACCESS_KEY=<access-key>
#   HETZNER_STORAGE_SECRET_KEY=<secret-key>
#   HETZNER_STORAGE_BUCKET=<bucket-name>
#   HETZNER_STORAGE_ENDPOINT=https://<location>.your-objectstorage.com

terraform {
  required_providers {
    minio = {
      source  = "aminueza/minio"
      version = "~> 3.3"
    }
  }
}

variable "access_key" {
  description = "Hetzner Object Storage S3 access key"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Hetzner Object Storage S3 secret key"
  type        = string
  sensitive   = true
}

variable "bucket_name" {
  description = "Object storage bucket name (must be globally unique in the region)"
  type        = string
  default     = "{{cookiecutter.project_slug}}-media"
}

variable "location" {
  description = "Hetzner datacenter location (fsn1, nbg1, hel1, ash, hil)"
  type        = string
  default     = "fsn1"
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
}

output "bucket_name" {
  description = "Bucket name - set as HETZNER_STORAGE_BUCKET in production"
  value       = minio_s3_bucket.media.bucket
}

output "endpoint_url" {
  description = "S3-compatible endpoint - set as HETZNER_STORAGE_ENDPOINT in production"
  value       = "https://${var.location}.your-objectstorage.com"
}

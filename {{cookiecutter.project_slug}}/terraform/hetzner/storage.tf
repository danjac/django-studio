# Hetzner Object Storage — media files
#
# Provisions an S3-compatible bucket for Django media uploads.
# django-storages' S3Boto3Storage backend works with Hetzner's endpoint.
#
# Usage:
#   terraform init
#   terraform apply
#
# After apply, create S3 credentials in the Hetzner console:
#   Cloud > Security > S3 credentials
# Set the key/secret as HETZNER_STORAGE_ACCESS_KEY / HETZNER_STORAGE_SECRET_KEY
# in your production environment.

terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.49"
    }
  }
}

variable "hcloud_token" {
  description = "Hetzner Cloud API token"
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

provider "hcloud" {
  token = var.hcloud_token
}

resource "hcloud_object_storage_bucket" "media" {
  name     = var.bucket_name
  location = var.location
}

output "bucket_name" {
  description = "Bucket name — set as HETZNER_STORAGE_BUCKET in production"
  value       = hcloud_object_storage_bucket.media.name
}

output "endpoint_url" {
  description = "S3-compatible endpoint — set as HETZNER_STORAGE_ENDPOINT in production"
  value       = "https://${hcloud_object_storage_bucket.media.location}.your-objectstorage.com"
}

output "bucket_name" {
  description = "Bucket name - set as HETZNER_STORAGE_BUCKET in production"
  value       = minio_s3_bucket.media.bucket
}

output "endpoint_url" {
  description = "S3-compatible endpoint - set as HETZNER_STORAGE_ENDPOINT in production"
  value       = "https://${var.location}.your-objectstorage.com"
}

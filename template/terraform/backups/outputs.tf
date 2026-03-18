output "bucket_name" {
  description = "Bucket name - set as backupBucket in helm/site/values.secret.yaml"
  value       = minio_s3_bucket.backups.bucket
}

output "endpoint_url" {
  description = "S3-compatible endpoint - set as backupEndpoint in helm/site/values.secret.yaml"
  value       = "https://${var.location}.your-objectstorage.com"
}

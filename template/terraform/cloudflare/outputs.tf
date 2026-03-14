output "zone_id" {
  description = "Cloudflare zone ID"
  value       = data.cloudflare_zone.domain.id
}

output "zone_name" {
  description = "Cloudflare zone name"
  value       = data.cloudflare_zone.domain.name
}

output "nameservers" {
  description = "Cloudflare nameservers for this zone"
  value       = data.cloudflare_zone.domain.name_servers
}

output "server_record_name" {
  description = "DNS record name for the server"
  value       = cloudflare_record.server.hostname
}

output "server_record_value" {
  description = "DNS record value (IP address)"
  value       = cloudflare_record.server.content
}

output "dns_status" {
  description = "Cloudflare DNS status"
  value       = data.cloudflare_zone.domain.status
}

output "ssl_mode" {
  description = "Cloudflare SSL/TLS mode"
  value       = cloudflare_zone_settings_override.domain_settings.settings[0].ssl
}

output "origin_cert_pem" {
  description = "Cloudflare origin certificate PEM - paste into helm/site/values.secret.yaml under secrets.cloudflare.cert"
  value       = cloudflare_origin_ca_certificate.origin.certificate
}

output "origin_key_pem" {
  description = "Origin certificate private key PEM - paste into helm/site/values.secret.yaml under secrets.cloudflare.key"
  value       = tls_private_key.origin.private_key_pem
  sensitive   = true
}

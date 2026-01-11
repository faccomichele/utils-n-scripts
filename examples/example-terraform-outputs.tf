# Example Terraform outputs for use with deploy-website workflow

# Required outputs for the deploy-website workflow
output "website_bucket_name" {
  value       = aws_s3_bucket.website.id
  description = "The name of the S3 bucket for the website"
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.website.id
  description = "The ID of the CloudFront distribution"
}

# Additional outputs that can be used with placeholder replacement
output "api_endpoint" {
  value       = aws_api_gateway_deployment.api.invoke_url
  description = "API Gateway endpoint URL"
}

output "environment_name" {
  value       = var.environment
  description = "The environment name (dev, stg, prod)"
}

# Example of other outputs you might want to expose
output "user_pool_id" {
  value       = aws_cognito_user_pool.main.id
  description = "Cognito User Pool ID"
  sensitive   = false
}

output "region" {
  value       = var.region
  description = "AWS region where resources are deployed"
}

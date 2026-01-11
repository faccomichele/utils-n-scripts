# Examples

This directory contains example files demonstrating how to use the reusable workflows in this repository.

## Files

### complete-deployment-workflow.yml

A complete GitHub Actions workflow example showing how to chain together:
1. Lambda Build workflow - builds Lambda function packages
2. Terraform Run workflow - provisions AWS infrastructure
3. Deploy Website workflow - deploys static website with placeholder replacement

This example demonstrates:
- Building Lambda functions
- Running Terraform plan on pull requests
- Running Terraform apply on main branch
- Deploying website files to S3 after infrastructure is ready
- Automatic placeholder replacement in HTML/JS files

### example-terraform-outputs.tf

Example Terraform output configuration showing:
- Required outputs for the deploy-website workflow (`website_bucket_name`, `cloudfront_distribution_id`)
- Additional outputs that can be used with placeholder replacement
- Best practices for output descriptions

### example-website-index.html

Example HTML file demonstrating:
- Placeholder syntax using `__output_name__` format
- How to use replaced values in JavaScript
- Common use cases like API endpoints and configuration values

## Usage

### 1. Copy the workflow file to your repository

```bash
# Copy to your repository's .github/workflows directory
cp examples/complete-deployment-workflow.yml .github/workflows/deploy.yml
```

### 2. Configure Terraform outputs

Add the required outputs to your Terraform configuration:

```hcl
output "website_bucket_name" {
  value = aws_s3_bucket.website.id
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.website.id
}
```

### 3. Create website files with placeholders

In your website files (HTML, JS, CSS, etc.), use the placeholder format:

```html
<script>
  const API_URL = '__api_endpoint__';
</script>
```

### 4. Configure repository secrets

Set up the required secrets in your GitHub repository:
- `DEV_AWS_ID` - AWS Account ID for dev environment
- `DEV_ROLE_SECRET` - IAM role suffix for dev environment
- `CORE_TERRAFORM_ACCOUNT` - AWS Account ID for Terraform state
- `CORE_TERRAFORM_ROLE_SECRET` - IAM role suffix for Terraform state

### 5. Push your code

The workflow will automatically:
1. Build Lambda functions
2. Run Terraform plan (or apply on main)
3. Replace placeholders in your website files
4. Sync files to S3
5. Create CloudFront invalidations for changed files

## Placeholder Replacement

The deploy-website workflow automatically replaces placeholders in your files before uploading to S3.

### Supported format

```
__output_name__
```

Where `output_name` matches a Terraform output name.

### Example

Terraform output:
```hcl
output "api_endpoint" {
  value = "https://api.example.com"
}
```

HTML file before deployment:
```html
<script>const API = '__api_endpoint__';</script>
```

HTML file after deployment:
```html
<script>const API = 'https://api.example.com';</script>
```

### File types

Replacement works on all text files (detected using the `file` command):
- HTML files (`.html`)
- JavaScript files (`.js`)
- CSS files (`.css`)
- JSON files (`.json`)
- Text files (`.txt`)
- And other text-based formats

Binary files are automatically skipped.

## Directory Structure

Expected directory structure for your project:

```
your-repo/
├── .github/
│   └── workflows/
│       └── deploy.yml         # Your workflow file
├── terraform/
│   ├── main.tf
│   ├── outputs.tf             # Terraform outputs
│   └── lambda/                # Lambda function folders
│       ├── function1/
│       └── function2/
└── website/
    ├── index.html             # With __placeholder__ values
    ├── script.js
    └── styles.css
```

## Troubleshooting

### Placeholder not replaced

- Ensure the Terraform output name matches exactly (case-sensitive)
- Verify the file is text-based (not binary)
- Check that the workflow completed successfully
- Review the workflow logs for the "Parse Terraform outputs" step

### CloudFront invalidation not created

- Verify `cloudfront_distribution_id` output is present in Terraform
- Check IAM permissions include `cloudfront:CreateInvalidation`
- Review workflow logs for error messages

### S3 sync fails

- Verify `website_bucket_name` output is present in Terraform
- Check IAM permissions include `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`
- Ensure the bucket exists and is accessible

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Terraform Output Values](https://www.terraform.io/language/values/outputs)
- [AWS S3 Sync Command](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html)
- [CloudFront Invalidations](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html)

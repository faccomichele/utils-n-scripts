# Example: Process Config Templates with Terraform

This example shows how to use the config template processing workflow with Terraform deployment.

## Workflow Example

```yaml
name: Deploy with Config Processing

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  # First, process all .fmtcf template files
  process-configs:
    uses: faccomichele/utils-n-scripts/.github/workflows/process-fmtcf-files.yml@latest
    with:
      working-directory: './terraform'
      region: 'us-east-1'

  # Then run Terraform with the processed configs available
  terraform-plan:
    needs: process-configs
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@latest
    with:
      action: 'plan'
      environment: 'dev'
      region: 'us-east-1'
      working-directory: './terraform'
    secrets: inherit

  terraform-apply:
    if: github.ref == 'refs/heads/main'
    needs: terraform-plan
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@latest
    with:
      action: 'apply'
      environment: 'dev'
      region: 'us-east-1'
      working-directory: './terraform'
    secrets: inherit
```

## Directory Structure

```
terraform/
├── main.tf
├── variables.tf
├── config/
│   ├── app-config.json.fmtcf      # Template file
│   └── database-config.yaml.fmtcf  # Template file
└── modules/
    └── ...
```

## Template Files

### app-config.json.fmtcf
```json
{
  "environment": "ENV::ENVIRONMENT",
  "database": {
    "host": "ENV::DB_HOST",
    "username": "AWS-PARAMETER::db-username",
    "password": "AWS-SECRET::db-password"
  },
  "api": {
    "key": "AWS-PARAMETER::api-key",
    "endpoint": "https://api.example.com"
  }
}
```

### database-config.yaml.fmtcf
```yaml
database:
  host: ENV::DB_HOST
  port: 5432
  username: AWS-PARAMETER::db-username
  password: AWS-SECRET::db-password
  ssl: true
```

## Workflow Execution

1. **process-configs** job:
   - Finds all `.fmtcf` files in `./terraform`
   - Processes each file, replacing placeholders
   - Creates artifact `processed-configs-{run_id}` with:
     - `config/app-config.json`
     - `config/database-config.yaml`

2. **terraform-plan** job:
   - Downloads the `processed-configs-{run_id}` artifact automatically
   - Files are available at `./terraform/config/` before `terraform init`
   - Terraform can reference these files in configuration

3. **terraform-apply** job (on main branch):
   - Same as plan, but applies changes
   - Processed configs available throughout execution

## Using Processed Configs in Terraform

### Example: File Upload to S3

```hcl
resource "aws_s3_object" "app_config" {
  bucket = aws_s3_bucket.config.id
  key    = "app-config.json"
  source = "${path.module}/config/app-config.json"
  etag   = filemd5("${path.module}/config/app-config.json")
}
```

### Example: Lambda Environment from File

```hcl
locals {
  app_config = jsondecode(file("${path.module}/config/app-config.json"))
}

resource "aws_lambda_function" "app" {
  # ... other configuration ...
  
  environment {
    variables = {
      ENVIRONMENT = local.app_config.environment
      API_KEY     = local.app_config.api.key
      API_ENDPOINT = local.app_config.api.endpoint
    }
  }
}
```

## Benefits

1. **Separation of Concerns**: Keep sensitive values in AWS and environment variables
2. **Template Reusability**: Same templates work across environments with different values
3. **Security**: Secrets never stored in version control
4. **Automation**: Fully automated in CI/CD pipeline
5. **Flexibility**: Mix AWS and environment variable sources

## Requirements

- AWS credentials configured in GitHub Actions
- IAM permissions for SSM Parameter Store and Secrets Manager
- Environment variables set in GitHub Actions
- `.fmtcf` template files in your repository

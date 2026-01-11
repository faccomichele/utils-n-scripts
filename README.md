# Utils and Scripts

A collection of reusable utilities and scripts for infrastructure automation and DevOps workflows.

## Contents

This repository contains:

- **GitHub Actions Workflows**: Reusable workflows for common CI/CD tasks
- **Terraform Utilities**: Scripts for processing and formatting Terraform output

## GitHub Actions Workflows

### Lambda Build Workflow

Located in `.github/workflows/lambda-build.yml`, this is a reusable workflow for building Lambda function packages independently from Terraform operations.

#### Features

- Automatically detects Lambda functions in subfolders of the working directory
- Identifies build type based on file extensions (.py for Python, .js for Node.js)
- Builds Lambda packages concurrently using matrix strategy
- Python: Installs dependencies from `requirements.txt` using `pip`
- Node.js: Installs dependencies from `package.json` using `npm install --production`
- Creates individual zip packages for each Lambda function
- Uploads each Lambda package as a separate artifact
- Failed builds can be retried individually without rebuilding all Lambdas
- Minimal retention (1 day) to reduce storage costs

#### Usage

The Lambda Build workflow can be used standalone or combined with the Terraform Run workflow:

```yaml
name: Lambda and Terraform Deployment

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  lambda-build:
    uses: faccomichele/utils-n-scripts/.github/workflows/lambda-build.yml@main
    with:
      working-directory: './terraform'

  terraform-plan:
    needs: lambda-build
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@main
    with:
      action: 'plan'
      environment: 'dev'
      region: 'us-west-2'
      working-directory: './terraform'
      download-lambda-artifacts: true
    secrets: inherit
```

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `working-directory` | string | No | `'.'` | Directory containing the Lambda function subfolders |

#### Requirements

- Lambda functions should be in separate subfolders within the working directory
- Python Lambdas: Must contain at least one `.py` file; optional `requirements.txt` for dependencies
- Node.js Lambdas: Must contain at least one `.js` file; optional `package.json` for dependencies
- Each Lambda subfolder will be packaged into `<subfolder-name>.zip`

#### How It Works

1. **Detection**: Scans all subfolders in the working directory
2. **Classification**: Identifies build type based on file extensions
3. **Matrix Build**: Builds all Lambdas concurrently (fail-fast: false)
4. **Packaging**: Creates zip files with dependencies included
5. **Upload**: Each Lambda package uploaded as `lambda-<name>-<run-id>`

### Terraform Run Workflow

Located in `.github/workflows/terraform-run.yml`, this is a reusable workflow for running Terraform operations on AWS infrastructure.

#### Features

- Supports three Terraform actions: `plan`, `apply`, and `destroy`
- Multi-environment support (dev, staging, production)
- Multi-region AWS deployments
- Automatic Terraform state management using S3 backend
- Integration with AWS IAM roles via OIDC
- Automatic PR comments with Terraform plan summaries
- Detailed Markdown reports in GitHub job summaries
- Optional Lambda artifact integration (downloads pre-built Lambda packages)
- Backward compatible: runs `setup.sh` if no artifacts are provided

#### Usage

To use this workflow in your repository, create a workflow file (e.g., `.github/workflows/terraform.yml`) with the following content:

```yaml
name: Terraform Deployment

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  terraform-plan:
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@main
    with:
      action: 'plan'
      environment: 'dev'
      region: 'us-west-2'
      working-directory: './terraform'
    secrets: inherit

  terraform-apply:
    if: github.ref == 'refs/heads/main'
    needs: terraform-plan
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@main
    with:
      action: 'apply'
      environment: 'dev'
      region: 'us-west-2'
      working-directory: './terraform'
    secrets: inherit
```

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | No | `'plan'` | The Terraform action to perform: `'plan'`, `'apply'`, or `'destroy'` |
| `environment` | string | No | `'dev'` | Target environment/workspace (e.g., dev, stg, prod) |
| `region` | string | No | `'global'` | AWS region in AWS format (e.g., `'us-west-2'`) or `'global'` |
| `working-directory` | string | No | `'.'` | Directory containing Terraform files |
| `download-lambda-artifacts` | boolean | No | `false` | If true, downloads all Lambda artifacts from current run. If false, runs `setup.sh` (backward compatible) |

#### Required Secrets

The workflow expects the following secrets to be configured in your repository:

- `<ENV>_AWS_ID`: AWS Account ID for the target environment (e.g., `DEV_AWS_ID`)
- `<ENV>_ROLE_SECRET`: Suffix for the IAM role name (e.g., `DEV_ROLE_SECRET`)
- `CORE_TERRAFORM_ACCOUNT`: AWS Account ID for Terraform state storage
- `CORE_TERRAFORM_ROLE_SECRET`: Role suffix for accessing Terraform state

#### Required Variables

Optional repository variables that can be configured:

- `RUNNERS`: Custom GitHub Actions runner (defaults to `ubuntu-latest`)
- `TF_VERSION`: Terraform version to use (defaults to `1.14.3`)
- `PYTHON_VERSION`: Python version for scripts (defaults to `3.13`)
- `NODE_VERSION`: Node.js version (defaults to `20`)
- `TF_STATE_SSM_REGION`: Region for Terraform state backend (defaults to `eu-central-1`)
- `EKS_CLUSTER`: Optional EKS cluster name to include in resource tags

#### Permissions Required

The workflow needs the following permissions:

```yaml
permissions:
  id-token: write      # For AWS OIDC authentication
  pull-requests: write # For commenting on PRs
  contents: read       # For checking out code
```

### Deploy Website Workflow

Located in `.github/workflows/deploy-website.yml`, this is a reusable workflow for deploying static website files to AWS S3 and invalidating CloudFront cache.

#### Features

- Downloads Terraform output artifact containing infrastructure details
- Performs automatic replacements of `__output_name__` placeholders in files
- Syncs website files to S3 bucket with cache control headers
- Creates CloudFront invalidations only for changed paths
- Integration with AWS IAM roles via OIDC
- Multi-environment support (dev, staging, production)
- Efficient invalidation: only invalidates paths that were actually synced

#### Usage

This workflow is typically used after Terraform has provisioned the infrastructure:

```yaml
name: Website Deployment

on:
  push:
    branches:
      - main

jobs:
  terraform-apply:
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@main
    with:
      action: 'apply'
      environment: 'dev'
      region: 'us-west-2'
      working-directory: './terraform'
    secrets: inherit

  deploy-website:
    needs: terraform-apply
    uses: faccomichele/utils-n-scripts/.github/workflows/deploy-website.yml@main
    with:
      environment: 'dev'
      region: 'us-west-2'
      working-directory: 'website'
      terraform-artifact-name: 'terraform-output'
    secrets: inherit
```

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `environment` | string | No | `'dev'` | Target environment/workspace (e.g., dev, stg, prod) |
| `region` | string | No | `'global'` | AWS region in AWS format (e.g., `'us-west-2'`) or `'global'` |
| `working-directory` | string | No | `'website'` | Directory containing the files to be synced to S3 |
| `terraform-artifact-name` | string | No | `'terraform-output'` | Name of the Terraform output artifact (without run_id suffix) |

#### Required Terraform Outputs

The workflow expects the following outputs in the Terraform configuration:

- `website_bucket_name`: The S3 bucket name for the website
- `cloudfront_distribution_id`: The CloudFront distribution ID (optional, skips invalidation if not provided)
- Any other outputs that should replace `__output_name__` placeholders in files

Example Terraform outputs:

```hcl
output "website_bucket_name" {
  value       = aws_s3_bucket.website.id
  description = "The name of the S3 bucket for the website"
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.website.id
  description = "The ID of the CloudFront distribution"
}

output "api_endpoint" {
  value       = aws_api_gateway_deployment.api.invoke_url
  description = "API Gateway endpoint URL"
}
```

#### Placeholder Replacement

The workflow automatically replaces placeholders in your website files before syncing to S3:

- Pattern: `__output_name__`
- Example: `__api_endpoint__` → replaced with actual API endpoint URL
- Works on all text files in the working directory (non-binary files)

Example HTML file:

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Website</title>
</head>
<body>
  <script>
    const API_URL = '__api_endpoint__';
    const BUCKET = '__website_bucket_name__';
  </script>
</body>
</html>
```

#### S3 Sync Behavior

- Uses `aws s3 sync` with `--delete` flag (removes files not present locally)
- Sets `cache-control: max-age=3600` on all uploaded files
- Only uploads changed files (efficient)
- Captures list of uploaded/deleted files for targeted CloudFront invalidation

#### CloudFront Invalidation

- Creates invalidation only for paths that were actually synced
- If no specific paths detected, invalidates all paths (`/*`)
- Skips invalidation if `cloudfront_distribution_id` output is not provided
- Efficient: minimizes invalidation costs by targeting specific paths

#### Required Secrets

The workflow expects the following secrets to be configured in your repository:

- `<ENV>_AWS_ID`: AWS Account ID for the target environment (e.g., `DEV_AWS_ID`)
- `<ENV>_ROLE_SECRET`: Suffix for the IAM role name (e.g., `DEV_ROLE_SECRET`)

#### Permissions Required

The workflow needs the following permissions:

```yaml
permissions:
  id-token: write  # For AWS OIDC authentication
  contents: read   # For checking out code
```

#### IAM Role Requirements

The AWS IAM role must have the following permissions:

- `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` on the website bucket
- `cloudfront:CreateInvalidation` on the CloudFront distribution (if using CloudFront)

## Terraform Utilities

### Terraform Output to Markdown Converter

Located in `terraform/tf_out_to_md.py`, this Python script converts Terraform JSON output into human-readable Markdown reports.

#### Features

- Parses Terraform plan and apply output in JSON format
- Generates formatted Markdown reports with:
  - Summary statistics (resources to add/change/destroy)
  - Detailed change descriptions with emojis
  - Error highlighting
  - Resource grouping
- Outputs to `tf-report.md` in the current directory

#### Usage

The script is automatically used by the Terraform Run workflow, but can also be run standalone:

```bash
# Generate Terraform JSON output
terraform plan -out=tfplan -json > tf-logs.json
terraform show -json tfplan > tf-show.json

# Convert to Markdown
./terraform/tf_out_to_md.py

# View the generated report
cat tf-report.md
```

#### Input Files

The script looks for these files in the current directory:

- `tf-logs.json`: Terraform streaming JSON output (from `terraform plan/apply/destroy -json`)
- `tf-show.json`: Terraform show output (from `terraform show -json tfplan`)

#### Output

- `tf-report.md`: Formatted Markdown report with plan/apply summary and details

## Setup

### Prerequisites

- Python 3.13+ (for Terraform utilities)
- Terraform 1.14+ (when using workflows)
- AWS account with proper IAM roles configured
- GitHub repository with Actions enabled

### Installation

This repository is designed to be used as a reusable workflow reference. No installation is required in your local environment.

To use the workflows:

1. Reference the workflow in your repository's workflow files using the `uses` syntax
2. Configure required secrets and variables in your repository settings
3. Ensure your AWS IAM roles are properly configured for OIDC authentication

## Configuration

### AWS IAM Role Setup

The Terraform workflow expects IAM roles following this naming pattern:

```
arn:aws:iam::{ACCOUNT_ID}:role/github-role-for-{REPO_NAME}-GitHubActionsRole-{ROLE_SECRET}
```

Where:
- `{ACCOUNT_ID}`: Your AWS account ID
- `{REPO_NAME}`: First 17 characters of your repository name
- `{ROLE_SECRET}`: Custom suffix from secrets

### Terraform Backend Configuration

The workflow automatically configures an S3 backend for state storage:

- **Bucket**: `terraform-core-aws-state-files-{environment}-{account}`
- **Key**: `{repository-name}/terraform.tfstate`
- **Encryption**: Enabled
- **Locking**: Enabled

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Michele Facco (@faccomichele)

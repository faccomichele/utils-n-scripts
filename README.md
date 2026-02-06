# Utils and Scripts

A collection of reusable utilities and scripts for infrastructure automation and DevOps workflows.

## Contents

This repository contains:

- **GitHub Actions Workflows**: Reusable workflows for common CI/CD tasks
- **Terraform Utilities**: Scripts for processing and formatting Terraform output
- **Examples**: Sample configurations and usage examples (see [examples/](examples/README.md))

## GitHub Actions Workflows

**Recommendation:** Prefer referencing the `latest` workflow tag instead of the `main` branch when using the `uses` syntax (for example: `uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@latest`). Using a stable tag like `latest` reduces the chance of unexpected breakages from changes on the `main` branch.

### Lambda Build Workflow

Located in `.github/workflows/lambda-build.yml`, this is a reusable workflow for building Lambda function packages independently from Terraform operations.

#### Features

- Automatically detects Lambda functions in subfolders of the working directory
- Identifies build type based on file extensions (.py for Python, .js for Node.js) or dependency files (requirements.txt, package.json)
- **Supports layer-only builds**: Folders with only `requirements.txt` or `package.json` (without handler files) will build only a layer package
- Builds Lambda packages concurrently using matrix strategy
- **Separates code from dependencies for cleaner deployment:**
  - Main package (`<name>.zip`): Contains only the Lambda handler code (*.py or *.js files) - created only when handler files exist
  - Layer package (`<name>-layer.zip`): Contains only the dependencies (installed libraries)
  - Package definition files (requirements.txt, package.json, package-lock.json) are excluded from both packages
- Python: Installs dependencies from `requirements.txt` into a layer package
- Node.js: Installs dependencies from `package.json` into a layer package
- Uploads both main and layer packages as artifacts (layer only created if dependencies exist)
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
    uses: faccomichele/utils-n-scripts/.github/workflows/lambda-build.yml@latest
    with:
      working-directory: './terraform'

  terraform-plan:
    needs: lambda-build
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@latest
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
- **Python Lambdas**: 
  - Must contain at least one `.py` file OR a `requirements.txt` file
  - `.py` files are optional if you only need to build a layer (layer-only build)
  - `requirements.txt` is optional for dependencies
- **Node.js Lambdas**: 
  - Must contain at least one `.js` file OR a `package.json` file
  - `.js` files are optional if you only need to build a layer (layer-only build)
  - `package.json` is optional for dependencies
- Each Lambda subfolder will be packaged into one or two files:
  - `<subfolder-name>.zip`: Main Lambda code package (handler files only) - created only when `.py` or `.js` files exist
  - `<subfolder-name>-layer.zip`: Lambda layer package (dependencies only, created if `requirements.txt` or `package.json` exists)

#### How It Works

1. **Detection**: Scans all subfolders in the working directory for:
   - Python handler files (`.py`)
   - Node.js handler files (`.js`)
   - Python dependency files (`requirements.txt`)
   - Node.js dependency files (`package.json`)
2. **Classification**: Identifies build type and whether handler files are present
   - Folders with handler files: Build both function package and layer package (if dependencies exist)
   - Folders with only dependency files: Build layer package only (layer-only build)
3. **Matrix Build**: Builds all Lambdas concurrently (fail-fast: false)
4. **Packaging**: Creates packages as needed:
   - **Main package** (if handler files exist): Contains only the Lambda handler code files (*.py or *.js)
   - **Layer package** (if dependency files exist): Contains only dependencies installed from requirements.txt or package.json
   - Package definition files are excluded from both packages for a clean deployment
5. **Upload**: Packages uploaded as artifacts under `lambda-<name>-<run-id>`

**Package Structure:**

- **Python Lambda with handler:**
  - `<name>.zip`: Contains `*.py` files only
  - `<name>-layer.zip`: Contains packages installed via pip in `python/` directory structure (AWS Lambda layer format) - created only if `requirements.txt` exists
  
- **Python Layer-only (no handler files):**
  - `<name>-layer.zip`: Contains packages installed via pip in `python/` directory structure (AWS Lambda layer format)
  
- **Node.js Lambda with handler:**
  - `<name>.zip`: Contains `*.js` files only
  - `<name>-layer.zip`: Contains `node_modules/` in `nodejs/` directory structure (AWS Lambda layer format) - created only if `package.json` exists

- **Node.js Layer-only (no handler files):**
  - `<name>-layer.zip`: Contains `node_modules/` in `nodejs/` directory structure (AWS Lambda layer format)

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
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@latest
    with:
      action: 'plan'
      environment: 'dev'
      region: 'us-west-2'
      working-directory: './terraform'
    secrets: inherit

  terraform-apply:
    if: github.ref == 'refs/heads/main'
    needs: terraform-plan
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@latest
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
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@latest
    with:
      action: 'apply'
      environment: 'dev'
      region: 'us-west-2'
      working-directory: './terraform'
    secrets: inherit

  deploy-website:
    needs: terraform-apply
    uses: faccomichele/utils-n-scripts/.github/workflows/deploy-website.yml@latest
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

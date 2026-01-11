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

- Builds Lambda packages for Node.js and Python
- Executes `scripts/setup.sh` to create zip files
- Uploads all Lambda zip files as workflow artifacts
- Can be invoked independently or as part of a larger workflow
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
      lambda-artifact-name: ${{ needs.lambda-build.outputs.artifact-name }}
    secrets: inherit
```

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `working-directory` | string | No | `'.'` | Directory containing the `scripts/setup.sh` file |

#### Outputs

| Output | Description |
|--------|-------------|
| `artifact-name` | Name of the uploaded artifact containing Lambda zip files |

#### Requirements

- A `scripts/setup.sh` file in the working directory that creates Lambda zip files
- Lambda zip files should be created in a `lambda/` subdirectory
- The script should work with the specified Node.js and Python versions

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
| `lambda-artifact-name` | string | No | - | Optional: Name of artifact with pre-built Lambda packages. If provided, downloads artifacts instead of running `setup.sh` |

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

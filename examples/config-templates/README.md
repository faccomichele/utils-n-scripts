# Example Configuration Template Files

This directory contains example `.fmtcf` (format config) template files that demonstrate the placeholder replacement feature.

## Supported Placeholders

- `AWS-PARAMETER::name` - Retrieves values from AWS SSM Parameter Store (with decryption)
- `AWS-SECRET::name` - Retrieves values from AWS Secrets Manager
- `ENV::name` - Retrieves values from environment variables

## Example Files

### app-config.json.fmtcf
A JSON configuration file demonstrating all three placeholder types.

### docker-compose.yml.fmtcf
A Docker Compose file showing how to use placeholders for service configuration.

## Usage

### Manual Processing

Use the Python script directly:

```bash
python3 python/process_fmtcf.py examples/config-templates/app-config.json.fmtcf --region us-east-1
```

This will create `app-config.json` with all placeholders replaced.

### Workflow Processing

Use the reusable workflow to process all `.fmtcf` files:

```yaml
jobs:
  process-configs:
    uses: faccomichele/utils-n-scripts/.github/workflows/process-fmtcf-files.yml@latest
    with:
      working-directory: './config'
      region: 'us-east-1'
```

The workflow will:
1. Find all `.fmtcf` files in the specified directory
2. Process each file, replacing placeholders
3. Upload all processed files as an artifact named `processed-configs-{run_id}`

### Integration with Terraform

The processed configs can be automatically used in Terraform workflows:

```yaml
jobs:
  process-configs:
    uses: faccomichele/utils-n-scripts/.github/workflows/process-fmtcf-files.yml@latest
    with:
      working-directory: './terraform'
      region: 'us-east-1'

  terraform-apply:
    needs: process-configs
    uses: faccomichele/utils-n-scripts/.github/workflows/terraform-run.yml@latest
    with:
      action: 'apply'
      environment: 'dev'
      region: 'us-east-1'
      working-directory: './terraform'
    secrets: inherit
```

The Terraform workflow automatically downloads the `processed-configs-{run_id}` artifact before running `terraform init`.

## Requirements

### For AWS Placeholders
- AWS credentials must be configured (via environment variables or IAM role)
- Appropriate IAM permissions to read from SSM Parameter Store and Secrets Manager

### For Environment Variable Placeholders
- Environment variables must be set before running the script

## Notes

- Processed files maintain the same directory structure as the templates
- The `.fmtcf` extension is automatically removed from the output filename
- Files without the `.fmtcf` extension are skipped with a warning

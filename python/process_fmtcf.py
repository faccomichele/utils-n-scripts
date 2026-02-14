#!/usr/bin/env python3
"""
Configuration File Template Processor

Processes .fmtcf template files by replacing placeholders with actual values:
- AWS-PARAMETER::name => AWS SSM Parameter Store value (with decryption)
- AWS-SECRET::name => AWS Secrets Manager secret value
- ENV::name => Environment variable value

The processed file is saved without the .fmtcf extension.
For example: config.json.fmtcf -> config.json
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("Warning: boto3 not installed. AWS placeholder replacement will not work.", file=sys.stderr)
    boto3 = None


def get_aws_parameter(name: str, region: str = None) -> str:
    """Retrieve value from AWS SSM Parameter Store with decryption."""
    if boto3 is None:
        raise RuntimeError("boto3 is required for AWS operations")
    
    session_kwargs = {}
    if region:
        session_kwargs['region_name'] = region
    
    ssm = boto3.client('ssm', **session_kwargs)
    
    try:
        response = ssm.get_parameter(Name=name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ParameterNotFound':
            raise ValueError(f"AWS Parameter '{name}' not found")
        else:
            raise RuntimeError(f"Failed to retrieve AWS Parameter '{name}': {e}")


def get_aws_secret(name: str, region: str = None) -> str:
    """Retrieve value from AWS Secrets Manager."""
    if boto3 is None:
        raise RuntimeError("boto3 is required for AWS operations")
    
    session_kwargs = {}
    if region:
        session_kwargs['region_name'] = region
    
    secretsmanager = boto3.client('secretsmanager', **session_kwargs)
    
    try:
        response = secretsmanager.get_secret_value(SecretId=name)
        return response['SecretString']
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            raise ValueError(f"AWS Secret '{name}' not found")
        else:
            raise RuntimeError(f"Failed to retrieve AWS Secret '{name}': {e}")


def get_env_var(name: str) -> str:
    """Retrieve value from environment variable."""
    value = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable '{name}' not found")
    return value


def process_placeholders(content: str, region: str = None) -> str:
    """Replace all placeholders in the content with their actual values."""
    
    # Pattern to match AWS-PARAMETER::name, AWS-SECRET::name, ENV::name
    pattern = r'(AWS-PARAMETER|AWS-SECRET|ENV)::([a-zA-Z0-9_\-/]+)'
    
    def replace_placeholder(match):
        placeholder_type = match.group(1)
        name = match.group(2)
        
        try:
            if placeholder_type == 'AWS-PARAMETER':
                return get_aws_parameter(name, region)
            elif placeholder_type == 'AWS-SECRET':
                return get_aws_secret(name, region)
            elif placeholder_type == 'ENV':
                return get_env_var(name)
        except Exception as e:
            print(f"Error replacing {placeholder_type}::{name}: {e}", file=sys.stderr)
            raise
        
        return match.group(0)  # Return original if no match
    
    return re.sub(pattern, replace_placeholder, content)


def main():
    parser = argparse.ArgumentParser(
        description='Process .fmtcf template files by replacing placeholders with actual values'
    )
    parser.add_argument(
        'file',
        type=str,
        help='Path to the .fmtcf file to process'
    )
    parser.add_argument(
        '--region',
        type=str,
        default=None,
        help='AWS region for parameter/secret retrieval (default: use currently configured session)'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.file)
    
    if not input_path.exists():
        print(f"Error: File '{args.file}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.suffix == '.fmtcf':
        print(f"Warning: File '{args.file}' does not end with .fmtcf extension. Skipping.", file=sys.stderr)
        sys.exit(0)
    
    # Read input file
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{args.file}': {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process placeholders
    try:
        processed_content = process_placeholders(content, args.region)
    except Exception as e:
        print(f"Error processing placeholders: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output file path (remove .fmtcf extension)
    output_path = input_path.with_suffix('')
    
    # Write output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        print(f"Successfully processed '{args.file}' -> '{output_path}'")
    except Exception as e:
        print(f"Error writing output file '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

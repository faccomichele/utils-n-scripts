# This script gets temporary credentials for an IAM user that requires MFA
# and updates a local AWS profile with them.

param(
    [string]$SourceProfile,
    [string]$MfaCode,         # This is the MFA code input by the user
    [string]$MfaProfile = "mfa"
)

Write-Host "Attempting to get session token from AWS using profile '$SourceProfile'..."

try {
    # Get the default region from the source profile
    $region = aws configure get region --profile $SourceProfile
    if ([string]::IsNullOrWhiteSpace($region)) {
        $region = "ap-southeast-1" # fallback default if not set: Singapore
    }

    $accountId = aws sts get-caller-identity --profile $SourceProfile --output json | ConvertFrom-Json | Select-Object -ExpandProperty Account

    # The user will be prompted for their MFA token here by the AWS CLI
    $tokenInfo = aws sts get-session-token --profile $SourceProfile --serial-number "arn:aws:iam::${accountId}:mfa/mfa-authenticator-app" --token-code  $MfaCode --output json | ConvertFrom-Json

    if ($null -eq $tokenInfo) {
        throw "Failed to parse session token JSON. The AWS CLI command might have failed."
    }

    $accessKeyId = $tokenInfo.Credentials.AccessKeyId
    $secretAccessKey = $tokenInfo.Credentials.SecretAccessKey
    $sessionToken = $tokenInfo.Credentials.SessionToken

    aws configure set aws_access_key_id "$accessKeyId" --profile $MfaProfile
    aws configure set aws_secret_access_key "$secretAccessKey" --profile $MfaProfile
    aws configure set aws_session_token "$sessionToken" --profile $MfaProfile
    aws configure set region "$region" --profile $MfaProfile
    aws configure set output "json" --profile $MfaProfile

    Write-Host -ForegroundColor Green "Successfully updated profile '$MfaProfile' with temporary credentials."
    Write-Host "These credentials will expire at $($tokenInfo.Credentials.Expiration)"

}
catch {
    Write-Host -ForegroundColor Red "An error occurred:"
    Write-Host -ForegroundColor Red $_.Exception.Message
    exit 1
}

# Adds the current folder to the user's PATH environment variable permanently
# filepath: add-current-folder-to-path.ps1

$CurrentFolder = (Get-Location).Path
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")

if ($UserPath -notlike "*$CurrentFolder*") {
    $NewPath = "$UserPath;$CurrentFolder"
    [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
    Write-Host "Added $CurrentFolder to your user PATH."
} else {
    Write-Host "$CurrentFolder is already in your user PATH."
}

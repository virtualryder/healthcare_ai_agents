# Delete the retained WORM bucket from the acceptance test, AFTER its Object Lock
# COMPLIANCE retention expires (2026-06-30T21:11:54Z). Run on a machine with AWS creds.
# COMPLIANCE objects cannot be deleted before that time by anyone, including root.
param(
  [string]$Bucket = "hpp-gp01-acc-wormbucket-a8zdvmdnfhs6",
  [string]$Region = "us-east-1"
)
$ErrorActionPreference = "Stop"; $env:AWS_PAGER = ""

$now = [DateTime]::UtcNow
$unlock = [DateTime]::Parse("2026-06-30T21:11:54Z").ToUniversalTime()
if ($now -lt $unlock) {
  Write-Host "Object Lock not yet expired. Deletable after $($unlock.ToString('o')) (now $($now.ToString('o'))). Try again then."
  exit 1
}

Write-Host "Deleting all object versions in $Bucket ..."
$versions = aws s3api list-object-versions --bucket $Bucket --region $Region `
  --query "Versions[].{Key:Key,VersionId:VersionId}" --output json | ConvertFrom-Json
foreach ($o in $versions) {
  aws s3api delete-object --bucket $Bucket --key $o.Key --version-id $o.VersionId --region $Region | Out-Null
}
$markers = aws s3api list-object-versions --bucket $Bucket --region $Region `
  --query "DeleteMarkers[].{Key:Key,VersionId:VersionId}" --output json | ConvertFrom-Json
foreach ($o in $markers) {
  aws s3api delete-object --bucket $Bucket --key $o.Key --version-id $o.VersionId --region $Region | Out-Null
}
Write-Host "Removing bucket ..."
aws s3api delete-bucket --bucket $Bucket --region $Region
Write-Host "Done. Verifying it's gone:"
aws s3api head-bucket --bucket $Bucket --region $Region 2>&1

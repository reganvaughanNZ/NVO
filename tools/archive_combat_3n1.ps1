$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$gameRoot = [IO.Path]::GetFullPath('C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
$packRoot = Join-Path $projectRoot 'source\combat\step3n1'
if (Get-Process FalloutNV,geck -ErrorAction SilentlyContinue) { throw 'Close New Vegas and GECK before archiving the manual helper.' }
$review = Get-Content -LiteralPath (Join-Path $packRoot 'RUNTIME-RESULT.json') -Raw | ConvertFrom-Json
if ($review.status -ne 'targeted_new_game_reload_retirement_passed') { throw 'Runtime review has not passed.' }
$installed = Get-Content -LiteralPath (Join-Path $packRoot 'INSTALL-RESULT.json') -Raw | ConvertFrom-Json
$archiveRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot ('backups\baron-check-3N1-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))))
if (-not $archiveRoot.StartsWith($projectRoot + '\backups\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Archive outside project backups.' }
$allowed = @('NVOBaronCheck.txt','Data\NVSE\user_defined_functions\NVOBaronCheck\Check.txt')
$operations = @()
foreach ($relative in $allowed) {
    $source = [IO.Path]::GetFullPath((Join-Path $gameRoot $relative))
    $destination = [IO.Path]::GetFullPath((Join-Path $archiveRoot $relative))
    if (-not $source.StartsWith($gameRoot + '\',[StringComparison]::OrdinalIgnoreCase) -or -not $destination.StartsWith($archiveRoot + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Archive path check failed.' }
    $record = @($installed.installed | Where-Object { $_.destination -eq $source })
    if ($record.Count -ne 1 -or (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record[0].sha256) { throw 'Helper differs from installed packet; preserve for review.' }
    if (Test-Path -LiteralPath $destination) { throw 'Archive target already exists.' }
    $operations += [PSCustomObject]@{source=$source; destination=$destination; sha256=$record[0].sha256}
}
foreach ($operation in $operations) {
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($operation.destination)) | Out-Null
    Move-Item -LiteralPath $operation.source -Destination $operation.destination
    if ((Get-FileHash -LiteralPath $operation.destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $operation.sha256) { throw 'Archive hash mismatch.' }
}
foreach ($property in $installed.protected_unchanged.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath $property.Name -Algorithm SHA256).Hash.ToLowerInvariant() -ne $property.Value) { throw 'Protected asset differs from test installation.' }
}
[ordered]@{packet='3N1'; archived_utc=[DateTime]::UtcNow.ToString('o'); files=$operations; logs_preserved=$true; protected_assets_unchanged=$true} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $packRoot 'ARCHIVE-RESULT.json') -Encoding UTF8
Write-Output 'Archived the two completed manual helper files; logs and six protected game assets preserved.'

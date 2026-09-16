$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$gameRoot = [IO.Path]::GetFullPath('C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
$packRoot = Join-Path $projectRoot 'source\combat\step3n1'
$manifest = Get-Content -LiteralPath (Join-Path $packRoot 'manifest.json') -Raw | ConvertFrom-Json
if (Get-Process FalloutNV,geck -ErrorAction SilentlyContinue) { throw 'Close New Vegas and GECK before installing this packet.' }
$protected = @{}
$prior = Get-Content -LiteralPath (Join-Path $projectRoot 'source\combat\step3n\PACKET-RESULT.json') -Raw | ConvertFrom-Json
foreach ($asset in $prior.baseline_assets) {
    $protected[$asset.path] = (Get-FileHash -LiteralPath $asset.path -Algorithm SHA256).Hash.ToLowerInvariant()
}
$esm = Join-Path $gameRoot 'Data\NVO.esm'
if ($protected[$esm] -ne $manifest.expected_esm_sha256) { throw 'NVO.esm changed since the verified save. Review before installation.' }
$allowed = @('NVOBaronCheck.txt', 'Data/NVSE/user_defined_functions/NVOBaronCheck/Check.txt')
$operations = @()
foreach ($file in $manifest.payload) {
    if ($file.relative_path -cnotin $allowed) { throw 'Unexpected payload path.' }
    $source = Join-Path $packRoot $file.relative_path
    $destination = [IO.Path]::GetFullPath((Join-Path $gameRoot $file.relative_path))
    if (-not $destination.StartsWith($gameRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Destination outside game folder.' }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256) { throw 'Payload hash mismatch.' }
    if (Test-Path -LiteralPath $destination) { throw 'A test file already exists. Review or archive it before replacing.' }
    $operations += [PSCustomObject]@{source=$source; destination=$destination; sha256=$file.sha256}
}
if ($operations.Count -ne 2) { throw 'Expected exactly two test files.' }
$logBefore = @()
foreach ($relative in @('NVOCombatCore.log','nvse.log','Data/NVSE/Plugins/NVOBaronCheck.log')) {
    $path = Join-Path $gameRoot $relative
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path
        $logBefore += [PSCustomObject]@{path=$path; size=$item.Length; modified_utc=$item.LastWriteTimeUtc.ToString('o'); sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
    }
}
foreach ($operation in $operations) {
    $parent = [IO.Path]::GetDirectoryName($operation.destination)
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    Copy-Item -LiteralPath $operation.source -Destination $operation.destination
    if ((Get-FileHash -LiteralPath $operation.destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $operation.sha256) { throw 'Installed file verification failed.' }
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $protected[$path]) { throw 'Protected game asset changed during installation.' }
}
$result = [ordered]@{packet='3N1'; installed_utc=[DateTime]::UtcNow.ToString('o'); installed=$operations; protected_unchanged=$protected; prior_logs=$logBefore; gameplay_tested=$false; damage_replacement=$false}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $packRoot 'INSTALL-RESULT.json') -Encoding UTF8
Write-Output 'Installed and hash-verified two manual test files. Six protected game assets unchanged. Gameplay test pending.'

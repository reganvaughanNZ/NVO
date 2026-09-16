$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$nvoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$nvoStep = Join-Path $nvoRoot 'source\combat\step4b\stress'
$nvoPlan = Get-Content -LiteralPath (Join-Path $nvoStep 'INSTALL-plan.json') -Raw | ConvertFrom-Json
$nvoGame = [IO.Path]::GetFullPath([string]$nvoPlan.game_root)
$nvoRelease = Join-Path $nvoRoot 'release\NVO-Combat-Packet-4B-Stress-Check'
if ($nvoGame -ne 'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas') { throw 'Unexpected game root.' }
if ($nvoPlan.packet -ne '4B-stress' -or $nvoPlan.native_version -ne 326) { throw 'Unexpected packet.' }
if (Test-Path -LiteralPath (Join-Path $nvoStep 'INSTALL-result.json')) { throw 'Installation already recorded.' }
function Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Child([string]$Root, [string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative)) { throw 'Relative path required.' }
    $resolved = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $resolved.StartsWith($Root.TrimEnd('\')+'\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped root.' }
    $cursor = $resolved
    while ($cursor) {
        if ((Test-Path -LiteralPath $cursor) -and ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Reparse path refused.' }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    $resolved
}
$nvoAllowed = @('NVOStressKit4B.txt','NVOStressTarget4B.txt')
if (@($nvoPlan.files).Count -ne 2 -or @($nvoPlan.files.path | Select-Object -Unique).Count -ne 2) { throw 'Exactly two new helper files required.' }
foreach ($row in $nvoPlan.files) {
    if ($row.path -notin $nvoAllowed) { throw 'Unexpected file.' }
    $src = Child $nvoRelease $row.path
    $dest = Child $nvoGame $row.path
    if ($src -ne $row.source -or (Hash $src) -ne $row.sha256) { throw 'Source differs.' }
    if (Test-Path -LiteralPath $dest) { throw 'Refuse to replace an existing file.' }
}
foreach ($prop in $nvoPlan.protected.PSObject.Properties) {
    if ((Hash (Child $nvoGame $prop.Name)) -ne $prop.Value) { throw 'Protected baseline differs.' }
}
if (Test-Path -LiteralPath (Join-Path $nvoGame 'Data\RD.esm')) { throw 'RD.esm unexpectedly present.' }
$nvoCreated = @()
try {
    foreach ($row in $nvoPlan.files) {
        $dest = Child $nvoGame $row.path
        # File.Copy with overwrite=false atomically refuses a newly-created destination.
        [IO.File]::Copy([string]$row.source, $dest, $false)
        $nvoCreated += $row.path
        if ((Hash $dest) -ne $row.sha256) { throw 'Installed helper hash differs.' }
    }
    foreach ($prop in $nvoPlan.protected.PSObject.Properties) {
        if ((Hash (Child $nvoGame $prop.Name)) -ne $prop.Value) { throw 'Protected file changed.' }
    }
} catch {
    foreach ($relative in $nvoCreated) {
        $dest = Child $nvoGame $relative
        $row = @($nvoPlan.files | Where-Object path -eq $relative)[0]
        if ((Test-Path -LiteralPath $dest) -and (Hash $dest) -eq $row.sha256) { Remove-Item -LiteralPath $dest }
    }
    throw
}
$nvoResult = @{status='installed'; packet='4B-stress'; installed=$nvoPlan.files; protected_files_verified=@($nvoPlan.protected.PSObject.Properties).Count; native_unchanged=$true; process_actions=0; gameplay_tested=$false}
$nvoResult | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $nvoStep 'INSTALL-result.json') -Encoding UTF8
$nvoResult | ConvertTo-Json -Depth 6

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$nvoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$nvoStep = Join-Path $nvoRoot 'source\combat\step4i1'
$nvoPlanPath = Join-Path $nvoStep 'Evidence\INSTALL-plan.json'
$nvoPlan = Get-Content -LiteralPath $nvoPlanPath -Raw | ConvertFrom-Json
$nvoGame = [IO.Path]::GetFullPath([string]$nvoPlan.game_root)
$nvoRelease = Join-Path $nvoRoot 'release\NVO-Combat-Packet-4I1-Callback-Survival'
if ($nvoGame -ne 'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas') { throw 'Unexpected game root.' }
if ($nvoPlan.packet -ne '4I1' -or $nvoPlan.native_version -ne 329) { throw 'Unexpected packet.' }
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
$nvoExpected = @{
    'Data/NVSE/Plugins/NVOCombatCore.dll'='45c1713b57c13c48ef6f35ab40c51398e6e332ef1403a59fa2ed89139debea2f'
    'Data/NVSE/Plugins/NVOCombatCore.pdb'='1664369aeaa0a54dbbffdcacff595b9144d0f430f9e9d6bff81e4e7c5c3e28c4'
}
if (@($nvoPlan.files).Count -ne 2 -or @($nvoPlan.files.path | Select-Object -Unique).Count -ne 2) { throw 'Exactly two unique files required.' }
foreach ($row in $nvoPlan.files) {
    if (-not $nvoExpected.ContainsKey([string]$row.path) -or $row.sha256 -ne $nvoExpected[$row.path]) { throw 'Unexpected source file/hash.' }
    $src = Child $nvoRelease $row.path
    $dest = Child $nvoGame $row.path
    if ($src -ne $row.source -or (Hash $src) -ne $row.sha256) { throw 'Prepared source differs.' }
    if ($row.previous_sha256) {
        if ((Hash $dest) -ne $row.previous_sha256) { throw 'Installed baseline differs.' }
    } elseif (Test-Path -LiteralPath $dest) { throw 'New configuration already exists; preserve and review it.' }
}
foreach ($prop in $nvoPlan.protected.PSObject.Properties) {
    if ((Hash (Child $nvoGame $prop.Name)) -ne $prop.Value) { throw "Protected baseline differs: $($prop.Name)" }
}
if (Test-Path -LiteralPath (Join-Path $nvoGame 'Data\RD.esm')) { throw 'RD.esm unexpectedly present.' }
if (@(Get-Process GECK -ErrorAction SilentlyContinue).Count) { throw 'GECK is open; no files changed.' }
# A background Vortex instance is not a file owner. Never overwrite deployed
# hardlinks, and verify the protected inventory before and after the transaction.
# Any actual concurrent deployment that changes those bytes aborts this install.
$nvoBackgroundVortex = @(Get-Process Vortex -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$nvoClosed = @()
foreach ($proc in @(Get-Process FalloutNV -ErrorAction SilentlyContinue)) {
    if ($proc.Path -ne (Join-Path $nvoGame 'FalloutNV.exe')) { throw 'Unrecognized FalloutNV process.' }
    $sent = $proc.CloseMainWindow()
    $exited = $proc.WaitForExit(8000)
    if (-not $exited) {
        $current = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
        if ($current -and $current.Path -eq (Join-Path $nvoGame 'FalloutNV.exe')) {
            Stop-Process -Id $current.Id -Force
            if (-not $current.WaitForExit(5000)) { throw 'Game did not exit.' }
        }
    }
    $nvoClosed += @{pid=$proc.Id; close_message_sent=$sent; forced=(-not $exited)}
}
if (@(Get-Process FalloutNV -ErrorAction SilentlyContinue).Count) { throw 'Game is still running.' }
$nvoBackup = Child $nvoRoot ('backups\combat-install-4I1-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
$null = New-Item -ItemType Directory -Path $nvoBackup
Copy-Item -LiteralPath $nvoPlanPath -Destination (Join-Path $nvoBackup 'plan.json')
$nvoBefore = @()
foreach ($row in $nvoPlan.files) {
    $dest = Child $nvoGame $row.path
    $exists = Test-Path -LiteralPath $dest -PathType Leaf
    $hash = if ($exists) { Hash $dest } else { $null }
    if ($hash -ne $row.previous_sha256) { throw 'Destination changed before backup.' }
    if ($exists) {
        $save = Child $nvoBackup ('originals\'+$row.path)
        $null = New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($save)) -Force
        Copy-Item -LiteralPath $dest -Destination $save
        if ((Hash $save) -ne $hash) { throw 'Backup verification failed.' }
    }
    $nvoBefore += @{path=$row.path; existed=$exists; sha256=$hash}
}
$nvoProtected = @{}
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $nvoGame 'Data\NVSE') -File -Recurse -Force) {
    if ($file.FullName -notin @($nvoPlan.files | ForEach-Object { Child $nvoGame $_.path })) { $nvoProtected[$file.FullName] = Hash $file.FullName }
}
foreach ($prop in $nvoPlan.protected.PSObject.Properties) { $nvoProtected[(Child $nvoGame $prop.Name)] = $prop.Value }
foreach ($path in @('C:\Users\regan\AppData\Local\FalloutNV\plugins.txt','C:\Users\regan\AppData\Local\FalloutNV\loadorder.txt')) {
    if (Test-Path -LiteralPath $path -PathType Leaf) { $nvoProtected[$path] = Hash $path }
}
$nvoLog = Child $nvoGame 'NVOCombatCore.log'
if (Test-Path -LiteralPath $nvoLog -PathType Leaf) { Copy-Item -LiteralPath $nvoLog -Destination (Join-Path $nvoBackup 'NVOCombatCore-before.log') }
@{before=$nvoBefore; protected=$nvoProtected; closed_processes=$nvoClosed; background_vortex_left_running=$nvoBackgroundVortex} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $nvoBackup 'before.json') -Encoding UTF8
$nvoTouched = @()
try {
    if (@(Get-Process FalloutNV,GECK -ErrorAction SilentlyContinue).Count) { throw 'Game or GECK reopened before installation.' }
    foreach ($row in $nvoPlan.files) {
        $dest = Child $nvoGame $row.path
        if ($row.previous_sha256) {
            if ((Hash $dest) -ne $row.previous_sha256) { throw 'Destination changed after backup.' }
            # Unlink only this deployed file before copying, preserving any hardlinked mod-manager source.
            Remove-Item -LiteralPath $dest -Force
            $nvoTouched += $row.path
        }
        [IO.File]::Copy([string]$row.source,$dest,$false)
        if ($row.path -notin $nvoTouched) { $nvoTouched += $row.path }
        if ((Hash $dest) -ne $row.sha256) { throw 'Installed hash differs.' }
    }
    foreach ($entry in $nvoProtected.GetEnumerator()) {
        if ((Hash $entry.Key) -ne $entry.Value) { throw "Protected file changed: $($entry.Key)" }
    }
} catch {
    $failure = $_.Exception.Message
    $rollbackErrors = @()
    foreach ($relative in $nvoTouched) {
        try {
            $dest = Child $nvoGame $relative
            if (Test-Path -LiteralPath $dest -PathType Leaf) { Remove-Item -LiteralPath $dest -Force }
            $before = @($nvoBefore | Where-Object { $_.path -eq $relative })[0]
            if ($before.existed) {
                [IO.File]::Copy((Child $nvoBackup ('originals\'+$relative)),$dest,$false)
                if ((Hash $dest) -ne $before.sha256) { throw 'Rollback hash differs.' }
            }
        } catch { $rollbackErrors += "$relative : $($_.Exception.Message)" }
    }
    @{status='failed'; error=$failure; rollback_errors=$rollbackErrors; backup=$nvoBackup} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $nvoBackup 'result.json') -Encoding UTF8
    throw "Installation failed: $failure. Rollback errors: $($rollbackErrors.Count). Backup: $nvoBackup"
}
$nvoResult = @{status='installed'; packet='4I1'; native_version=329; installed_utc=[DateTime]::UtcNow.ToString('o'); backup=$nvoBackup; closed_processes=$nvoClosed; installed=@($nvoPlan.files | ForEach-Object { @{path=$_.path; sha256=(Hash (Child $nvoGame $_.path))} }); protected_files_verified=$nvoProtected.Count; rd_absent=$true; game_launched=$false; gameplay_tested=$false; damage_replacement=$false; stagger_writes=$false}
$nvoResult | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $nvoBackup 'result.json') -Encoding UTF8
$nvoResult | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $nvoStep 'INSTALL-result.json') -Encoding UTF8
$nvoResult | ConvertTo-Json -Depth 6


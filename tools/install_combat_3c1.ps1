$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$nvoWorkspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$nvoPlanPath = Join-Path $nvoWorkspace 'source\combat\step3c1\INSTALL-3C1-plan.json'
$nvoPlan = Get-Content -LiteralPath $nvoPlanPath -Raw | ConvertFrom-Json
$nvoGame = [IO.Path]::GetFullPath([string]$nvoPlan.game_root)
$nvoExpectedGame = 'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas'
if ($nvoGame -ne $nvoExpectedGame -or $nvoWorkspace -ne [string]$nvoPlan.workspace) { throw 'Unexpected target root.' }

function Assert-ChildPath([string]$Root, [string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative)) { throw 'Relative path required.' }
    $resolved = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $resolved.StartsWith($Root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes target: $Relative"
    }
    # Refuse directory junctions/symlinks, including any above the target root.
    $cursor = $resolved
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse path refused: $cursor" }
        }
        $parent = [IO.Path]::GetDirectoryName($cursor)
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
    return $resolved
}
function File-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Running-Game {
    @(Get-Process -Name FalloutNV -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -and ([IO.Path]::GetFullPath($_.Path) -eq (Join-Path $nvoGame 'FalloutNV.exe'))
    })
}

# Validate the exact allowlist and release bytes before touching the running game.
$nvoRelease = Join-Path $nvoWorkspace 'release\NVO-Combat-Packet-3C1-Compiled'
$nvoAllowedInstall = @('Data/NVSE/Plugins/NVOCombatCore.dll', 'Data/NVSE/Plugins/NVOCombatCore.pdb')
if (@($nvoPlan.files).Count -ne 2 -or @($nvoPlan.files.path | Select-Object -Unique).Count -ne 2) { throw 'Exactly two unique NVO install files required.' }
foreach ($row in $nvoPlan.files) {
    $null = Assert-ChildPath $nvoGame $row.path
    if ($row.action -eq 'install') {
        if ($row.path -notin $nvoAllowedInstall) { throw 'Unexpected installed file.' }
        $sourcePath = Assert-ChildPath $nvoRelease $row.path
        if ($sourcePath -ne [string]$row.source -or (File-Hash $sourcePath) -ne $row.source_sha256) {
            throw "Source mismatch: $($row.path)"
        }
    } else { throw 'Only the two named NVO install actions are allowed.' }
    if ($row.path -match '\.(esm|esp|bsa|fos)$') { throw 'Game plugins/assets/saves must not be changed.' }
}

foreach ($dependency in $nvoPlan.dependency_preconditions) {
    if ($dependency.path -notin @('Data/NVSE/Plugins/itr-nvse.dll', 'Data/NVSE/Plugins/jip_nvse.dll', 'Data/NVSE/Plugins/ShowOffNVSE.dll')) { throw 'Unexpected dependency precondition.' }
    $dependencyPath = Assert-ChildPath $nvoGame $dependency.path
    if ((File-Hash $dependencyPath) -ne $dependency.sha256) { throw 'An inspected dependency binary changed since ABI review. Installation stopped without modifying game files.' }
}

$nvoClosed = @()
foreach ($process in @(Running-Game)) {
    $pidToClose = $process.Id
    $requested = $process.CloseMainWindow()
    $exited = $process.WaitForExit(8000)
    if (-not $exited) {
        # Recheck identity before using the user's explicit permission to close it.
        $stillRunning = Get-Process -Id $pidToClose -ErrorAction SilentlyContinue
        if ($stillRunning -and $stillRunning.Path -eq (Join-Path $nvoGame 'FalloutNV.exe')) {
            Stop-Process -Id $pidToClose -Force
            if (-not $stillRunning.WaitForExit(5000)) { throw 'Game did not exit.' }
        }
    }
    $nvoClosed += [PSCustomObject]@{ pid=$pidToClose; close_message_sent=$requested; forced=(-not $exited) }
}
if (@(Running-Game).Count) { throw 'Fallout New Vegas is still running.' }

$nvoBackupName = 'backups\combat-install-3C1-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$nvoBackup = Assert-ChildPath $nvoWorkspace $nvoBackupName
$null = New-Item -ItemType Directory -Path $nvoBackup
Copy-Item -LiteralPath $nvoPlanPath -Destination (Join-Path $nvoBackup 'plan.json')

$nvoAffected = @($nvoPlan.files | ForEach-Object { (Assert-ChildPath $nvoGame $_.path).ToLowerInvariant() })
$nvoProtected = @()
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $nvoGame 'Data\NVSE') -Recurse -File -Force) {
    if ($file.FullName.ToLowerInvariant() -notin $nvoAffected) {
        $nvoProtected += [PSCustomObject]@{ path=$file.FullName; sha256=(File-Hash $file.FullName) }
    }
}
foreach ($relative in $nvoPlan.protected_assets) {
    $path = Assert-ChildPath $nvoGame $relative
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $nvoProtected += [PSCustomObject]@{ path=$path; sha256=(File-Hash $path) }
    }
}
$nvoBefore = @()
foreach ($nvoActivationPath in @('C:\Users\regan\AppData\Local\FalloutNV\plugins.txt', 'C:\Users\regan\AppData\Local\FalloutNV\loadorder.txt')) {
    if (Test-Path -LiteralPath $nvoActivationPath -PathType Leaf) {
        $nvoProtected += [PSCustomObject]@{ path=$nvoActivationPath; sha256=(File-Hash $nvoActivationPath) }
    }
}
foreach ($row in $nvoPlan.files) {
    $path = Assert-ChildPath $nvoGame $row.path
    $exists = Test-Path -LiteralPath $path -PathType Leaf
    $hash = if ($exists) { File-Hash $path } else { $null }
    if (-not $row.log_may_change_until_game_exits -and $hash -ne $row.sha256) { throw "Destination changed since inventory: $($row.path)" }
    if ($exists) {
        $backupPath = Assert-ChildPath $nvoBackup ('originals\' + $row.path)
        $null = New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($backupPath)) -Force
        Copy-Item -LiteralPath $path -Destination $backupPath
        if ((File-Hash $backupPath) -ne $hash) { throw "Backup mismatch: $($row.path)" }
    }
    $nvoBefore += [PSCustomObject]@{ path=$row.path; existed=$exists; sha256=$hash; action=$row.action }
}
foreach ($relative in $nvoPlan.preserve_log_copy) {
    $path = Assert-ChildPath $nvoGame $relative
    if (Test-Path -LiteralPath $path -PathType Leaf) { Copy-Item -LiteralPath $path -Destination (Join-Path $nvoBackup $relative) }
}
@{ before=$nvoBefore; protected=$nvoProtected; closed_processes=$nvoClosed } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $nvoBackup 'before.json') -Encoding UTF8

$nvoTouched = @()
try {
    if (@(Running-Game).Count) { throw 'Game relaunched before installation.' }
    foreach ($row in $nvoPlan.files) {
        $path = Assert-ChildPath $nvoGame $row.path
        $before = @($nvoBefore | Where-Object path -eq $row.path)[0]
        if ($before.existed) {
            if ((File-Hash $path) -ne $before.sha256) { throw "File changed after backup: $($row.path)" }
            # Remove the deployed file, never overwrite a possible Vortex hardlink.
            Remove-Item -LiteralPath $path -Force
        }
        $nvoTouched += $row.path
        if ($row.action -eq 'install') {
            $null = New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($path)) -Force
            Copy-Item -LiteralPath $row.source -Destination $path
            if ((File-Hash $path) -ne $row.source_sha256) { throw "Installed hash mismatch: $($row.path)" }
        } elseif (Test-Path -LiteralPath $path) { throw "Old file still present: $($row.path)" }
    }
    foreach ($row in $nvoProtected) {
        if ((File-Hash $row.path) -ne $row.sha256) { throw "Protected file changed: $($row.path)" }
    }
    foreach ($relative in $nvoPlan.empty_directories) {
        $path = Assert-ChildPath $nvoGame $relative
        if ((Test-Path -LiteralPath $path -PathType Container) -and @(Get-ChildItem -LiteralPath $path -Force).Count -eq 0) {
            Remove-Item -LiteralPath $path -Force # empty only; no recursive removal
        }
    }
} catch {
    $failure = $_.Exception.Message
    $rollbackErrors = @()
    foreach ($relative in $nvoTouched) {
        try {
            $path = Assert-ChildPath $nvoGame $relative
            if (Test-Path -LiteralPath $path -PathType Leaf) { Remove-Item -LiteralPath $path -Force }
            $before = @($nvoBefore | Where-Object path -eq $relative)[0]
            if ($before.existed) {
                $null = New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($path)) -Force
                Copy-Item -LiteralPath (Assert-ChildPath $nvoBackup ('originals\' + $relative)) -Destination $path
                if ((File-Hash $path) -ne $before.sha256) { throw 'Restoration hash mismatch.' }
            }
        } catch { $rollbackErrors += "$relative : $($_.Exception.Message)" }
    }
    @{ status='failed'; error=$failure; rollback_errors=$rollbackErrors; backup=$nvoBackup } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $nvoBackup 'result.json') -Encoding UTF8
    throw "Installation failed: $failure. Backup: $nvoBackup. Rollback errors: $($rollbackErrors.Count)"
}
$nvoResult = [PSCustomObject]@{
    status='installed'; packet='3C1'; version=306; backup=$nvoBackup;
    closed_processes=$nvoClosed;
    archived_removed=@($nvoBefore | Where-Object { $_.action -eq 'archive_remove' -and $_.existed }).Count;
    replaced=@($nvoBefore | Where-Object { $_.action -eq 'install' -and $_.existed }).Count;
    installed=@($nvoPlan.files | Where-Object action -eq 'install' | ForEach-Object { @{ path=$_.path; sha256=(File-Hash (Assert-ChildPath $nvoGame $_.path)) } });
    protected_files_verified=$nvoProtected.Count; game_relaunched=$false; gameplay_tested=$false
}
$nvoResult | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $nvoBackup 'result.json') -Encoding UTF8
$nvoResult | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $nvoWorkspace 'source\combat\step3c1\INSTALL-3C1-result.json') -Encoding UTF8
$nvoResult | ConvertTo-Json -Depth 6

param(
    [ValidateSet('Validate','Cleanup','Restore')][string]$Mode = 'Validate',
    [string]$BackupPath
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Workspace = 'C:\Users\regan\Documents\ChatGPT\NVO'
$Game = 'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas'
$Audit = Join-Path $Workspace 'reference\game-cleanup-20260915'
$PlanHash = 'c44c71bf731f0bd64869577e7c9ad8d741944f7b7947cf2d07ce3f6937ef79bf'

function Assert-NoReparse([string]$Path) {
    $cursor = [IO.Path]::GetFullPath($Path)
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse path refused: $cursor" }
        }
        $parent = [IO.Path]::GetDirectoryName($cursor)
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}
function Child([string]$Root, [string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative) -or $Relative.Contains(':')) { throw "Not a relative path: $Relative" }
    $base = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $full = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $full.StartsWith($base, [StringComparison]::OrdinalIgnoreCase)) { throw "Path escapes root: $full" }
    Assert-NoReparse $full
    return $full
}
function Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Verify([string]$Path, [string]$Expected, [long]$Bytes = -1) {
    Assert-NoReparse $Path
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "File missing: $Path" }
    if ($Bytes -ge 0 -and (Get-Item -LiteralPath $Path -Force).Length -ne $Bytes) { throw "Size changed: $Path" }
    if ((Hash $Path) -ne $Expected) { throw "SHA256 changed: $Path" }
}
function Write-Json([string]$Path, $Object) { $Object | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding utf8 }
function Assert-Idle {
    $busy = @(Get-Process FalloutNV,GECK,Vortex -ErrorAction SilentlyContinue)
    if ($busy.Count) { throw ('Close game/editor/mod manager before file changes: ' + ($busy.ProcessName -join ', ')) }
}
function Snapshot {
    $items = @{}
    foreach ($file in Get-ChildItem -LiteralPath $Game -File -Force -Recurse) {
        $relative = $file.FullName.Substring($Game.Length + 1).Replace('\','/')
        if (-not $Candidates.ContainsKey($relative)) {
            $items[$relative] = @{bytes=$file.Length; ticks=$file.LastWriteTimeUtc.Ticks}
        }
    }
    return $items
}

Assert-NoReparse $Workspace
Assert-NoReparse $Game
$PlanPath = Join-Path $Audit 'PLAN.json'
if ($Mode -eq 'Restore') {
    if (-not $BackupPath) { throw 'Restore requires the exact backup directory.' }
    $BackupPath = [IO.Path]::GetFullPath($BackupPath).TrimEnd('\')
    $relative = $BackupPath.Substring($Workspace.Length + 1)
    if ((Child $Workspace $relative) -ne $BackupPath -or -not $relative.StartsWith('backups\game-cleanup-20260915-')) { throw 'Unexpected backup directory.' }
    $PlanPath = Join-Path $BackupPath 'PLAN.json'
}
Verify $PlanPath $PlanHash
$Plan = Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
if ($Plan.workspace -ne $Workspace -or $Plan.game_root -ne $Game -or -not $Plan.archive_greenisle_authorized) { throw 'Plan scope mismatch.' }
if ($Plan.files.Count -ne 211 -or ($Plan.files | Measure-Object bytes -Sum).Sum -ne 27207663) { throw 'Plan count/size mismatch.' }
$Candidates = @{}
$Jobs = @()
$AllowedCategories = @('greenisle','orphan_cell_cache','orphan_config','orphan_editor_cache','stale_log','thumbnail_cache','unused_plugin','unused_plugin_backup')
foreach ($entry in $Plan.files) {
    if ($Candidates.ContainsKey($entry.path)) { throw "Duplicate path: $($entry.path)" }
    if ($entry.category -notin $AllowedCategories) { throw 'Unexpected category.' }
    $full = Child $Game $entry.path
    $extension = [IO.Path]::GetExtension($full).ToLowerInvariant()
    if ($extension -in @('.dll','.exe','.pdb','.nif','.dds','.kf','.wav','.mp3','.bik','.cpp','.h')) { throw "Protected extension: $full" }
    if ($extension -in @('.esm','.esp') -and $entry.path -notin @('Data/Cheat.esm','Data/knights.esm','Data/GreenIsle.esm')) { throw "Protected plugin: $full" }
    if ($extension -eq '.bsa' -and $entry.path -ne 'Data/GreenIsle.bsa') { throw "Protected archive: $full" }
    $Candidates[$entry.path] = $true
    $Jobs += [pscustomobject]@{path=$entry.path; source=$full; sha256=$entry.sha256; bytes=$entry.bytes}
}

if ($Mode -eq 'Restore') {
    Assert-Idle
    # Check every source and conflict before restoring any file. Never overwrite.
    foreach ($job in $Jobs) {
        Verify (Child (Join-Path $BackupPath 'originals') $job.path) $job.sha256 $job.bytes
        if (Test-Path -LiteralPath $job.source) { Verify $job.source $job.sha256 $job.bytes }
    }
    $restored = 0
    foreach ($job in $Jobs) {
        Assert-Idle
        if (-not (Test-Path -LiteralPath $job.source)) {
            $null = Child $Game $job.path
            $null = New-Item -ItemType Directory -Path (Split-Path -Parent $job.source) -Force
            Copy-Item -LiteralPath (Child (Join-Path $BackupPath 'originals') $job.path) -Destination $job.source
            Verify $job.source $job.sha256 $job.bytes
            $restored++
        }
    }
    Write-Json (Join-Path $BackupPath 'RESTORE-RESULT.json') @{status='restored'; restored_files=$restored; checked_files=$Jobs.Count; at=(Get-Date -Format o)}
    Write-Output "Restored $restored files; all 211 files match archived hashes."
    exit
}

if (Test-Path -LiteralPath (Join-Path $Audit 'RESULT.json')) { throw 'Cleanup already has a result; do not repeat this transaction.' }
foreach ($job in $Jobs) { Verify $job.source $job.sha256 $job.bytes }
$Protected = @{}
foreach ($entry in $Plan.foundation) {
    Verify (Child $Game $entry.path) $entry.sha256
    $Protected[$entry.path] = $entry.sha256
}
foreach ($name in $Plan.protected_plugins) {
    $plugin = $Plan.plugin_inventory.PSObject.Properties[$name].Value
    foreach ($master in $plugin.masters) { if ($master.ToLowerInvariant() -notin $Plan.protected_plugins) { throw "Missing protected master: $master" } }
    $relative = 'Data/' + $plugin.name
    Verify (Child $Game $relative) $plugin.sha256
    $Protected[$relative] = $plugin.sha256
}
foreach ($entry in $Plan.activation_files) { Verify $entry.path $entry.sha256 }
if ($Mode -eq 'Validate') { Write-Output 'Validated exact 211-file cleanup, master chain, packet 3E and activation hashes. No files changed.'; exit }

# Prior user authorization permits closing only the exact New Vegas game process.
$ClosedGame = $false
foreach ($process in @(Get-Process FalloutNV -ErrorAction SilentlyContinue)) {
    if ($process.Path -ne (Join-Path $Game 'FalloutNV.exe')) { throw 'Unexpected FalloutNV process path.' }
    $null = $process.CloseMainWindow()
    if (-not $process.WaitForExit(8000)) {
        $current = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
        if ($current) {
            if ($current.Path -ne (Join-Path $Game 'FalloutNV.exe')) { throw 'Process identity changed.' }
            Stop-Process -Id $current.Id -Force
        }
    }
    $ClosedGame = $true
}
Assert-Idle
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupPath = Child $Workspace ('backups/game-cleanup-20260915-' + $stamp + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
$Originals = Join-Path $BackupPath 'originals'
$null = New-Item -ItemType Directory -Path $Originals
Copy-Item -LiteralPath $PlanPath -Destination (Join-Path $BackupPath 'PLAN.json')
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $BackupPath 'execute_game_cleanup.ps1')
Copy-Item -LiteralPath (Join-Path $Audit 'PLAN.md') -Destination (Join-Path $BackupPath 'PLAN.md')

# Supplement pinned foundation hashes with every retained loose NVSE file and root executable/library.
$Extra = @(Get-ChildItem -LiteralPath (Join-Path $Game 'Data/nvse') -File -Recurse -Force)
$Extra += @(Get-ChildItem -LiteralPath $Game -File -Force | Where-Object { $_.Extension -in @('.dll','.exe','.pdb') })
foreach ($file in $Extra) {
    $relative = $file.FullName.Substring($Game.Length + 1).Replace('\','/')
    if (-not $Candidates.ContainsKey($relative) -and -not $Protected.ContainsKey($relative)) { $Protected[$relative] = Hash $file.FullName }
}
$Before = Snapshot
Write-Json (Join-Path $BackupPath 'RETAINED-BEFORE.json') $Before
Write-Json (Join-Path $BackupPath 'PROTECTED-HASHES.json') $Protected
foreach ($job in $Jobs) {
    $destination = Child $Originals $job.path
    $null = New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force
    Copy-Item -LiteralPath $job.source -Destination $destination
    Verify $destination $job.sha256 $job.bytes
}
Write-Output "Verified all 211 backup copies in $BackupPath"
$Removed = [Collections.Generic.List[string]]::new()
$Result = [ordered]@{status='started'; at=(Get-Date -Format o); backup=$BackupPath; plan_sha256=$PlanHash; game_closed=$ClosedGame; game_launched=$false; gameplay_tested=$false}
try {
    # No deletion occurs until every backup is verified. Recheck preimages at each exact file.
    foreach ($job in $Jobs) {
        Assert-Idle
        $checked = Child $Game $job.path
        Verify $checked $job.sha256 $job.bytes
        $Removed.Add($job.path)
        Write-Json (Join-Path $BackupPath 'JOURNAL.json') @{started_files=@($Removed.ToArray()); total=$Jobs.Count}
        Remove-Item -LiteralPath $checked -Force
    }
    foreach ($job in $Jobs) {
        if (Test-Path -LiteralPath $job.source) { throw "Candidate still present: $($job.path)" }
        Verify (Child $Originals $job.path) $job.sha256 $job.bytes
    }
    foreach ($relative in $Protected.Keys) { Verify (Child $Game $relative) $Protected[$relative] }
    foreach ($entry in $Plan.activation_files) { Verify $entry.path $entry.sha256 }
    $After = Snapshot
    if ($Before.Count -ne $After.Count) { throw 'Retained-file count changed.' }
    foreach ($relative in $Before.Keys) {
        if (-not $After.ContainsKey($relative) -or $Before[$relative].bytes -ne $After[$relative].bytes -or $Before[$relative].ticks -ne $After[$relative].ticks) { throw "Retained-file metadata changed: $relative" }
    }
    $Result.status = 'completed'
    $Result.archived_files = $Jobs.Count
    $Result.archived_bytes = [long]($Jobs | Measure-Object bytes -Sum).Sum
    $Result.retained_files_metadata_unchanged = $After.Count
    $Result.protected_hashes_unchanged = $Protected.Count
    $Result.activation_files_unchanged = $Plan.activation_files.Count
    $Result.required_master_chain_preserved = $true
    $Result.rd_master_retained = $true
    Write-Json (Join-Path $BackupPath 'RETAINED-AFTER.json') $After
} catch {
    $Result.status = 'failed_rollback_attempted'
    $Result.error = $_.Exception.Message
    $rollbackErrors = @()
    foreach ($relative in $Removed) {
        try {
            $job = $Jobs | Where-Object path -eq $relative
            $destination = Child $Game $relative
            if (-not (Test-Path -LiteralPath $destination)) {
                Verify (Child $Originals $relative) $job.sha256 $job.bytes
                Copy-Item -LiteralPath (Child $Originals $relative) -Destination $destination
            }
            Verify $destination $job.sha256 $job.bytes
        } catch { $rollbackErrors += $_.Exception.Message }
    }
    $Result.rollback_errors = $rollbackErrors
}
$Result.finished_at = Get-Date -Format o
Write-Json (Join-Path $BackupPath 'RESULT.json') $Result
Write-Json (Join-Path $Audit 'RESULT.json') $Result
$restoreText = @"
# Restore the archived files

Close New Vegas, GECK and Vortex. Run this in PowerShell:

    & '$BackupPath\execute_game_cleanup.ps1' -Mode Restore -BackupPath '$BackupPath'

The script verifies the pinned plan and all archived hashes, restores missing files only and refuses conflicting existing files. It preserves this archive. Review PLAN.md for the exact file list. No load-order or activation files were edited by cleanup.
"@
$restoreText | Set-Content -LiteralPath (Join-Path $BackupPath 'RESTORE.md') -Encoding utf8
$Result | ConvertTo-Json -Depth 6
if ($Result.status -ne 'completed') { throw 'Cleanup failed; inspect RESULT.json and rollback status.' }

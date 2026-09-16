$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-PlainPath([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $cursor = $full
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Linked path requires review: $cursor"
            }
        }
        $parent = Split-Path -Path $cursor -Parent
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
    return $full
}
function Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }

$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'PACKET.json') -Raw | ConvertFrom-Json
if ($manifest.packet -ne '3I') { throw 'Wrong packet manifest.' }
$workspace = Assert-PlainPath 'C:\Users\regan\Documents\ChatGPT\NVO'
$game = Assert-PlainPath 'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas'
$target = Assert-PlainPath (Join-Path $game 'Data\NVO.esm')
$source = Assert-PlainPath (Join-Path $PSScriptRoot 'Staged\Data\NVO.esm')
$rd = Assert-PlainPath (Join-Path $game 'Data\RD.esm')
$expectedOld = '2bb53410287c1c409a0bbb9b51ef38bf14bba2a4e3376f23b5cfc9f73fc0028d'
$expectedNew = '2d0760c96dfd7cb06a95d4736891f67a98f5f5c25c148eb572a5fd75741e795b'
$expectedRD = '9498ee5bee4119ec289b8f88af83e3bbd0ff2e2ec57e45809f3e18dd8b139bc3'
if ((Hash $source) -ne $expectedNew -or (Hash $rd) -ne $expectedRD) { throw 'Prepared file or RD changed. Ask for a refreshed packet.' }
if ((Hash $target) -eq $expectedNew) { Write-Host 'Player baseline already applied. Next: compile the three scripts in GECK.'; exit 0 }
if ((Hash $target) -ne $expectedOld) { throw 'NVO.esm has newer or different edits. Nothing replaced. Ask for a refreshed packet.' }
$blockers = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(FalloutNV|GECK|GECKExtender|Geck_extender|Vortex|FNVEdit|xEdit)$' })
if ($blockers.Count -gt 0) { throw "Close the game, save/close GECK and close Vortex/xEdit before applying. Running: $($blockers.ProcessName -join ', ')" }

$backupRoot = Assert-PlainPath (Join-Path $workspace 'backups')
$backup = Assert-PlainPath (Join-Path $backupRoot ('combat-records-3I-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)))
if (-not $backup.StartsWith($backupRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid backup destination.' }
$null = New-Item -ItemType Directory -Path $backup
$prior = Join-Path $backup 'NVO.esm'
Copy-Item -LiteralPath $target -Destination $prior
Copy-Item -LiteralPath $rd -Destination (Join-Path $backup 'RD.esm')
if ((Hash $prior) -ne $expectedOld -or (Hash $target) -ne $expectedOld) { throw 'Baseline changed during backup. Nothing replaced.' }
$replaced = $false
try {
    # Only this exact file is unlinked, never recursively. This avoids writing
    # through a Vortex hard link into its staging copy.
    $null = Assert-PlainPath $target
    Remove-Item -LiteralPath $target
    $replaced = $true
    Copy-Item -LiteralPath $source -Destination $target
    if ((Hash $target) -ne $expectedNew -or (Hash $rd) -ne $expectedRD) { throw 'Post-copy verification failed.' }
    [ordered]@{ packet='3I'; status='player_baseline_applied_scripts_pending'; target=$target; backup=$backup; before=$expectedOld; after=$expectedNew; rd_unchanged=$true; native_replaced=$false; scripts_compiled=$false } |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'receipt.json') -Encoding UTF8
    Write-Host "Player baseline applied. Backup: $backup"
    Write-Host 'Now use NVO.esm as active in GECK and compile the THREE complete scripts from START-HERE.html.'
    Write-Host 'The old compiled startup messages remain until those scripts are compiled and the ESM is saved.'
} catch {
    if ($replaced) {
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target }
        Copy-Item -LiteralPath $prior -Destination $target
        if ((Hash $target) -ne $expectedOld) { throw "Restore failed. Original backup is $prior" }
    }
    throw
}

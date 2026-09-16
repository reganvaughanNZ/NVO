$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$game = 'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas'
$data = Join-Path $game 'Data'
$target = Join-Path $data 'NVO.esm'
$packet = Join-Path $workspace 'source\combat\step3j\cleanup'
$prepared = Join-Path $packet 'Data\NVO.esm'
$oldHash = 'e75f142b75e8b85ea63917905d287fbbb7407008b1e9de139475d1ae2a504845'
$newHash = 'fb25c3c6362c3ef0c5a3f9d67625aa433dfe8379c2bb77fc7d492800b4dc5e4d'
function AssertHash([string]$path,[string]$hash) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hash) { throw "File changed; installation stopped: $path" }
}
$protected = @{
    (Join-Path $data 'NVSE\Plugins\NVOCombatCore.dll') = '6f53637f281243bbc9e1d2566adf6cc850e8bee5cf7c70299ca03709891455f6'
    (Join-Path $data 'NVSE\Plugins\NVOCombatCore.pdb') = '292ee2664af3a68298b4229a2665778a79124fafcfccb69d6501db7a9e89ee64'
    (Join-Path $data 'NVOFlightPilot.esp') = 'bc522fba37ff5f7c5b622bf3a7cb53235d8daac587735d9ae920b042d0c7fe8f'
}
AssertHash $target $oldHash
AssertHash $prepared $newHash
foreach ($entry in $protected.GetEnumerator()) { AssertHash $entry.Key $entry.Value }
if (Test-Path -LiteralPath (Join-Path $data 'RD.esm')) { throw 'RD.esm has returned; investigate first.' }
$editors = @(Get-Process -Name geck,Vortex,FNVEdit,xFOEdit,xFOEdit64 -ErrorAction SilentlyContinue)
if ($editors.Count) { throw ('Close editors before installation: ' + ($editors.ProcessName -join ', ')) }
foreach ($proc in @(Get-Process -Name FalloutNV -ErrorAction SilentlyContinue)) {
    if ([IO.Path]::GetFullPath($proc.Path) -ne (Join-Path $game 'FalloutNV.exe')) { throw 'Unexpected game process path.' }
    Stop-Process -Id $proc.Id
    $proc.WaitForExit(10000) | Out-Null
    if (-not $proc.HasExited) { throw 'Game is still running.' }
}
$backup = [IO.Path]::GetFullPath((Join-Path $workspace ('backups\combat-3J-cleanup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))))
if (-not $backup.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid backup path.' }
New-Item -ItemType Directory -Path $backup | Out-Null
$saved = Join-Path $backup 'NVO.esm'
[IO.File]::WriteAllBytes($saved,[IO.File]::ReadAllBytes($target))
AssertHash $saved $oldHash
if ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($target)) -ne $data) { throw 'Invalid target path.' }
$changed = $false
try {
    # Unlink only this exact file before copying, protecting any old hardlink.
    $changed = $true
    Remove-Item -LiteralPath $target
    Copy-Item -LiteralPath $prepared -Destination $target
    AssertHash $target $newHash
    foreach ($entry in $protected.GetEnumerator()) { AssertHash $entry.Key $entry.Value }
    $receipt = [ordered]@{status='installed'; date=(Get-Date -Format o); backup=$backup; previous_sha256=$oldHash; installed_sha256=$newHash; bytes=453236; removed_duplicate_scripts=3; bootstrap_compiled_code_promoted_to_original=$true; native_and_pilot_unchanged=$true; activation_files_changed=$false; rd_still_absent=$true; assistant_gameplay_tested=$false}
    $json = $receipt | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $packet 'INSTALL-RECEIPT.json'),$json)
    [IO.File]::WriteAllText((Join-Path $backup 'INSTALL-RECEIPT.json'),$json)
    Write-Output $json
} catch {
    $problem = $_
    if ($changed) {
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target }
        Copy-Item -LiteralPath $saved -Destination $target
        AssertHash $target $oldHash
    }
    throw $problem
}

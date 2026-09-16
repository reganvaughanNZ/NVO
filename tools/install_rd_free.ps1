$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$game = 'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas'
$data = Join-Path $game 'Data'
$profile = 'C:\Users\regan\AppData\Local\FalloutNV'
$package = Join-Path $workspace 'release\NVO-Combat-Packet-3J-RD-Free'
$nvo = Join-Path $data 'NVO.esm'
$rd = Join-Path $data 'RD.esm'
$plugins = Join-Path $profile 'plugins.txt'
$loadorder = Join-Path $profile 'loadorder.txt'
$expected = @{
    $nvo = '2bb53410287c1c409a0bbb9b51ef38bf14bba2a4e3376f23b5cfc9f73fc0028d'
    $rd = '9498ee5bee4119ec289b8f88af83e3bbd0ff2e2ec57e45809f3e18dd8b139bc3'
    $plugins = '7aa80eab19487289fb74052da3e9c02d2f3d9a4eba01fb9c700f7ebfc8d271ca'
    $loadorder = '905dfd6e4411e20449ab93af58d9c9bf56f2d6e91f58e1494ce5b4775adac156'
}
$protected = @{
    (Join-Path $data 'NVOFlightPilot.esp') = 'bc522fba37ff5f7c5b622bf3a7cb53235d8daac587735d9ae920b042d0c7fe8f'
    (Join-Path $data 'NVSE\Plugins\NVOCombatCore.dll') = '6f53637f281243bbc9e1d2566adf6cc850e8bee5cf7c70299ca03709891455f6'
    (Join-Path $data 'NVSE\Plugins\NVOCombatCore.pdb') = '292ee2664af3a68298b4229a2665778a79124fafcfccb69d6501db7a9e89ee64'
}
function AssertHash([string]$path,[string]$hash) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hash) { throw "Changed file; installation stopped: $path" }
}
foreach ($entry in $expected.GetEnumerator()) { AssertHash $entry.Key $entry.Value }
foreach ($entry in $protected.GetEnumerator()) { AssertHash $entry.Key $entry.Value }
$newHash = '2c005477f719ff6e2884d7ffeb6c7d547a0146196869999e14b8bff9e560ea98'
$prepared = Join-Path $package 'Data\NVO.esm'
AssertHash $prepared $newHash
$editors = @(Get-Process -Name geck,GECK,Vortex,FNVEdit,xFOEdit,xFOEdit64 -ErrorAction SilentlyContinue)
if ($editors.Count) { throw ('Close the editor/mod manager first: ' + ($editors.ProcessName -join ', ')) }
foreach ($proc in @(Get-Process -Name FalloutNV -ErrorAction SilentlyContinue)) {
    if ([IO.Path]::GetFullPath($proc.Path) -ne (Join-Path $game 'FalloutNV.exe')) { throw 'Unexpected FalloutNV process path.' }
    Stop-Process -Id $proc.Id
    $proc.WaitForExit(10000) | Out-Null
    if (-not $proc.HasExited) { throw 'FalloutNV is still running.' }
}
$order = @('FalloutNV.esm','DeadMoney.esm','HonestHearts.esm','OldWorldBlues.esm','LonesomeRoad.esm','GunRunnersArsenal.esm','ClassicPack.esm','MercenaryPack.esm','TribalPack.esm','CaravanPack.esm','NVO.esm','NVOFlightPilot.esp')
foreach ($name in $order) { if (-not (Test-Path -LiteralPath (Join-Path $data $name) -PathType Leaf)) { throw "Missing retained file: $name" } }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = [IO.Path]::GetFullPath((Join-Path $workspace ('backups\rd-removal-3J-' + $stamp)))
if (-not $backup.StartsWith($workspace + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Backup escaped workspace.' }
New-Item -ItemType Directory -Path $backup | Out-Null
foreach ($path in @($nvo,$rd,$plugins,$loadorder)) {
    $copy = Join-Path $backup ([IO.Path]::GetFileName($path))
    [IO.File]::WriteAllBytes($copy,[IO.File]::ReadAllBytes($path))
    AssertHash $copy $expected[$path]
}
$changed = $false
try {
    # Exact, nonrecursive operations. Unlink first so Vortex hardlinks cannot
    # propagate this replacement back into an older source/staging file.
    foreach ($path in @($nvo,$rd)) { if ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($path)) -ne $data) { throw 'Unexpected game file path.' } }
    $changed = $true
    Remove-Item -LiteralPath $nvo
    Copy-Item -LiteralPath $prepared -Destination $nvo
    AssertHash $nvo $newHash
    $ascii = [Text.Encoding]::ASCII
    [IO.File]::WriteAllText($plugins, '# NVO Packet 3J: official content + NVO, RD retired.' + "`r`n" + ($order -join "`r`n") + "`r`n", $ascii)
    [IO.File]::WriteAllText($loadorder, '# NVO Packet 3J load order' + "`r`n" + ($order -join "`r`n") + "`r`n", $ascii)
    AssertHash $rd $expected[$rd]
    Remove-Item -LiteralPath $rd
    if (Test-Path -LiteralPath $rd) { throw 'RD was not removed from Data.' }
    foreach ($entry in $protected.GetEnumerator()) { AssertHash $entry.Key $entry.Value }
    $receipt = [ordered]@{ status='installed'; date=(Get-Date -Format o); backup=$backup; nvo_sha256=$newHash; rd_archived_to=(Join-Path $backup 'RD.esm'); official_dlc_explicitly_active=$true; native_version=318; native_and_pilot_unchanged=$true; game_tested=$false; quiet_scripts_geck_compiled=$false; load_order=$order }
    $json = $receipt | ConvertTo-Json -Depth 5
    [IO.File]::WriteAllText((Join-Path $workspace 'source\combat\step3j\INSTALL-RECEIPT.json'), $json)
    [IO.File]::WriteAllText((Join-Path $package 'INSTALL-RECEIPT.json'), $json)
    [IO.File]::WriteAllText((Join-Path $backup 'INSTALL-RECEIPT.json'), $json)
    Write-Output $json
} catch {
    $problem = $_
    if ($changed) {
        foreach ($path in @($nvo,$rd,$plugins,$loadorder)) {
            if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path }
            Copy-Item -LiteralPath (Join-Path $backup ([IO.Path]::GetFileName($path))) -Destination $path
            AssertHash $path $expected[$path]
        }
    }
    throw $problem
}

# Read-only capture of a bounded code region from the user's already running game.
# No game launch, injection, engine calls, suspension or process-memory writes.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$nvoWorkspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$nvoGamePath = 'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas\FalloutNV.exe'
$nvoProcesses = @(Get-Process -Name FalloutNV -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -and [IO.Path]::GetFullPath($_.Path) -eq $nvoGamePath
})
if ($nvoProcesses.Count -ne 1) { throw 'Leave one Fallout New Vegas instance open at its main menu, then retry.' }
$nvoProcess = $nvoProcesses[0]
$nvoStartTime = $nvoProcess.StartTime.ToUniversalTime().ToString('o')

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class NvoScalingReadOnly {
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern IntPtr OpenProcess(uint access, bool inherit, uint id);
    [DllImport("kernel32.dll", SetLastError=true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool ReadProcessMemory(IntPtr process, IntPtr address,
        [Out] byte[] buffer, UIntPtr size, out UIntPtr bytesRead);
    [DllImport("kernel32.dll", SetLastError=true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CloseHandle(IntPtr handle);
}
'@
# PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, never VM_WRITE/OPERATION.
$nvoHandle = [NvoScalingReadOnly]::OpenProcess(0x1010, $false, [uint32]$nvoProcess.Id)
if ($nvoHandle -eq [IntPtr]::Zero) { throw "Read-only OpenProcess failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())" }
function Read-CodeBytes([UInt32]$Address, [int]$Count) {
    $bytes = New-Object byte[] $Count
    $got = [UIntPtr]::Zero
    if (-not [NvoScalingReadOnly]::ReadProcessMemory($nvoHandle, [IntPtr][long]$Address, $bytes, [UIntPtr][uint32]$Count, [ref]$got) -or $got.ToUInt64() -ne $Count) {
        throw ('Read-only capture failed at 0x{0:X8}' -f $Address)
    }
    return ,$bytes
}
try {
    $nvoHeader = Read-CodeBytes 0x400000 4096
    $nvoPe = [BitConverter]::ToInt32($nvoHeader, 0x3C)
    if ($nvoHeader[0] -ne 0x4D -or $nvoHeader[1] -ne 0x5A -or $nvoPe -lt 64 -or $nvoPe -gt 3500) { throw 'Unexpected loaded image header.' }
    if ([BitConverter]::ToUInt32($nvoHeader, $nvoPe) -ne 0x4550 -or
        [BitConverter]::ToUInt16($nvoHeader, $nvoPe+4) -ne 0x14C -or
        [BitConverter]::ToUInt32($nvoHeader, $nvoPe+8) -ne 0x4E0D50ED -or
        [BitConverter]::ToUInt16($nvoHeader, $nvoPe+24) -ne 0x10B -or
        [BitConverter]::ToUInt32($nvoHeader, $nvoPe+52) -ne 0x400000 -or
        [BitConverter]::ToUInt32($nvoHeader, $nvoPe+80) -ne 0x107B000) { throw 'Runtime identity does not match the inspected FNV image.' }
    # Bounded code, settings and difficulty metadata only. No engine calls.
    $nvoRanges = @(
        @{name='hitme_tail_and_health_apply'; address=0x89BF60; count=0x2200},
        @{name='health_scaling'; address=0x8808A0; count=0x800},
        @{name='difficulty_multiplier_selector'; address=0x648CB0; count=0x80},
        @{name='difficulty_getter'; address=0x5BE4D0; count=0x20},
        @{name='difficulty_setting_tables'; address=0x119B310; count=0x28},
        @{name='setting_value_getter'; address=0x403E20; count=0x50}
    )
    $nvoCaptured = @()
    foreach ($r in $nvoRanges) {
        $first = Read-CodeBytes $r.address $r.count
        $second = Read-CodeBytes $r.address $r.count
        if ([Convert]::ToBase64String($first) -ne [Convert]::ToBase64String($second)) { throw 'Code changed during capture.' }
        $nvoCaptured += @{name=$r.name; address=$r.address; bytes=$first}
    }
    $nvoSettings = @()
    $nvoSpecs = Get-Content -LiteralPath (Join-Path $nvoWorkspace 'source\combat\step3l\SETTING-ADDRESSES.json') -Raw | ConvertFrom-Json
    foreach ($s in $nvoSpecs) {
        $first = Read-CodeBytes ([uint32]$s.address) 12
        $second = Read-CodeBytes ([uint32]$s.address) 12
        if ([Convert]::ToBase64String($first) -ne [Convert]::ToBase64String($second)) { throw 'Setting changed during capture.' }
        $namePointer = [BitConverter]::ToUInt32($first,8)
        if ($namePointer -lt 0x400000 -or $namePointer -gt 0x7FFFFFFF) { throw 'Setting name pointer outside expected range.' }
        $nameBytes = Read-CodeBytes $namePointer 96
        $nul = [Array]::IndexOf($nameBytes,[byte]0)
        if ($nul -lt 1) { throw 'Setting name not terminated within96 bytes.' }
        $actualName = [Text.Encoding]::ASCII.GetString($nameBytes,0,$nul)
        if ($actualName -cne $s.name -and -not ($s.name -eq 'iDifficulty' -and $actualName -ieq 'iDifficulty:GamePlay')) { throw "Setting name mismatch: expected $($s.name), got $actualName" }
        $value = if ($s.name -eq 'iDifficulty') { [BitConverter]::ToInt32($first,4) } else { [BitConverter]::ToSingle($first,4) }
        $nvoSettings += [ordered]@{name=$s.name; actual_name=$actualName; address=('{0:X8}' -f [uint32]$s.address); value=$value; object_bytes=[Convert]::ToBase64String($first); scope='main_menu_current_value'}
    }
    # 008808A0 uses PlayerCharacter.cachedDifficulty via 005BE4D0, not the INI
    # setting directly. Read only this field after checking identity; no calls.
    $playerPointer = [BitConverter]::ToUInt32((Read-CodeBytes 0x11DEA3C 4),0)
    if ($playerPointer -lt 0x10000 -or $playerPointer -gt 0x7FFFF000) { throw 'Invalid player singleton pointer.' }
    $playerHeader = Read-CodeBytes $playerPointer 16
    if ([BitConverter]::ToUInt32($playerHeader,0) -ne 0x108AA3C -or [BitConverter]::ToUInt32($playerHeader,12) -ne 0x14) { throw 'Unexpected player identity.' }
    $difficultyField = Read-CodeBytes ($playerPointer+0x7B8) 4
    $difficultyAgain = Read-CodeBytes ($playerPointer+0x7B8) 4
    if ([Convert]::ToBase64String($difficultyField) -ne [Convert]::ToBase64String($difficultyAgain) -or [BitConverter]::ToUInt32((Read-CodeBytes 0x11DEA3C 4),0) -ne $playerPointer) { throw 'Difficulty identity changed.' }
    $nvoDifficulty = [ordered]@{scope='main_menu_current_value'; getter='005BE4D0'; field_offset='000007B8'; value=[BitConverter]::ToInt32($difficultyField,0); identity_checked=$true; bytes=[Convert]::ToBase64String($difficultyField)}
    $nvoStill = Get-Process -Id $nvoProcess.Id -ErrorAction Stop
    if ($nvoStill.Path -ne $nvoGamePath -or $nvoStill.StartTime.ToUniversalTime().ToString('o') -ne $nvoStartTime) { throw 'Process identity changed during capture.' }
    $nvoDest = [IO.Path]::GetFullPath((Join-Path $nvoWorkspace ('source\combat\step3l\runtime-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))))
    if (-not $nvoDest.StartsWith($nvoWorkspace+'\', [StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $nvoDest)) { throw 'Unexpected or existing output directory.' }
    $null = New-Item -ItemType Directory -Path $nvoDest
    $nvoFiles = @()
    foreach ($r in $nvoCaptured) {
        $name = '{0}-{1:X8}.bin' -f $r.name,$r.address
        $path = Join-Path $nvoDest $name
        [IO.File]::WriteAllBytes($path, $r.bytes)
        $nvoFiles += @{name=$r.name; address=('{0:X8}' -f $r.address); bytes=$r.bytes.Length; filename=$name; sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()}
    }
    $nvoManifest = [ordered]@{
        captured_at=(Get-Date).ToString('o'); pid=$nvoProcess.Id; process_start_utc=$nvoStartTime;
        process_path=$nvoGamePath; access='QUERY_LIMITED_INFORMATION|VM_READ';
        settings=$nvoSettings; cached_difficulty=$nvoDifficulty; files=$nvoFiles; code_stable_across_two_reads=$true; process_write_or_injection=$false; game_launched=$false
    }
    $nvoManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $nvoDest 'manifest.json') -Encoding UTF8
    $nvoDest
} finally {
    $null = [NvoScalingReadOnly]::CloseHandle($nvoHandle)
}




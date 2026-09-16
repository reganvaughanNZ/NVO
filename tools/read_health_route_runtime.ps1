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
public static class NvoHealthRouteReadOnly {
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
$nvoHandle = [NvoHealthRouteReadOnly]::OpenProcess(0x1010, $false, [uint32]$nvoProcess.Id)
if ($nvoHandle -eq [IntPtr]::Zero) { throw "Read-only OpenProcess failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())" }
function Read-CodeBytes([UInt32]$Address, [int]$Count) {
    $bytes = New-Object byte[] $Count
    $got = [UIntPtr]::Zero
    if (-not [NvoHealthRouteReadOnly]::ReadProcessMemory($nvoHandle, [IntPtr][long]$Address, $bytes, [UIntPtr][uint32]$Count, [ref]$got) -or $got.ToUInt64() -ne $Count) {
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
    # Bounded method/vtable captures only. No actor/save contents or engine calls.
    $nvoRanges = @(
        @{name='hitme'; address=0x89A760; count=0x1800},
        @{name='character_damage'; address=0x881130; count=0x500},
        @{name='creature_damage'; address=0x8D49F0; count=0x500},
        @{name='player_damage'; address=0x93B7A0; count=0x700},
        @{name='character_getav'; address=0x8805F0; count=0x180},
        @{name='creature_getav'; address=0x8D4870; count=0x180},
        @{name='player_getav'; address=0x93ACB0; count=0x180},
        @{name='npc_damage_modifier'; address=0x8B0D70; count=0x500},
        @{name='player_damage_modifier'; address=0x94C490; count=0x500},
        @{name='av_notify'; address=0x66E900; count=0x1000},
        @{name='character_tables'; address=0x10869A4; count=0x500},
        @{name='creature_tables'; address=0x1086FE4; count=0x500},
        @{name='player_tables'; address=0x108A974; count=0x500}
    )
    $nvoCaptured = @()
    foreach ($r in $nvoRanges) {
        $first = Read-CodeBytes $r.address $r.count
        $second = Read-CodeBytes $r.address $r.count
        if ([Convert]::ToBase64String($first) -ne [Convert]::ToBase64String($second)) { throw 'Code changed during capture.' }
        $nvoCaptured += @{name=$r.name; address=$r.address; bytes=$first}
    }
    $nvoStill = Get-Process -Id $nvoProcess.Id -ErrorAction Stop
    if ($nvoStill.Path -ne $nvoGamePath -or $nvoStill.StartTime.ToUniversalTime().ToString('o') -ne $nvoStartTime) { throw 'Process identity changed during capture.' }
    $nvoDest = [IO.Path]::GetFullPath((Join-Path $nvoWorkspace ('source\combat\step3k\runtime-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))))
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
        files=$nvoFiles; code_stable_across_two_reads=$true; process_write_or_injection=$false; game_launched=$false
    }
    $nvoManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $nvoDest 'manifest.json') -Encoding UTF8
    $nvoDest
} finally {
    $null = [NvoHealthRouteReadOnly]::CloseHandle($nvoHandle)
}




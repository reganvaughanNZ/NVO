"""One-time source assembly for the bounded native flight pilot; no game writes."""
from pathlib import Path
import hashlib, json
R=Path(__file__).resolve().parents[1]
P=R/'native/NVOCombatCore'
snap=R/'source/combat/step3c/runtime-20260915-121449'
fingerprints=[]
for name,address,size in [('movement',0x92F260,0x123C),('matrix_vector',0x4B4500,0xAC),('rotation_matrix',0x4A0C90,0x300),('projectile_move',0x9BF300,0x16C),('projectile_update',0x9B8030,0x865)]:
    data=(snap/f'{name}-{address:08X}.bin').read_bytes()[:size]
    assert len(data)==size
    h=14695981039346656037
    for b in data: h=((h^b)*1099511628211)&0xffffffffffffffff
    fingerprints.append(dict(name=name,address=f'{address:08X}',size=size,fnv1a64=f'{h:016X}',sha256=hashlib.sha256(data).hexdigest()))
guard='''bool Guard() noexcept
{
    const auto game=GetModuleHandleW(nullptr);
    IMAGE_DOS_HEADER dos{}; IMAGE_NT_HEADERS32 nt{};
    if (reinterpret_cast<std::uintptr_t>(game)!=0x400000 || !Read(game,0,dos)
        || dos.e_magic!=IMAGE_DOS_SIGNATURE || dos.e_lfanew<0x40 || dos.e_lfanew>0x1000
        || !Read(game,dos.e_lfanew,nt) || nt.Signature!=IMAGE_NT_SIGNATURE
        || nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_I386 || nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR32_MAGIC
        || nt.FileHeader.TimeDateStamp!=0x4E0D50ED || nt.OptionalHeader.SizeOfImage!=0x107B000) return false;
    return '''+'\n        && '.join(f'Fingerprint(0x{f["address"]},0x{f["size"]:X},0x{f["fnv1a64"]}ull)' for f in fingerprints)+''';
}'''
path=P/'src/FlightPhysics.cpp'
s=path.read_text().replace('bool Guard() noexcept; // generated fingerprint list below',guard)
s=s.replace('Read(base,0x6C,gravity)','Read(base,0x64,gravity)')
s=s.replace('    char section[2048]{};\n    const DWORD length=GetPrivateProfileSectionA("Physics",section,sizeof(section),"");\n    (void)length; // Wide path below avoids locale-dependent installation paths.\n','')
path.write_text(s)
(P/'reference/FLIGHT-PHYSICS-SOURCE.json').write_text(json.dumps(dict(packet='3C',capture=str(snap.relative_to(R)),fingerprints=fingerprints,donor='BallistX 5.4',donor_archive_sha256='d71fe28f1262dec7a0f2086f06b243168d74a3f11d8b57cd8b7b8127c9506e3d',tables_source='source/combat/step3a/NVO-Flight-Pilot.json',adaptations=['G1/G7 linear interpolation','RK4 gravity and drag','no donor damage/deletion/roll-state code'],guard_normalization='Only this DLL-owned five-byte CALL is normalized for subsequent capture guards.'),indent=2)+'\n')
path=P/'src/FlightPreview.cpp';s=path.read_text()
s=s.replace('#include "FlightTiming.hpp"','#include "FlightTiming.hpp"\n#include "FlightPhysics.hpp"')
s=s.replace('nvo::timing::BeginCapture(session);','{ nvo::timing::BeginCapture(session); nvo::physics::BeginCapture(session); }')
s=s.replace('    nvo::timing::Suspend(reason);','    nvo::physics::Suspend(reason);\n    nvo::timing::Suspend(reason);')
s=s.replace('    nvo::timing::Event(projectile, lifetime, destroyed);','    nvo::physics::Event(projectile, lifetime, destroyed);\n    nvo::timing::Event(projectile, lifetime, destroyed);')
start=s.index('    // Timing remains restricted')
end=s.index('    const double settingSpeed',start)
restriction=s[start:end]
# Shared private identity selection before any diagnostic quota.
condition=restriction[restriction.index('    if ('):restriction.index('        nvo::timing::Track')].strip()
insertion='''    const auto& p = gProfiles[profile];
    '''+condition+'''
        nvo::physics::Track(projectile, lifetime, source, weapon, ammo, state.base, p.weapon.local == 0x800 ? 0u : 1u);
'''
s=s[:start]+restriction+s[end:]
s=s.replace('    ++gMatched;\n','    ++gMatched;\n'+insertion)
# Remove second declaration after quota (first one is now above quota).
s=s.replace('    ++gCreateRows;\n    const auto& p = gProfiles[profile];','    ++gCreateRows;')
s=s.replace('native_flight_writes=0','preview_writes=0').replace('flight_writes=0','preview_writes=0').replace('future_flight_authority=disabled','native_flight_authority=see_PHYSICS_READY')
path.write_text(s)
path=P/'src/FlightTiming.cpp';s=path.read_text().replace('flight_writes=0','timing_writes=0');path.write_text(s)
path=P/'src/Plugin.cpp';s=path.read_text().replace('#include "DamageEvents.hpp"','#include "DamageEvents.hpp"\n#include "FlightPhysics.hpp"')
s=s.replace('304; // 0.3.4, packet 3B3A thread correction','305; // 0.3.5, packet 3C private gravity/drag pilot')
s=s.replace('nvo::log::Write("LIFECYCLE deferred_init");','nvo::log::Write("LIFECYCLE deferred_init");\n        nvo::physics::Initialize();')
s=s.replace('0.3.4 | phase=3B3A','0.3.5 | phase=3C').replace('| flight_writes=0 |','| native_physics_pending=1 |')
path.write_text(s)
path=P/'BUILD.cmd';s=path.read_text().replace('"%NVO_PROJECT_DIR%\\src\\FlightTiming.cpp" /link','"%NVO_PROJECT_DIR%\\src\\FlightTiming.cpp" "%NVO_PROJECT_DIR%\\src\\FlightPhysics.cpp" /link');path.write_text(s)
path=P/'CMakeLists.txt';s=path.read_text().replace('VERSION 0.3.4','VERSION 0.3.5').replace('src/FlightTiming.cpp src/Exports.def','src/FlightTiming.cpp src/FlightPhysics.cpp src/Exports.def');path.write_text(s)
path=P/'src/NativeLog.cpp';s=path.read_text().replace('#include <cwchar>','#include <cwchar>\n#include <cstring>')
s=s.replace('unsigned gRows = 0;\nconstexpr unsigned kMaximumRows = 8192;','unsigned gRows = 0, gDetailRows = 0, gPriorityRows = 0;\nconstexpr unsigned kMaximumDetail = 7168, kMaximumPriority = 1024;')
s=s.replace('    gRows = 0;','    gRows = gDetailRows = gPriorityRows = 0;')
s=s.replace('    if (!gReady || gRows >= kMaximumRows) {','''    const bool priority = std::strstr(format, "SUMMARY") || std::strstr(format, "LIFECYCLE")
        || std::strstr(format, "READY") || std::strstr(format, "DISABLED") || std::strstr(format, "REJECT")
        || std::strstr(format, "PHYSICS_SHOT") || std::strstr(format, "FLIGHT_TIMING_SHOT")
        || std::strstr(format, "NVOCombatCore");
    if (!gReady || (priority ? gPriorityRows >= kMaximumPriority : gDetailRows >= kMaximumDetail)) {''')
s=s.replace('    if (gRows == kMaximumRows) {\n        constexpr char footer[] = "END native log process limit reached\\r\\n";','''    if (priority) ++gPriorityRows; else ++gDetailRows;
    if (!priority && gDetailRows == kMaximumDetail) {
        constexpr char footer[] = "DETAIL_LIMIT reached; lifecycle and summaries retain separate bounded reserve\\r\\n";''')
path.write_text(s)
print('Prepared packet 3C source integration and fingerprints. No game files changed.')

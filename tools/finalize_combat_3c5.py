"""Record and package the actual install without rewriting prior file hashes."""
from pathlib import Path
import hashlib, json, shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'source/combat/step3c5'
RELEASE=ROOT/'release/NVO-Combat-Packet-3C5-Compiled'
result=json.loads((PACKET/'INSTALL-3C5-result.json').read_text(encoding='utf-8-sig'))
plan=json.loads((PACKET/'INSTALL-3C5-plan.json').read_text())
manifest=json.loads((RELEASE/'manifest.json').read_text())
evidence=json.loads((RELEASE/'build-evidence/static-evidence.json').read_text())
assert result['status']=='installed' and result['version']==310 and len(result['installed'])==2
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for row in result['installed']:
    assert digest(Path(plan['game_root'])/row['path'])==row['sha256']==digest(RELEASE/row['path'])
backup=Path(result['backup'])
before=json.loads((backup/'before.json').read_text(encoding='utf-8-sig'))
for row in before['before']:
    assert digest(backup/'originals'/row['path'])==row['sha256']
closed='The game was already closed.' if not result['closed_processes'] else f"Closed processes: {result['closed_processes']}."
receipt=f'''# Packet 3C5 installation receipt

Installed NVOCombatCore 0.3.10 / 310. The installed DLL/PDB match the compiled release. {result['protected_files_verified']} protected entries were verified unchanged, including NVO.esm, NVOFlightPilot.esp, configuration, activation and other extenders.

{closed} No game launch, gameplay, GECK work or configuration edit occurred. Runtime correction acceptance is pending.

Backup: `{backup}`

With the game closed, restore both previous version 309 files from the backup's `originals/Data/NVSE/Plugins` to the same relative game directory to reverse:

- NVOCombatCore.dll
- NVOCombatCore.pdb

DLL SHA256: {evidence['dll_sha256']}

PDB SHA256: {evidence['pdb_sha256']}

Build: native/NVOCombatCore/{manifest['build_output']}. Zero warnings/errors, PE32 x86, exactly the two NVSE exports and matching PDB GUID {evidence['codeview_pdb_guid']}, age {evidence['pdb_age']}.

The new bridge preserves a verified pilot's working local Z only at the engine's conditional reset. Untracked calls and failed checks replay the original instructions, with the CALL stack offset accounted for. Integration and displacement tolerance are unchanged. Actual gravity/drag success must be established from the user's next log.

INSTALL-3C5-plan.json preserves prior hashes; INSTALL-3C5-result.json records the actual transaction. Do not regenerate packaging preimages after installation.
'''
(PACKET/'INSTALL-3C5.md').write_text(receipt,encoding='utf-8')
for name in ('INSTALL-3C5.md','INSTALL-3C5-plan.json','INSTALL-3C5-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
for relative in ('START-HERE.html','README.md','BUILD-RESULT.md','Installation/INSTALL-3C5.md'):
    assert (RELEASE/relative).is_file()
archive=ROOT/'release/NVO-Combat-Packet-3C5-Compiled.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file(): z.write(p,p.relative_to(RELEASE).as_posix())
zip_hash=digest(archive)
checkpoint=f'''## Current combat checkpoint: 3C5 / 310 installed; guarded local-Z correction awaits test

2026-09-15: user approved the controller correction. Packet 3C5 adds a six-byte CALL+NOP at C73517 (original FLDZ/FSTP [ESP+58]) inside the concrete C73170 controller identified by the accepted 309 diagnostic. PreserveLocalZ verifies pending private identity/thread/controller/request, C73170 incoming frame and parent generic frame, owned virtual return 92FFEF, pre-patch ESP = align_down(inner EBP,16)-B0, local vector pointer at ESP+48, XYZ at ESP+50, exact vtable/target, timestep/rotation, collision-free identity and byte-identical submitted/request/working XYZ. Only verified applied pilot vectors skip the reset; baseline and unsupported calls replay it. This independently observes the actual reset branch. LocalZBridge saves/restores GP/EFLAGS/x87/SSE/MXCSR along both exits; fallback FSTP [ESP+5C] accounts for CALL's extra four bytes. No new direct controller/request/object/damage writes or engine calls. Details source/combat/step3c5/IMPLEMENTATION.md.

Eight spans/four pages retain exact transactional patch normalization/rollback. New 2048-byte C73170 prefix fingerprint 0193951146A4412C matches 309 archived SHA20a927ae6742fc61e6cdf8f0a52c945051a7a33cf743c1aa7c7a151627e0beac. Prefix only, not full function. Raw target byte capture removed after identification. Unchanged baseline must visit the reset and match movement before future input writes; unchanged RK4 and actual-displacement tolerance. PHYSICS_LOCAL_Z and reset_entries/reset_preserved counters distinguish branch execution from physical acceptance. A failure stops subsequent edits, not the already-submitted segment. Damage authority still disabled; only two private combinations. No new console notices or dependencies. Separate BALLISTX-main library not incorporated.

Built {manifest['build_output']}; zero warnings/errors; static assembly inspected, PE32 x86, two exports, matching PDB GUID {evidence['codeview_pdb_guid']} age {evidence['pdb_age']}. DLL SHA {evidence['dll_sha256']}; PDB SHA {evidence['pdb_sha256']}. CurrentHit/NativeObserver/DamageEvents/FlightPreview/FlightTiming/NativeLog source-identical to 309. Installed only DLL/PDB, {result['protected_files_verified']} protected entries unchanged. {closed} No assistant game launch/GECK/gameplay/DLL execution/process-memory capture. Backup {backup}. Receipt source/combat/step3c5/INSTALL-3C5.md and immutable plan/result JSON. ZIP SHA {zip_hash}. No packaging regeneration after install.

Next user check: prepared save, wait three seconds, one private NVO Flight Hunting Rifle and one private NVO Flight 9mm shot with private ammo at the same distant solid scenery outside VATS, pause, exit/report done. God mode fine. No extra reload/stress/video/GECK. Read/archive game-root NVOCombatCore.log directly before another launch. Require PHYSICS_LOCAL_Z baseline preserve=0 and applied preserve=1 on observed reset branches; PHYSICS_ACTUAL matched=1 for both baselines and multiple applied segments; nonzero applied_verified and no mismatches/guard/unpaired faults; original impact/destruction route. Merely armed or preserved is not acceptance. Physics still pending; do not advance to broader projectile coverage/armour. Ask before another packet. Xhigh sufficient, no settings changed.

'''
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    data=p.read_bytes()
    if checkpoint.splitlines()[0].encode() not in data:
        first,sep,rest=data.partition(b'\n')
        p.write_bytes(first+sep+b'\n'+checkpoint.encode()+rest)
print(json.dumps(dict(receipt=str(PACKET/'INSTALL-3C5.md'),zip_sha256=zip_hash,zip_bytes=archive.stat().st_size,installed_version=310),indent=2))

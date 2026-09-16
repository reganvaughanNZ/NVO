"""Write the actual install receipt and archive it without regenerating preimages."""
from pathlib import Path
import hashlib, json, shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'source/combat/step3c4'
RELEASE=ROOT/'release/NVO-Combat-Packet-3C4-Compiled'
result=json.loads((PACKET/'INSTALL-3C4-result.json').read_text(encoding='utf-8-sig'))
assert result['status']=='installed' and result['version']==309
plan=json.loads((PACKET/'INSTALL-3C4-plan.json').read_text())
assert len(result['installed'])==2
for row in result['installed']:
    p=Path(plan['game_root'])/row['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    assert hashlib.sha256((RELEASE/row['path']).read_bytes()).hexdigest()==row['sha256']
backup=Path(result['backup'])
before=json.loads((backup/'before.json').read_text(encoding='utf-8-sig'))
for row in before['before']:
    assert hashlib.sha256((backup/'originals'/row['path']).read_bytes()).hexdigest()==row['sha256']
receipt=f'''# Packet 3C4 installation receipt

Installed NVOCombatCore 0.3.9 / 309. The two installed files match the compiled release and debug pair. {result['protected_files_verified']} protected entries were verified unchanged, including the ESM, pilot ESP, INIs, activation and other extenders.

The game was already closed. No game launch, gameplay, GECK work, load-order or configuration edit occurred. Runtime diagnostic acceptance remains pending.

Backup: `{backup}`

With the game closed, reversal restores these matching version 308 files from the backup's `originals/Data/NVSE/Plugins` directory to the same relative directory in the game folder:

- NVOCombatCore.dll
- NVOCombatCore.pdb

Installed DLL SHA256: {result['installed'][0]['sha256']}

Installed PDB SHA256: {result['installed'][1]['sha256']}

Build: native/NVOCombatCore/out/build-9235-26601. Zero warnings/errors, PE32 x86, two NVSE exports and matching PDB GUID 98b76d7c-6923-4ffa-acec-752bb4e592a7, age 1. Static bridge review confirms the virtual load/call wrapper preserves the original target and argument cleanup; request observations add no controller or position writes.

See INSTALL-3C4-plan.json for immutable prior hashes and INSTALL-3C4-result.json for actual transaction output. Do not rerun packaging to rewrite preimages after installation.
'''
(PACKET/'INSTALL-3C4.md').write_text(receipt,encoding='utf-8')
for name in ('INSTALL-3C4.md','INSTALL-3C4-plan.json','INSTALL-3C4-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
archive=ROOT/'release/NVO-Combat-Packet-3C4-Compiled.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file(): z.write(p,p.relative_to(RELEASE).as_posix())
zip_hash=hashlib.sha256(archive.read_bytes()).hexdigest()
checkpoint=f'''## Current combat checkpoint: 3C4 / 309 installed; controller request test pending

2026-09-15: user authorized the next packet after the accepted 308 diagnostic checkpoint. Prepared 3C4 to identify the concrete controller target and request entry/return before attempting a correction. New read-only observations at 0092FFEA (8-byte virtual load/call), 0092FFD4 (alternate direct call), 0092FFFB (post-return flag query). Request generic EBP-208, saved argument frame EBX, exact pending private owner/input/thread/controller pairing. Existing movement input write, integrator, baseline and mismatch tolerance retained. At most two executable game-image target byte captures of 2048 bytes per process in the diagnostic log. No controller/request/object/damage writes. No new console notices or dependencies. Gravity/drag remains unaccepted; the same mismatch may recur. Details source/combat/step3c4/IMPLEMENTATION.md.

Built native/NVOCombatCore/out/build-9235-26601, zero warnings/errors, PE32 x86, correct exports, matching PDB. DLL SHA256 8b2765db4ee25950a127f356d07193467fe8dabc5535f112e7c02c88761c801d. Seven original spans in three protected pages, variable-length exact normalization and rollback. Static assembly inspected all seven bridges. Six hit/observer/timing/preview/log modules source-identical to 308. No assistant native execution/gameplay/GECK/memory capture. Installed only DLL/PDB, 52 protected entries unchanged. Game already closed; no termination or relaunch. Backup {backup}. Plan/result/receipt under source/combat/step3c4/INSTALL-3C4*. Compiled ZIP SHA256 {zip_hash}.

Next user check: prepared save, wait three seconds, one private NVO Hunting Rifle and one private NVO 9mm shot with their private ammo at the same distant solid scenery outside VATS, pause between shots, exit and report done. God mode fine; no extra reload/stress/video/GECK required. Read and archive game-root NVOCombatCore.log before relaunch. Review PHYSICS_CONTROLLER request rotations/input and virtual_enter/direct_enter/return, PHYSICS_CONTROLLER_ARGUMENT, code begin/chunks/end hashes, PHYSICS_BOUNDARY and PHYSICS_ACTUAL. Missing entry rows do not prove this branch executed; do not patch a guessed target. Keep existing collision route and strict verification. Ask before another packet. Console-spam cleanup remains pending an exact repeated message. Xhigh appropriate, settings unchanged.

'''
for path in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    data=path.read_bytes()
    if checkpoint.splitlines()[0].encode() not in data:
        # Preserve historical mixed-encoding bytes while inserting at the top.
        first,sep,rest=data.partition(b'\n')
        path.write_bytes(first+sep+b'\n'+checkpoint.encode('utf-8')+rest)
print(json.dumps(dict(receipt=str(PACKET/'INSTALL-3C4.md'),zip_sha256=zip_hash,zip_bytes=archive.stat().st_size),indent=2))

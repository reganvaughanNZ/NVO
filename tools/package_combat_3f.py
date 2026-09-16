"""Package the prepared 3F update and derive its bounded installer. Workspace only."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'source/combat/step3f'
RELEASE = ROOT/'release/NVO-Combat-Packet-3F-Update'
PRIOR = ROOT/'release/NVO-Combat-Packet-3E-Update'
assert not (PACKET/'INSTALL-3F-result.json').exists(), 'Do not overwrite an installed transaction.'
plan_hash = hashlib.sha256((PACKET/'INSTALL-3F-plan.json').read_bytes()).hexdigest()
installer = (ROOT/'tools/install_combat_3e.ps1').read_text(encoding='utf-8-sig').replace('3E','3F').replace('step3e','step3f')
anchor = '$nvoPlan = Get-Content -LiteralPath $nvoPlanPath -Raw | ConvertFrom-Json'
assert installer.count(anchor) == 1
installer = installer.replace(anchor, f"if ((Get-FileHash -LiteralPath $nvoPlanPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne '{plan_hash}') {{ throw 'Prepared plan changed.' }}\n"+anchor)
anchor = '# Validate the exact allowlist and release bytes before touching the running game.'
installer = installer.replace(anchor, "if (@(Get-Process GECK,Vortex -ErrorAction SilentlyContinue).Count) { throw 'Close GECK and Vortex before installing this packet.' }\n\n"+anchor)
installer = installer.replace("if (@(Running-Game).Count) { throw 'Game relaunched before installation.' }",
    "if (@(Get-Process FalloutNV,GECK,Vortex -ErrorAction SilentlyContinue).Count) { throw 'Game, GECK or Vortex opened before installation.' }")
(ROOT/'tools/install_combat_3f.ps1').write_text(installer, encoding='utf-8')
for folder in ('Installation','Source/tools','Source/baseline-3E'):
    (RELEASE/folder).mkdir(parents=True,exist_ok=True)
for name in ('README.md','START-HERE.html'):
    shutil.copyfile(PACKET/name,RELEASE/name)
for name in ('IMPLEMENTATION.md','RECORD-AUDIT.json','STATIC-CHECKS.json','INSTALL-3F-plan.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
for name in ('CREDITS-BALLISTX.md','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt'):
    shutil.copyfile(PRIOR/name,RELEASE/name)
for name in ('NVOFlightPilot.esp','NVOFlightPreview.ini','RECORD-AUDIT.json','INSTALL-3E-result.json','CHECKPOINT-ACCEPTED.md'):
    shutil.copyfile(ROOT/'source/combat/step3e'/name,RELEASE/'Source/baseline-3E'/name)
for name in ('prepare_combat_3f.py','package_combat_3f.py','install_combat_3f.ps1','finalize_combat_3f.py','prepare_combat_3b2.py','inspect_plugin.py'):
    shutil.copyfile(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
shutil.copyfile(ROOT/'tools/install_combat_3f.ps1',RELEASE/'Installation/install_combat_3f.ps1')
with (RELEASE/'THIRD-PARTY-NOTICES.md').open('a',encoding='utf-8') as f:
    f.write('\n\nPacket 3F: two explicit stock .308 AP/HP mappings reuse the accepted standard .308 BallistX tuning only for the identity checkpoint. No donor ammunition conversion scripts or new native code are installed. Native build311 and its existing notices remain applicable. Local JIP GameForms.h is a read-only layout/enum reference, recorded by path and hash in RECORD-AUDIT.json.\n')
manifest = json.loads((RELEASE/'manifest.json').read_text())
manifest['installer_plan_sha256'] = plan_hash
manifest['test_steps'] = 'standard -> AP -> HP -> standard; save with HP, load once, HP VATS at live target'
manifest['tuning_scope'] = 'Shared accepted standard .308 tuning for identity checkpoint; not variant calibration.'
(RELEASE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(packet='3F',plan_sha256=plan_hash,release=str(RELEASE)),indent=2))

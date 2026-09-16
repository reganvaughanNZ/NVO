import hashlib
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
step = root / 'source/combat/step4b/stress'
release = root / 'release/NVO-Combat-Packet-4B-Stress-Check'
result = json.loads((step / 'INSTALL-result.json').read_text(encoding='utf-8-sig'))
assert result['status'] == 'installed' and result['native_unchanged']
page = step / 'START-HERE.html'
page.write_text(page.read_text(encoding='utf-8').replace('After 64 accepted attempts', 'After 64 snapshot attempts'), encoding='utf-8')
for name in ['START-HERE.html','README.md','INSTALL-plan.json','INSTALL-result.json','ITEM-PROVENANCE.json']:
    shutil.copy2(step / name, release / name)
manifest = dict(packet='4B-stress', native_version=326, status='Helpers installed; user test pending',
    native_changed=False, damage_replacement=False, distinct_misc_forms=128, expected_shots='About90 before reload; about5 after',
    inventory_limit_unchanged=512, snapshot_limit_unchanged=64, gameplay_tested=False,
    files=[dict(path=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
           for p in sorted(release.iterdir()) if p.is_file() and p.name != 'manifest.json'])
for base in (step, release):
    (base / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
status = root / 'STATUS.md'
old = status.read_bytes()
heading = '''\n## Current checkpoint: Packet 4B stress helpers INSTALLED; user test pending

User approved automatic-fire/enlarged-inventory checkpoint. Native326 and12 existing foundation/helper files hash-verified unchanged; only root-level NVOStressKit4B.txt and NVOStressTarget4B.txt added. No process actions, DLL/ESM/config/load-order changes or damage enablement.128 explicitly selected unscripted nonquest base-game MISC forms exercise distinct inventory entries. Target gets full Combat Armor/Helmet and100,000 health only when user runs the selected-target BAT. Player kit gives9mm SMG+300 standard rounds.

USER TEST: disposable test save, living humanoid, AI-disabled usual setup. Run both helpers, save NVO4BStress separately, empty three30-round SMG magazines into torso, reload setup once, fire about5 rounds, quit normally and report smoothness/hitches. God mode off for meaningful magazine count. Expect >64 qualifying Character hits, enlarged traversal counts,64 snapshot attempts then intentional omitted_after_limit, and fresh snapshots after reload. Omissions beyond logging limits are not errors. No per-scan timing exists; do not infer precise overhead or always-on readiness. No more creature test required.

Page release/NVO-Combat-Packet-4B-Stress-Check/START-HERE.html. Evidence/install source/combat/step4b/stress. Await user result; capture game-root NVOCombatCore.log and review before next approval. No4C/damage promotion.

'''
if heading.encode() not in old:
    cut = old.index(b'\n') + 1
    status.write_bytes(old[:cut] + heading.encode() + old[cut:])
print(json.dumps(dict(page=str(release / 'START-HERE.html'), files=len(manifest['files']), helpers_installed=2, native_changed=False)))

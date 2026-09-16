"""Package 3L's existing evidence. No game, plugin, configuration or native writes."""
from pathlib import Path
import base64
import hashlib
import json
import math
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3l'
CAPTURE = PACKET / 'runtime-20260916-124233'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = read_json(CAPTURE / 'manifest.json')
for f in manifest['files']:
    path = CAPTURE / f['filename']
    assert path.parent == CAPTURE and path.stat().st_size == f['bytes']
    assert sha(path) == f['sha256']
settings = {int(s['address'], 16): s for s in manifest['settings']}
tables = struct.unpack('<10I', (CAPTURE / 'difficulty_setting_tables-0119B310.bin').read_bytes())
rows = []
for index, suffix in enumerate(('VE', 'E', 'N', 'H', 'VH')):
    row = {'index': index, 'suffix': suffix}
    for offset, receiver, name in ((0, 'player', 'ToPC'), (5, 'non_player', 'ByPC')):
        address = tables[index + offset]
        s = settings[address]
        assert s['actual_name'] == f'fDiffMultHP{name}{suffix}'
        raw = struct.unpack_from('<f', base64.b64decode(s['object_bytes']), 4)[0]
        assert math.isfinite(raw) and abs(raw - s['value']) < 1e-6
        row[receiver] = {'name': s['name'], 'address': s['address'], 'value': raw}
    rows.append(row)
assert manifest['cached_difficulty']['value'] == 0
assert settings[0x11E0940]['value'] == 0
assert rows[0]['non_player']['value'] == 2 and rows[0]['player']['value'] == 0.5

baseline = read_json(ROOT / 'backups/combat-install-3K1-20260916-122305-96aa1f5d/before.json')
verified = []
for f in baseline['protected']:
    actual = sha(Path(f['path']))
    assert actual == f['sha256'], f'Protected file differs: {f["path"]}'
    verified.append({'path': f['path'], 'sha256': actual})
installed = read_json(ROOT / 'source/combat/step3k1/INSTALL-3K1-result.json')
for f in installed['installed']:
    path = GAME / f['path']
    actual = sha(path)
    assert actual == f['sha256']
    verified.append({'path': str(path), 'sha256': actual})
assert not (GAME / 'Data/RD.esm').exists()

result = {
    'packet': '3L', 'status': 'prepared_read_only_audit', 'native_version_unchanged': 320,
    'canonical_capture': str(CAPTURE.relative_to(ROOT)),
    'current_difficulty_index': 0, 'current_setting_suffix': 'VE', 'tables': rows,
    'traced_health_request_return_address': '0089D82D',
    'historical_factor2_explanation': 'supported inference from current loaded code/settings and prior hit arithmetic; not historical hit-time setting capture',
    'health_formula_overrides_preserved': 5,
    'damage_replacement': False, 'pre_damage_gate': 'HOLD',
    'source_build_game_data_changes': False, 'gameplay_test_required_for_this_packet': False,
    'difficulty_replacement': 'proposal only; ten GMSTs and difficulty selection remain unchanged',
    'next_proposed': '3M disabled armour input and damage-handoff contract; ask first',
    'protected_plus_native_files_verified': len(verified), 'verified_files': verified,
    'inspection_session': read_json(PACKET / 'main-menu-inspection/SESSION.json'),
}
assert result['inspection_session']['closed'] and result['inspection_session']['startup_banner_submissions'] == 1
(PACKET / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')

page = '''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NVO · Packet 3L — Damage scaling</title>
<style>body{margin:48px auto;padding:0 24px;max-width:860px;background:#101b18;color:#e2e8de;font:18px/1.65 system-ui}h1{font-size:34px}h2{font-size:23px;color:#d3e2ab}a{color:#c8e8b3}strong{color:#eff5d9}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:10px;border-bottom:1px solid #46564c}.note{border-left:3px solid #acc286;padding:12px 20px;background:#172720}small{color:#b7c3b7}</style>
<p><small>NVO COMBAT · PACKET 3L · READ-ONLY AUDIT</small></p>
<h1>The existing ×2 scaling is accounted for</h1>
<p>The current loaded difficulty is <strong>Very Easy</strong>: health damage uses <strong>×2 against non-player targets</strong> and <strong>×0.5 against the player</strong>. The engine applies it before the health request we log.</p>
<table><tr><th>Completed test</th><th>Earlier hit value</th><th>Health lost</th></tr><tr><td>Hunting rifle</td><td>29.5 × 2</td><td>59</td></tr><tr><td>Punch after reload</td><td>0.45 × 2</td><td>0.90</td></tr></table>
<p>This matches your completed test. The historical test did not capture difficulty at hit time; its cause is inferred from the matching current settings, code and arithmetic.</p>
<div class="note"><strong>No installation, GECK work or repeat test.</strong> Native320 and the once-per-launch NVO banner remain installed. Your health settings, difficulty and flight configuration are unchanged. Damage replacement stays off.</div>
<h2>Your difficulty proposal</h2>
<p>We can make the ten health-damage multipliers 1.0 and use difficulty for NVO presets instead: supplies, believable enemy reactions/accuracy, and recovery/treatment forgiveness. Penetration and anatomical vulnerability would remain consistent. This is a proposal; no settings have been changed.</p>
<h2>Next, with your approval</h2>
<p><strong>3M: the disabled armour model’s inputs and damage handoff.</strong> Define ammunition mass and units, reliable impact information, unsupported-hit handling, and which system owns each modifier. Include difficulty and the Brahmin Baron extra damage path before enabling any replacement.</p>
<p><a href="README.md">Full packet notes</a> · <a href="ENGINE-TRACE.md">Engine evidence</a> · <a href="RESULT.json">Verification receipt</a></p>
<p><small>Reversal: none required. This packet only adds workspace evidence and notes. Do not install the captured binary/object files. The inspection game was closed without loading a save.</small></p></html>
'''
(PACKET / 'START-HERE.html').write_text(page, encoding='utf-8')
release = ROOT / 'release/NVO-Combat-Packet-3L-Scaling-Audit'
release.mkdir(exist_ok=True)
for name in ('README.md', 'ENGINE-TRACE.md', 'RESULT.json', 'START-HERE.html'):
    shutil.copy2(PACKET / name, release / name)
release_manifest = {'packet': '3L', 'install_files': [], 'files': [
    {'name': name, 'sha256': sha(release / name)} for name in ('README.md', 'ENGINE-TRACE.md', 'RESULT.json', 'START-HERE.html')]}
(release / 'MANIFEST.json').write_text(json.dumps(release_manifest, indent=2) + '\n', encoding='utf-8')

status = '''
## Current checkpoint: Packet 3L scaling audit prepared; native320 unchanged

2026-09-16: user approved 3L and raised Game Settings/difficulty. Read-only main-menu capture runtime-20260916-124233 verifies current INI iDifficulty0 AND PlayerCharacter cached gameDifficulty0. Engine0089D6F0 ->008808A0 ->00648CB0 multiplies Health by the current receiver-based difficulty table before the observed DamageActorValue call (return0089D82D). Tables/pointers/named values independently checked: index0(non-player2.0,player0.5), index2 both1.0. This matches prior3K rifle29.5->59 and punch0.45->0.9. Historical hit-time settings were NOT captured; describe old cause as a supported inference, current mechanism as verified. Do not blindly divide engine results by2 or assume ByPC names imply source-player filtering. All five NVO health GMSTs match runtime. fDifficultyDamageMultiplier10 is not read by this bounded helper; do not change it by name alone.

Packet is evidence/documentation only: source/combat/step3l and release/NVO-Combat-Packet-3L-Scaling-Audit. No DLL/source gameplay edits/build/install or GECK work; no new gameplay retest. Fifty-two protected plus two native files hash-match3K1; RD absent. Native320/banner retained, damage replacementOFF. Assistant's main-menu inspection PID4592 closed after archive; no save/gameplay loaded. The live game log now contains this inspection, while completed gameplay evidence remains archived understep3k/captures/reload-1930643b54d3. First close guard safely stopped on PowerShell JSON DateTime/string comparison; exact timestamp tick comparison passed, no unexpected process change.

User proposed repurposing difficulty. Recorded PROPOSAL ONLY: ten fDiffMultHPByPC/ToPC GMSTs1.0; selected difficulty supplies NVO presets for resources, restrained AI, recovery/treatment. Preserve coherent penetration/anatomy, powerful familiar medicines, no save restrictions. No settings changed or feature implemented. Neutralizing these ten is not proof all difficulty/VATS effects disappear.

NEXT PROPOSED3M: disabled armour-model input and damage-handoff contract (units/mass/provenance, trusted contact, admission/fallback, scaling/ownership incldifficulty andBrahminBaron). ASK before preparing. Overallpre-damageHOLD remains; reuseUltra317 andFOLLOWUP-3L rather than rerunfullreview/oldstress. Need targeted evidence before damageauthority. Packet3L's bounded scaling inquiry is complete; universalpathclaims remain unsupported.

'''
for rel in ('STATUS.md', 'source/combat/README.md'):
    path = ROOT / rel
    original = path.read_bytes()
    marker = b'## Current checkpoint: Packet 3L scaling audit prepared; native320 unchanged'
    if marker not in original:
        end = original.index(b'\n') + 1
        path.write_bytes(original[:end] + status.replace('\n', '\r\n').encode('utf-8') + original[end:])
print(json.dumps({'release': str(release), 'verified_files': len(verified), 'difficulty_index': 0,
                  'game_closed': result['inspection_session']['closed'], 'damage_replacement': False}))

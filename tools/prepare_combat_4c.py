"""Verify and package the offline Step4C classifier. Never writes game files."""
import hashlib
import json
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'source/combat/step4c'
MODEL = ROOT / 'native/NVOCombatModel'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4C-Coverage-Profiles'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p, obj): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
def copy(src, dst): dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src,dst)
def row(p, base=ROOT): return dict(path=p.relative_to(base).as_posix(),bytes=p.stat().st_size,sha256=sha(p))

core = load(ROOT / 'source/combat/step4b/SOURCE-SNAPSHOT.json')
for r in core['files']: assert sha(ROOT/'native/NVOCombatCore'/r['path']) == r['sha256'], r['path']
prior = load(ROOT/'source/combat/step4a/SOURCE-SNAPSHOT.json')
for r in prior['model_source']: assert sha(ROOT/r['path']) == r['sha256'], r['path']
plan = load(ROOT/'source/combat/step4b/stress/INSTALL-plan.json')
game = Path(plan['game_root'])
pins = dict(plan['protected']); pins.update({r['path']:r['sha256'] for r in plan['files']})
for name,digest in pins.items(): assert sha(game/name)==digest, name
assert not (game/'Data/RD.esm').exists()

results = (MODEL/'out-coverage/results.txt').read_text()
assert 'PASS 53 checks; 76 captured snapshots; 10000 deterministic repetitions' in results
assert 'FAIL' not in results
profile_results = (STEP/'PROFILE-CHECKS.txt').read_text(encoding='utf-8-sig')
assert 'PASS 21 profile-authoring checks' in profile_results
build_log = (MODEL/'out-coverage/build.log').read_text()
assert not re.search(r'\b(warning|error) [A-Z]+\d+',build_log)
exe = MODEL/'out-coverage/coverage_checks.exe'
pe=exe.read_bytes(); offset=struct.unpack_from('<I',pe,0x3C)[0]
assert pe[offset:offset+4]==b'PE\0\0' and struct.unpack_from('<H',pe,offset+4)[0]==0x14c
module=(MODEL/'CoverageProfiles.hpp').read_text()+(MODEL/'CoverageProfiles.cpp').read_text()
for token in ['Windows.h','NVSE','WriteProcessMemory','VirtualProtect','ArmourModel.hpp','ShadowAdapter.hpp','NativeLog','fopen(', 'ofstream']:
    # The header comment says "NVSE" only in a negative description? No interface may be present.
    assert token not in module, token
checks=dict(packet='4C',status='Prepared offline; no runtime installation',x86_checks=53,
    profile_authoring_checks=21,replayed_captured_snapshots=76,deterministic_repetitions=10000,
    native_core_files_unchanged=len(core['files']),prior_model_source_files_unchanged=len(prior['model_source']),
    installed_files_unchanged=len(pins),compiled_target='PE32 x86 /W4 /WX',
    runtime_integrated=False,damage_replacement=False,authority_promoted=False,
    asset_geometry_validated=False,authored_profiles=2,profile_semantics='Provisional coarse-region candidate extents only',
    gameplay_test_required=False,new_game_files=0,checker=row(exe))
save(STEP/'CHECKS.json',checks)
save(STEP/'manifest.json',dict(packet='4C',scope='Offline explicit coverage classifier',status='Prepared; verified',
    native_version_preserved=326,damage_replacement=False,installed=False,gameplay_test_required=False,
    authored_profiles=2,profile_data='profiles/armour-coverage.json',runtime_config_loader=False))
sources=[MODEL/n for n in ['CoverageProfiles.hpp','CoverageProfiles.cpp','CoverageFixtures.inl','coverage_tests.cpp','run_coverage_checks.cmd']]
tools=[ROOT/'tools'/n for n in ['generate_combat_4c_fixtures.py','check_combat_4c_profiles.py','prepare_combat_4c.py']]
save(STEP/'SOURCE-SNAPSHOT.json',dict(packet='4C',files=[row(p) for p in sources+tools+[STEP/'profiles/armour-coverage.json']]))
(STEP/'BUILD-RESULT.md').write_text('''# Step4C verification

Standalone PE32 x86 checker compiled with MSVC C++17, /W4 /WX and static runtime.53 focused C++ checks,21 strict authoring checks,76 captured-snapshot replays and10,000 deterministic repetitions passed. No DLL build or game installation occurred. Existing native and pure-model sources match their pinned baselines. See CHECKS.json for counts and SOURCE-SNAPSHOT.json for new source hashes.

Rebuild from the working project (or packaged Source tree): run the Python generator tools/generate_combat_4c_fixtures.py, then native/NVOCombatModel/run_coverage_checks.cmd. Run tools/check_combat_4c_profiles.py for authoring validation. The CMD uses the installed Visual Studio18 Community x86 environment. Generated fixtures contain only known captured base-game armour identities; they are not a general runtime FormID resolver.
''',encoding='utf-8')
for name in ['README.md','CONTRACT.md','START-HERE.html','BUILD-RESULT.md','CHECKS.json','manifest.json','SOURCE-SNAPSHOT.json','REPLAY-INPUTS.json','PROFILE-CHECKS.txt','profiles/armour-coverage.json']:
    copy(STEP/name,RELEASE/name)
for p in sources+tools: copy(p,RELEASE/'Source'/p.relative_to(ROOT))
copy(STEP/'profiles/armour-coverage.json',RELEASE/'Source/source/combat/step4c/profiles/armour-coverage.json')
for path,expected in load(STEP/'REPLAY-INPUTS.json')['captures'].items():
    assert sha(ROOT/path)==expected
    copy(ROOT/path,RELEASE/'Source'/path)
for name in ['results.txt','build.log','toolchain.log','coverage_checks.exe']:
    copy(MODEL/'out-coverage'/name,RELEASE/'Evidence'/name)
package=[row(p,RELEASE) for p in sorted(RELEASE.rglob('*')) if p.is_file() and p.name!='PACKAGE-SNAPSHOT.json']
save(RELEASE/'PACKAGE-SNAPSHOT.json',dict(files=package))
archive=Path(shutil.make_archive(str(RELEASE),'zip',RELEASE.parent,RELEASE.name))
with zipfile.ZipFile(archive) as z:
    for r in package: assert hashlib.sha256(z.read(RELEASE.name+'/'+r['path'])).hexdigest()==r['sha256']
save(STEP/'DELIVERY-VERIFICATION.json',dict(package_files=len(package),archive_sha256=sha(archive),checks=checks))
status=ROOT/'STATUS.md'; old=status.read_bytes()
heading='''\n## Current checkpoint: Packet 4C offline explicit coverage classifier PREPARED

User approved defining regional armour coverage. New pure CoverageProfiles module plus strict editable JSON authoring maps exact owning-plugin/localID keys to six explicit None/Partial/Full/Unknown extents. Seed Combat Armor declares partial torso/arms/legs and no head; Combat Helmet partial head only. These are provisional NVO authoring, not measured mesh coverage, material strength or actual-strike proof. Creature input returns creature_profile_required; empty equipped inventory never verifies bare anatomy. Unknown equipment/origin, record-mask drift, incomplete/unstable snapshots or invalid/duplicate inputs reject all rows. Slot masks and traversal order never generate anatomical coverage or layer order.

53 x86 /W4 /WX classifier checks,21 malformed-authoring checks,76 recorded4B snapshot replays and10,000 deterministic repetitions pass. NativeCore and prior4A sources remain pinned;14 installed files unchanged; RD absent. No DLL/game/GECK/config update or new playtest needed. All authority and damage remain HOLD; no ShadowAdapter/ArmourModel linkage. Source/evidence source/combat/step4c; release/NVO-Combat-Packet-4C-Coverage-Profiles.

NEXT ask before4D live exact-origin resolution and coverage classification diagnostics. Keep partial/unknown extents unresolved; no damage enablement. Authoritative contact speed, hit surfaces, material/target profiles, coherent at-impact evidence, layer order and modifier ownership remain separate gates. Original current4B stress success was bounded and did not measure per-scan timing.

'''
if heading.encode() not in old:
    cut=old.index(b'\n')+1; status.write_bytes(old[:cut]+heading.encode()+old[cut:])
print(json.dumps(dict(**checks,package_files=len(package),archive_sha256=sha(archive))))

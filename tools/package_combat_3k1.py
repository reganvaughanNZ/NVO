"""Package a banner-only native update, reusing the verified 319 foundation."""
from pathlib import Path
import argparse,inspect,json,difflib,re
import package_combat_3b3a as pair
from package_combat_3h import sha,js,copy
ROOT=Path(__file__).resolve().parents[1];NATIVE=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3k1';RELEASE=ROOT/'release/NVO-Combat-Packet-3K1-Compiled'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
ap=argparse.ArgumentParser();ap.add_argument('--build',required=True);a=ap.parse_args()
assert not (PACKET/'INSTALL-3K1-result.json').exists()
build=(NATIVE/'out'/a.build).resolve();assert build.parent==NATIVE/'out'
baseline=PACKET/'baseline-319';frozen=json.loads((baseline/'manifest.json').read_text())
allowed={'src/Plugin.cpp','include/NvseBootstrapApi.hpp','CMakeLists.txt'};unchanged=[];diffs=[]
for f in frozen['files']:
    old=baseline/f['path'];new=NATIVE/f['path'];assert sha(old)==f['sha256']
    if f['path'] not in allowed:assert sha(new)==f['sha256'];unchanged.append(f['path'])
    if old.read_bytes()!=new.read_bytes():diffs.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='native319/'+f['path'],tofile='native320/'+f['path']))
(PACKET/'SOURCE-DIFF.txt').write_text(''.join(diffs))
scope=vars(pair).copy();exec(inspect.getsource(pair.inspect_pair).replace('0.3.4 | phase=3B3A','0.3.20 | phase=3K1'),scope)
evidence=scope['inspect_pair'](build)
plugin=(NATIVE/'src/Plugin.cpp').read_text()
assert plugin.count('gStartupBannerAttempted = false')==1 and plugin.count('gStartupBannerAttempted = true')==1
assert plugin.count('RunScriptLine("PrintC')==1 and 'EmitStartupBanner();' in plugin
evidence.update(packet='3K1',native_version=320,unchanged_sources=unchanged,
    combat_observer_and_flight_sources_identical_to_319=True,
    prior_live_checkpoint='source/combat/step3k/CHECKPOINT-RESULT.json',new_combat_test_required=False,
    message='NVO [0.3.20] - The Mojave is yours.',once_guard='process-static, set before public console API call; no lifecycle reset',
    api_provenance='Local xNVSE Hooks_Gameplay.cpp HandleMainLoopHook and GameScript.cpp RunScriptLine; JIP patches_game.h DeferredInit',
    damage_replacement=False,gameplay_tested=False)
js(PACKET/'STATIC-CHECKS.json',evidence)
prior=json.loads((ROOT/'source/combat/step3k/INSTALL-3K-plan.json').read_text())
installed=json.loads((ROOT/'source/combat/step3k/INSTALL-3K-result.json').read_text(encoding='utf-8-sig'));assert installed['status']=='installed'
deps={r['path']:r['sha256'] for r in prior['dependency_preconditions']};deps.update({r['path']:r['sha256'] for r in installed['installed']})
for p,h in deps.items():assert sha(GAME/p)==h,p
assert not (GAME/'Data/RD.esm').exists()
plan=dict(prior,packet='3K1',version=320,files=[],dependency_preconditions=[dict(path=p,sha256=h) for p,h in deps.items()])
for name in ('NVOCombatCore.dll','NVOCombatCore.pdb'):
    relative='Data/NVSE/Plugins/'+name;target=RELEASE/relative;copy(build/name,target)
    plan['files'].append(dict(path=relative,action='install',sha256=sha(GAME/relative),source=str(target),source_sha256=sha(target),log_may_change_until_game_exits=False))
js(PACKET/'INSTALL-3K1-plan.json',plan);pin=sha(PACKET/'INSTALL-3K1-plan.json')
installer=(ROOT/'tools/install_combat_3k.ps1').read_text().replace('3K','3K1').replace('step3k','step3k1').replace('version -ne 319','version -ne 320').replace('version=319','version=320')
installer=re.sub(r"-ne '[0-9a-f]{64}'","-ne '"+pin+"'",installer,count=1)
(ROOT/'tools/install_combat_3k1.ps1').write_text(installer)
manifest=dict(packet='3K1',version='0.3.20',plugin_version=320,status='Compiled; installation pending',
    installed_by_assistant=False,gameplay_tested=False,damage_replacement=False,change='Once-per-process console banner only',
    build_output=str(build.relative_to(NATIVE)),installed_files=[dict(path=r['path'],sha256=r['source_sha256']) for r in plan['files']])
(NATIVE/'BUILD-RESULT.md').write_text(f'# Native320 / Packet3K1\n\nBanner-only update, Win32, zero compiler warnings/errors, matching DLL/PDB. Combat/flight sources unchanged from tested319. No repeat combat suite.\n\nDLL SHA256 {evidence["dll_sha256"]}\n\nPDB SHA256 {evidence["pdb_sha256"]}\n')
for n in ('README.md','START-HERE.html'):copy(PACKET/n,RELEASE/n);copy(PACKET/n,NATIVE/n)
js(RELEASE/'manifest.json',manifest);js(NATIVE/'manifest.json',manifest)
for n in ('STATIC-CHECKS.json','SOURCE-DIFF.txt','INSTALL-3K1-plan.json'):copy(PACKET/n,RELEASE/'Installation'/n)
copy(ROOT/'source/combat/step3k/CHECKPOINT-RESULT.json',RELEASE/'Installation/3K-CHECKPOINT-RESULT.json')
copy(ROOT/'tools/install_combat_3k1.ps1',RELEASE/'Installation/install_combat_3k1.ps1')
sources=[NATIVE/n for n in ('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','manifest.json','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md')]
for folder in ('src','include','config','reference'):sources.extend(p for p in (NATIVE/folder).glob('*') if p.is_file())
for p in sources:copy(p,RELEASE/'Source/NVOCombatCore'/p.relative_to(NATIVE))
for n in ('BUILD-RESULT.md','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md'):copy(NATIVE/n,RELEASE/n)
for n in ('build.log','toolchain.log','dll-details.txt'):copy(build/n,RELEASE/'build-evidence'/n)
for n in ('package_combat_3k1.py','package_combat_3h.py','package_combat_3b3a.py','install_combat_3k1.ps1','audit_actor_values.py'):copy(ROOT/'tools'/n,RELEASE/'Source/tools'/n)
print(json.dumps(dict(build=build.name,dll_sha256=evidence['dll_sha256'],release=str(RELEASE),plan_sha256=pin),indent=2))

"""Inspect and package native325; prepare an exact two-file install transaction."""
from pathlib import Path
import difflib, hashlib, inspect, json, re, shutil, subprocess
import package_combat_3b3a as pair
from package_combat_3h import instructions
ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'native/NVOCombatCore'; OUT=ROOT/'source/combat/step3u1'
RELEASE=ROOT/'release/NVO-Combat-Packet-3U1-World-Contacts'
BUILD=CORE/'out/build-29829-21199'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
DUMP=Path(r'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\HostX64\x86\dumpbin.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
def main():
 assert not (OUT/'INSTALL-3U1-result.json').exists()
 report=json.loads((OUT/'OFFLINE-RESULT.json').read_text())
 for path,h in report['source_sha256'].items():assert sha(ROOT/path)==h,path
 scope=vars(pair).copy()
 exec(inspect.getsource(pair.inspect_pair).replace('0.3.4 | phase=3B3A','0.3.25 | phase=3U1'),scope)
 evidence=scope['inspect_pair'](BUILD)
 data=(BUILD/'NVOCombatCore.dll').read_bytes()
 assert b'CAPACITY_PROBE_BUILD enabled=0' in data and b'CAPACITY_PROBE_ARM ' not in data
 assert b'IMPACT_SPEED ' in data and b'IMPACT_TERRAIN ' in data and b'target_kind=' in data
 prior=ROOT/'release/NVO-Combat-Packet-3U-Contact-Speed/Source/NVOCombatCore'
 snap=json.loads((ROOT/'source/combat/step3u/SOURCE-SNAPSHOT.json').read_text())['source_sha256']
 changes={'src/FlightImpact.inl','src/FlightImpactJoin.inl','src/FlightContactSpeed.inl','src/FlightPhysics.cpp','src/Plugin.cpp','CMakeLists.txt','tests/contact_speed_checks.inl'}
 unchanged=[];diff=[]
 for name,h in snap.items():
  if not(name.startswith(('src/','include/','config/')) or name in ['BUILD.cmd','CMakeLists.txt']):continue
  assert sha(prior/name)==h,name
  if name not in changes:assert sha(CORE/name)==h,name;unchanged.append(name)
  else:diff.extend(difflib.unified_diff((prior/name).read_text().splitlines(True),(CORE/name).read_text().splitlines(True),fromfile='native323/'+name,tofile='native324/'+name))
 (OUT/'SOURCE-DIFF.txt').write_text(''.join(diff),encoding='utf-8')
 # Naked bridge instruction bodies must remain byte-identical in COFF output.
 asm=[]
 for build,label in [(CORE/'out/build-24180-5912','native324'),(BUILD,'native325')]:
  raw=subprocess.run([str(DUMP),'/disasm',str(build/'FlightPhysics.obj')],check=True,capture_output=True).stdout
  (OUT/'out'/f'{label}-physics-disassembly.txt').write_bytes(raw);asm.append(raw.decode().replace('\r\n','\n'))
 bridges=re.findall(r'__declspec\(naked\) void (\w+)\(\)',(CORE/'src/FlightPhysics.cpp').read_text())
 for name in bridges:assert instructions(asm[0],name)==instructions(asm[1],name),name
 evidence.update(packet='3U1',native_version=325,unchanged_inputs=unchanged,unchanged_naked_bridges=bridges,
   new_hooks=0,capacity_probe_enabled=False,damage_replacement=False,gameplay_tested=False)
 save(OUT/'STATIC-CHECKS.json',evidence)
 engine=[]
 path=ROOT/'source/combat/step3f2/runtime-20260915-195354'
 man=json.loads((path/'manifest.json').read_text())
 row=next(x for x in man['files'] if x['name']=='movement')
 assert sha(path/row['filename'])==row['sha256']
 engine.append(dict(path=str((path/row['filename']).relative_to(ROOT)),sha256=row['sha256'],finding='Z-only terrain clamp at 00930155..00930186, after query at00930150'))
 path=ROOT/'source/combat/step3b2/timing-investigation/runtime-20260915-102703'
 man=json.loads((path/'manifest.json').read_text());p=path/'projectile-code-009B7000.bin'
 assert sha(p)==man['code_sha256']
 engine.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),finding='Contact input copy and virtual32C callers; surface-point offset cause NOT established'))
 save(OUT/'ENGINE-EVIDENCE.json',engine)
 manifest=dict(packet='3U1',version='0.3.25',plugin_version=325,status='Compiled; installation and user runtime checkpoint pending',
   installed_by_assistant=False,gameplay_tested=False,damage_replacement=False,capacity_probe_enabled=False,
   build_output=str(BUILD.relative_to(CORE)),new_hooks=0,new_dependencies=[],record_changes=0,configuration_changes=0,
   exact_contact_speed_authority=False,pre_movement_contacts='unavailable')
 readme=(OUT/'README.md').read_text()
 (CORE/'README.md').write_text(readme,encoding='utf-8')
 buildtext=f'''# Native325 / Packet3U1 build

Win32 MSVC /W4 /O2 /MT /Zi; zero warnings/errors. Reader and replay harnesses /W4 /WX passed. Matching DLL/PDB; exactly two NVSE exports. All {len(bridges)} physics bridge instruction bodies unchanged. {len(unchanged)} existing compilation/configuration inputs unchanged. New code distinguishes null world contacts from references while preserving actor identity checks; damage off. Live acceptance pending.

DLL {evidence['dll_sha256']}
PDB {evidence['pdb_sha256']}
'''
 (CORE/'BUILD-RESULT.md').write_text(buildtext);(CORE/'PROGRESS.md').write_text('Packet3U1: see README.md and source/combat/step3u1. Runtime checkpoint pending. Ultra317 HOLD.\n')
 save(CORE/'manifest.json',manifest)
 for p in CORE.rglob('*'):
  if p.is_file() and not any(part in ['out','.git'] for part in p.relative_to(CORE).parts):copy(p,RELEASE/'Source/NVOCombatCore'/p.relative_to(CORE))
 for name in ['README.md','BUILD-RESULT.md','CREDITS-BALLISTX.md','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt']:copy(CORE/name,RELEASE/name)
 copy(OUT/'CONTRACT.md',RELEASE/'CONTRACT.md')
 for name in ['STATIC-CHECKS.json','OFFLINE-RESULT.json','REPLAY-ROWS.json','SOURCE-DIFF.txt','ULTRA-3U1-AUDIT.md']:copy(OUT/name,RELEASE/'Evidence'/name)
 for name in ['build.log','dll-details.txt','toolchain.log']:copy(BUILD/name,RELEASE/'build-evidence'/name)
 for name in ['reader_checks-build.log','reader_checks-results.jsonl','capture_replay-build.log','capture_replay-results.jsonl']:copy(OUT/'out'/name,RELEASE/'build-evidence'/name)
 for name in ['replay_world_contact_3u1.py','replay_contact_speed_3u.py','package_combat_3u1.py','package_combat_3b3a.py','package_combat_3h.py']:copy(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
 plan=json.loads((ROOT/'source/combat/step3u/INSTALL-3U-plan.json').read_text())
 plan.update(packet='3U1',version=325,files=[])
 for ext in ['dll','pdb']:
  rel=f'Data/NVSE/Plugins/NVOCombatCore.{ext}';target=RELEASE/rel;copy(BUILD/target.name,target)
  plan['files'].append(dict(path=rel,action='install',sha256=sha(GAME/rel),source=str(target),source_sha256=sha(target),log_may_change_until_game_exits=False))
 prior_manifest=json.loads((CORE/'manifest.json').read_text())
 expected_pair={'dll':'e1327fe7eca5284bac4cebe0a99b724e185df8297ce5119b069c20008ca3c4c7','pdb':'62575d70fe4ceb06e51bfadfff1c9637f4f9d5f1add390ea9e368e54a8098714'}
 for dep in plan['dependency_preconditions']:
  ext=Path(dep['path']).suffix.lstrip('.')
  if Path(dep['path']).stem=='NVOCombatCore':dep['sha256']=expected_pair[ext]
  assert sha(GAME/dep['path'])==dep['sha256'],dep['path']
 assert not (GAME/'Data/RD.esm').exists()
 save(OUT/'INSTALL-3U1-plan.json',plan);pin=sha(OUT/'INSTALL-3U1-plan.json')
 installer=(ROOT/'tools/install_combat_3u.ps1').read_text().replace('3U','3U1').replace('step3u','step3u1').replace('Contact-Speed','World-Contacts').replace('version -ne 324','version -ne 325').replace('version=324','version=325')
 installer=re.sub(r"-ne '[0-9a-f]{64}'","-ne '"+pin+"'",installer,count=1)
 (ROOT/'tools/install_combat_3u1.ps1').write_text(installer)
 copy(ROOT/'tools/install_combat_3u1.ps1',RELEASE/'Source/tools/install_combat_3u1.ps1')
 copy(OUT/'INSTALL-3U1-plan.json',RELEASE/'Installation/INSTALL-3U1-plan.json')
 manifest['installed_files']=[dict(path=f['path'],sha256=f['source_sha256']) for f in plan['files']]
 for p in [CORE/'manifest.json',RELEASE/'manifest.json',RELEASE/'Source/NVOCombatCore/manifest.json']:save(p,manifest)
 snapshot=dict(packet='3U1',native_version=325,capacity_probe_enabled=False,source_sha256={str(p.relative_to(CORE)).replace('\\','/'):sha(p) for p in CORE.rglob('*') if p.is_file() and 'out' not in p.relative_to(CORE).parts})
 save(OUT/'SOURCE-SNAPSHOT.json',snapshot)
 html='''<!doctype html><html lang="en"><meta charset="utf-8"><title>NVO 3U1 — world contacts</title>
<style>body{max-width:800px;margin:40px auto;padding:0 24px;background:#111b18;color:#e6ede8;font:18px/1.6 system-ui}h1{color:#b9e4b4}a{color:#a1d7ff}li{margin:16px 0}strong{color:#f7d58b}code{background:#263a31;padding:2px 7px}</style>
<h1>NVO 0.3.25 · World-contact classification</h1><p>World impacts such as ground and walls are now distinguished from actor/reference impacts using the contact pointer read by the engine observer. Actor identity checks remain strict.</p>
<p><strong>Damage remains OFF. No GECK work.</strong> Runtime acceptance is pending. The assistant replaces only the DLL and matching PDB; check its final message for installation confirmation.</p>
<h2>One short check</h2><p>Use standard ammunition and the existing 9mm pistol or <code>bat NVOFlightKit3F</code>. Keep NVO.esm and NVOFlightPilot.esp active.</p>
<ol><li>Fire two 9mm shots into distant sloping ground.</li><li>Fire one close-range 9mm hit on a living target, aimed normally.</li><li>Reload once, then fire one 9mm shot into a nearby wall. Wait a few seconds and quit normally.</li></ol>
<p>Reply <strong>finished</strong> with anything unusual. I will read NVOCombatCore.log directly. No long stress test, recording, or attempt to force a rare error is needed.</p>
<p><a href="README.md">Details, limitations and reversal</a> · <a href="CONTRACT.md">Technical contract</a></p>
<p>The old 3U recording did not contain raw target pointers, so this fresh run is the acceptance evidence for world classification.</p></html>'''
 for p in [OUT/'START-HERE.html',RELEASE/'START-HERE.html',CORE/'START-HERE.html',RELEASE/'Source/NVOCombatCore/START-HERE.html']:p.write_text(html,encoding='utf-8')
 # Snapshot after the final documentation write too.
 snapshot['source_sha256']={str(p.relative_to(CORE)).replace('\\','/'):sha(p) for p in CORE.rglob('*') if p.is_file() and 'out' not in p.relative_to(CORE).parts}
 save(OUT/'SOURCE-SNAPSHOT.json',snapshot);copy(OUT/'SOURCE-SNAPSHOT.json',RELEASE/'Evidence/SOURCE-SNAPSHOT.json')
 print(json.dumps(dict(release=str(RELEASE),dll=evidence['dll_sha256'],pdb=evidence['pdb_sha256'],unchanged_bridges=len(bridges),unchanged_inputs=len(unchanged),plan_sha256=pin),indent=2))
if __name__=='__main__':main()

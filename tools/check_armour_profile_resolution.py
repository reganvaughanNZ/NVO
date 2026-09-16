"""Offline safety checks for shared-profile exports, including actual 4D replay."""
from copy import deepcopy
import hashlib,json,re,subprocess,sys,tempfile
from pathlib import Path
from resolve_armour_profiles import resolve_document,compile_source,MAX_TAGS
from compile_armour_coverage import encode_profiles

ROOT=Path(__file__).resolve().parents[1]
PACKAGED=(ROOT/'profiles/armour-tags.json').is_file()
STEP=ROOT if PACKAGED else ROOT/'source/combat/step4e'
BASE=json.loads((STEP/'profiles/armour-tags.json').read_text())
checks=[]
def check(ok,name):
    if not ok:raise AssertionError(name)
    checks.append(name)
def reject(name,mutate):
    d=deepcopy(BASE);mutate(d)
    try:resolve_document(d)
    except ValueError:check(True,name);return
    raise AssertionError('Expected rejection: '+name)

resolved,report=resolve_document(BASE)
runtime=encode_profiles(resolved)
baseline=STEP/'Evidence/BASELINE-4D.tsv' if PACKAGED else ROOT/'source/combat/step4d/Data/NVSE/Plugins/NVOArmourCoverage.tsv'
check(runtime==baseline.read_bytes(),'base export is byte-identical to the live-tested4D file')
check(report['new_runtime_dependencies']==[] and not report['runtime_keyword_import'],'no implied live KEYWORDS integration')
check(not any(report[k] for k in ('coverage_authority','damage_replacement','stagger_writes')),'authority remains disabled')
d=deepcopy(BASE);d['bindings'].reverse();d['keyword_rules'].reverse();d['profile_definitions'].reverse()
check(encode_profiles(resolve_document(d)[0])==runtime,'input ordering cannot select a winner')
d=deepcopy(BASE);d['bindings'][0]['keywords'][0]=d['bindings'][0]['keywords'][0].lower()
check(encode_profiles(resolve_document(d)[0])==runtime,'tag matching ignores ASCII case')
d=deepcopy(BASE);d['keyword_rules'].append(dict(keyword='NVO_Alias',profile='combat-armour'));d['bindings'][0]['keywords'].append('NVO_Alias')
check(encode_profiles(resolve_document(d)[0])==runtime,'aliases selecting the same profile are unambiguous')
d=deepcopy(BASE);d['keyword_rules'].append(dict(keyword='NVO_PowerArmour',profile=None));d['bindings'][0]['keywords'].append('NVO_PowerArmour')
check(encode_profiles(resolve_document(d)[0])==runtime,'metadata alone changes no coverage')

# Synthetic forms are offline fixtures; none is asserted to exist in NVO.esm.
synthetic=deepcopy(d)
salvaged=deepcopy(synthetic['profile_definitions'][0]);salvaged.update(id='synthetic-salvaged',revision=2,rationale='OFFLINE synthetic exception; no real item mapping')
salvaged['coverage'].update(torso='unknown',left_arm='none',right_arm='none')
synthetic['profile_definitions'].append(salvaged)
synthetic['bindings']=[
 dict(plugin='NVO.esm',local_id='0000AB01',expected_equip_mask='00000004',keywords=['NVO_Coverage_CombatBody']),
 dict(plugin='NVO.esm',local_id='0000AB02',expected_equip_mask='00000004',keywords=['NVO_Coverage_CombatBody','NVO_PowerArmour']),
 dict(plugin='Custom + Armor.esp',local_id='0000AB03',expected_equip_mask='00000602',keywords=['NVO_Coverage_CombatHelmet'])]
synthetic['record_overrides']=[dict(plugin='nvo.ESM',local_id='0000AB02',profile='synthetic-salvaged',rationale='Explicit reviewed exception fixture')]
out,decisions=resolve_document(synthetic)
by_key={(r['plugin'].lower(),r['local_id']):r for r in out['profiles']}
check(by_key[('nvo.esm','0000AB01')]['coverage']['torso']=='partial' and by_key[('nvo.esm','0000AB02')]['coverage']['torso']=='unknown','exact exception affects only its own record')
check(by_key[('nvo.esm','0000AB02')]['revision']==2,'exception retains selected definition revision')
check(sum(r['selection']=='exact_record_override' for r in decisions['decisions'])==1,'exception provenance recorded explicitly')
check(len(out['profiles'])==3 and len(set(r['id'] for r in out['profiles']))==3,'shared definitions export unique exact-record entries')
unchanged=deepcopy(synthetic);resolve_document(synthetic);check(synthetic==unchanged,'resolution does not mutate caller definitions or bindings')
d=deepcopy(synthetic);d['bindings'][1]['keywords']=[]
check(len(resolve_document(d)[0]['profiles'])==3,'explicit override may supply an otherwise absent selection')

reject('boolean schema',lambda d:d.update(schema_version=True))
reject('unknown top-level field',lambda d:d.update(damage_enabled=True))
reject('unsupported region',lambda d:d['regions'].append('heart'))
reject('empty definitions',lambda d:d.update(profile_definitions=[]))
reject('empty bindings',lambda d:d.update(bindings=[]))
reject('duplicate profile definition',lambda d:d['profile_definitions'].append(deepcopy(d['profile_definitions'][0])))
reject('zero revision',lambda d:d['profile_definitions'][0].update(revision=0))
reject('boolean revision',lambda d:d['profile_definitions'][0].update(revision=True))
reject('overflow revision',lambda d:d['profile_definitions'][0].update(revision=0x100000000))
reject('missing coverage region',lambda d:d['profile_definitions'][0]['coverage'].pop('head'))
reject('unapproved fractional coverage',lambda d:d['profile_definitions'][0]['coverage'].update(head=0.5))
reject('unsupported material data',lambda d:d['profile_definitions'][0].update(material='steel'))
reject('keyword outside NVO namespace',lambda d:d['keyword_rules'][0].update(keyword='PowerArmor'))
reject('overlong keyword',lambda d:d['keyword_rules'][0].update(keyword='NVO_'+'a'*60))
reject('keyword path syntax',lambda d:d['keyword_rules'][0].update(keyword='NVO_../body'))
reject('keyword rule missing profile',lambda d:d['keyword_rules'][0].update(profile='missing'))
reject('duplicate rule ignores case',lambda d:d['keyword_rules'].append(dict(keyword=d['keyword_rules'][0]['keyword'].lower(),profile='combat-armour')))
reject('undeclared keyword typo',lambda d:d['bindings'][0].update(keywords=['NVO_Coverage_ComabtBody']))
reject('no selector or exception',lambda d:d['bindings'][0].update(keywords=[]))
reject('conflicting selectors',lambda d:d['bindings'][0]['keywords'].append('NVO_Coverage_CombatHelmet'))
def conflict_with_override(d):
 d['bindings'][0]['keywords'].append('NVO_Coverage_CombatHelmet')
 d['record_overrides'].append(dict(plugin='FalloutNV.esm',local_id='00020420',profile='combat-armour',rationale='Must not mask ambiguity'))
reject('exact override cannot hide conflicting selectors',conflict_with_override)
reject('duplicate tag on binding',lambda d:d['bindings'][0]['keywords'].append(d['bindings'][0]['keywords'][0].lower()))
reject('plugin path rejected',lambda d:d['bindings'][0].update(plugin='../NVO.esm'))
reject('load-order byte in local ID rejected',lambda d:d['bindings'][0].update(local_id='01020420'))
reject('zero local ID',lambda d:d['bindings'][0].update(local_id='00000000'))
reject('zero equip mask',lambda d:d['bindings'][0].update(expected_equip_mask='00000000'))
reject('unsupported equip mask bit',lambda d:d['bindings'][0].update(expected_equip_mask='00100000'))
reject('duplicate exact record',lambda d:d['bindings'].append(deepcopy(d['bindings'][0])))
reject('orphan exception',lambda d:d['record_overrides'].append(dict(plugin='NVO.esm',local_id='0000AB01',profile='combat-armour',rationale='No binding')))
reject('missing exception profile',lambda d:d['record_overrides'].append(dict(plugin='FalloutNV.esm',local_id='00020420',profile='missing',rationale='test')))
reject('empty exception explanation',lambda d:d['record_overrides'].append(dict(plugin='FalloutNV.esm',local_id='00020420',profile='combat-armour',rationale='')))
def duplicate_override(d):
 o=dict(plugin='FalloutNV.esm',local_id='00020420',profile='combat-armour',rationale='test');d['record_overrides']=[o,deepcopy(o)]
reject('duplicate exact exception',duplicate_override)
d=deepcopy(BASE);d['bindings']=[dict(plugin='NVO.esm',local_id=f'{i:08X}',expected_equip_mask='00000004',keywords=['NVO_Coverage_CombatBody']) for i in range(1,257)]
check(len(resolve_document(d)[0]['profiles'])==256,'256 shared-profile bindings supported')
d['bindings'].append(dict(plugin='NVO.esm',local_id='00000101',expected_equip_mask='00000004',keywords=['NVO_Coverage_CombatBody']))
try:resolve_document(d);raise AssertionError('257 records accepted')
except ValueError:check(True,'257 records rejected before export')
reject('excess tag list rejected',lambda d:d['bindings'][0].update(keywords=['NVO_A']*(MAX_TAGS+1)))

# Failure must not damage an existing generated profile file.
with tempfile.TemporaryDirectory(prefix='nvo4e-',dir=STEP/'checks') as temp:
 folder=Path(temp).resolve();assert folder.parent==(STEP/'checks').resolve()
 source=folder/'source.json';dest=folder/'output.tsv';dest.write_bytes(b'previous reviewed output')
 source.write_text('{"schema_version":1,"schema_version":1}')
 command=[sys.executable,str(Path(__file__).with_name('resolve_armour_profiles.py')),str(source),str(dest)]
 failed=subprocess.run(command,capture_output=True,text=True)
 check(failed.returncode==2 and dest.read_bytes()==b'previous reviewed output','duplicate JSON fields fail without replacing existing output')
 source.write_bytes(b'x'*1048577);failed=subprocess.run(command,capture_output=True,text=True)
 check(failed.returncode==2 and dest.read_bytes()==b'previous reviewed output','oversized source fails without replacing existing output')
 source.write_text(json.dumps(BASE));ok=subprocess.run(command,capture_output=True,text=True)
 check(ok.returncode==0 and dest.read_bytes()==runtime,'CLI success produces the validated4D format')
 refused=subprocess.run([sys.executable,str(Path(__file__).with_name('resolve_armour_profiles.py')),str(source),str(source)],capture_output=True,text=True)
 check(refused.returncode==2 and json.loads(source.read_text())==BASE,'CLI refuses overwriting its authoring source')

# Replay every4D authored row, independent of inventory order after reload.
capture=STEP/'Evidence/REFERENCE-4D.log' if PACKAGED else ROOT/'source/combat/step4d/Evidence/LIVE-4D-20260917-010933.log'
check(hashlib.sha256(capture.read_bytes()).hexdigest()=='02f55dd6afa9999a85a595025c06c89f66a674f861a239f6a459335448fd5862','4D live capture pinned')
profiles={(p['plugin'].lower(),int(p['local_id'],16)):p for p in resolved['profiles']}
matched=0
for line in capture.read_text().splitlines():
 if not line.startswith('ARMOUR_COVERAGE_ITEM '):continue
 fields={k:(q or plain) for k,q,plain in re.findall(r'(\w+)=(?:"([^"]*)"|(\S+))',line)}
 p=profiles[(fields['plugin'].lower(),int(fields['local'],16))]
 assert p['coverage']=={r:fields[r] for r in p['coverage']}
 assert p['revision']==int(fields['revision']);matched+=1
check(matched==5,'all five recorded coverage rows preserved, including reload ordering')

(STEP/'checks/SYNTHETIC-ONLY.json').write_text(json.dumps(synthetic,indent=2)+'\n')
(STEP/'checks/SYNTHETIC-ONLY.tsv').write_bytes(encode_profiles(out))
result=dict(checks=len(checks),passed=checks,synthetic_not_game_records=True,live_rows_replayed=matched,game_launched=False,new_runtime_dependencies=[])
(STEP/'Evidence/RESOLUTION-CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'PASS {len(checks)} resolution/export checks; {matched} recorded4D coverage rows; no game activity')

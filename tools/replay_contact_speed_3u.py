"""Build/run the actual diagnostic code offline using pinned historical inputs.

Engine reads are fixtures, never a DLL load. Missing historical flags/reset
evidence stays missing; a separate prospective replay supplies those two new
live observations explicitly and must not be described as captured proof.
"""
from pathlib import Path
import hashlib, json, re, subprocess

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'native/NVOCombatCore'
OUT=ROOT/'source/combat/step3u'
BUILD=OUT/'out'
CAPTURES=[
 ('3G2','source/combat/step3g2/captures/2026-09-15-3G2-5c4e764753b7/NVOCombatCore.log','5c4e764753b73c258a176e4270b5b5bdbf8255ac6d35c097daa259cf89fcca63'),
 ('3H','source/combat/step3h/captures/2026-09-16-3H-e8d6c57f37f9/NVOCombatCore.log','e8d6c57f37f94a6ef93975ebede002bcea145824d5a8aff85e3ab2024d2968f5'),
 ('3Q','source/combat/step3q/captures/review-37821ee73c00/NVOCombatCore.log','37821ee73c001055b279fc56af83b8c57471ccefc16caac7e8e9a83fbde30b64')]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o): p.write_text(json.dumps(o,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def vector(s): return '{'+s.strip('()')+'}'
def main():
 BUILD.mkdir(parents=True,exist_ok=True)
 physics=(CORE/'src/FlightPhysics.cpp').read_text()
 helper=(CORE/'src/FlightImpact.inl').read_text()
 types=physics[physics.index('struct Vec {'):physics.index('Track gTracks')]
 math=physics[physics.index('double Cd('):physics.index('#include "FlightImpact.inl"')]
 start,end=helper.index('bool ImpactVector('),helper.index('void ImpactReset()')
 helper=helper[:start]+'''ImpactSample fixture{};
ImpactSample ReadImpact(const Track&,const float* =nullptr) noexcept { return fixture; }
'''+helper[end:]
 header='''#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstdarg>
#include <cassert>
#include <limits>
#include <string>
#include <vector>
#include <algorithm>
using U32=std::uint32_t; using U64=unsigned long long; using DWORD=std::uint32_t;
unsigned gSession=1,checks=0;
void Check(bool ok,const char* message) { ++checks; if(!ok) { fprintf(stderr,"CHECK FAILED: %s\\n",message); exit(1); } }
namespace nvo::log { std::vector<std::string> rows;
bool Write(const char* format,...) { char buffer[2048]; va_list args;
va_start(args,format); const int n=vsnprintf(buffer,sizeof(buffer),format,args); va_end(args);
Check(n>0 && n<767,"native logger row length"); rows.emplace_back(buffer); return true; } }
#include "FlightDragData.hpp"
#include "FlightPhysics.hpp"
'''
 cases=[]; evidence=[]
 for label,rel,expected_hash in CAPTURES:
  path=ROOT/rel
  assert sha(path)==expected_hash
  rows={}; flags={}; reset=set()
  for number,line in enumerate(path.read_text().splitlines(),1):
   tag=line.split(' ',1)[0]; d=dict(re.findall(r'(\w+)=([^\s]+)',line))
   if not all(k in d for k in ['session','lifetime']): continue
   life=(d['session'],d['lifetime'])
   if tag=='FLIGHT_RANGE' and d.get('phase')=='impact': flags[life]=(d,number)
   if tag=='PHYSICS_LOCAL_Z' and d.get('reset_branch_observed')=='1': reset.add((*life,d['step']))
   if tag in ['IMPACT_STEP','IMPACT_GEOMETRY','IMPACT_VELOCITY','IMPACT_MODEL']:
    key=(*life,d['step']); rows.setdefault(key,{})[tag]=(d,number)
  for key,entry in rows.items():
   s,sn=entry['IMPACT_STEP']; g,gn=entry['IMPACT_GEOMETRY']; v,vn=entry['IMPACT_VELOCITY']; old,_=entry['IMPACT_MODEL']
   flag=flags.get(key[:2]); has_reset=key in reset
   evidence.append(dict(capture=label,capture_sha256=expected_hash,session=int(key[0]),lifetime=int(key[1]),step=int(key[2]),
      step_line=sn,geometry_line=gn,velocity_line=vn,flags_line=flag[1] if flag else None,reset_observed=has_reset,
      flags_timing='later impact callback, not a captured accounting-boundary read',old_status=old['status']))
   c=['{ ImpactRecord r{}; Track t{};']
   for field,k in [('serial','lifetime'),('step','step')]: c.append(f'r.{field}={s[k]};')
   for field,k in [('ref','projectile'),('source','source'),('weapon','weapon'),('ammo','ammo'),('base','base')]: c.append(f'r.{field}=0x{s[k]};')
   c.append(f'r.wrote={s["applied"]}; r.baselineVerified={s["baseline_verified"]}; r.dt={s["dt_s"]}; r.tolerance={g["tolerance"]};')
   for field,k in [('start','start'),('expected','expected')]: c.append(f'r.{field}={vector(g[k])};')
   c.append(f'r.before={vector(v["before"])}; r.full={vector(v["proposed_full"])}; r.bc={v["bc"]}; r.dragModel={v["drag_model"]};')
   for field,k in [('position','position'),('point','contact'),('accounting','accounting_delta')]: c.append(f'r.collision.{field}={vector(g[k])};')
   known_reference=int(s['target'],16)!=0
   c.append(f'r.collision.valid={s["valid_mask"]}; r.collision.target=0x{s["target"]}; r.collision.targetKind=ImpactTargetKind::{"Reference" if known_reference else "Invalid"}; r.collision.region={s["region"]}; r.collision.more={s["more_contacts"]};')
   c.append(f'r.resetObserved={int(has_reset)}; r.collision.policyRead={int(flag is not None)}; r.collision.flags=0x{flag[0]["flags"] if flag else "0"};')
   c.append(f'gConfig={{{v["units_per_metre"]},{v["gravity"]},{v["density"]},{v["sound"]}}};')
   c.append('t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; auto point=EvaluateImpact(r,t);')
   c.append(f'Check(std::string(point.status)=="{old["status"]}","legacy point status unchanged");')
   c.append(f'Check(point.estimate=={old["candidate_valid"]},"legacy point admission unchanged");')
   c.append('auto result=EvaluateContactSpeed(r,t); auto prospective=r; prospective.resetObserved=true; prospective.collision.policyRead=true; prospective.collision.flags=0x10100; if(!prospective.collision.target && prospective.collision.region==-1) prospective.collision.targetKind=ImpactTargetKind::World; auto p=EvaluateContactSpeed(prospective,t);')
   c.append(f'''printf("{{\\"capture\\":\\"{label}\\",\\"session\\":{key[0]},\\"lifetime\\":{key[1]},\\"step\\":{key[2]},\\"historical_metadata_available\\":%d,\\"status\\":\\"%s\\",\\"range_available\\":%d,\\"low_mps\\":%.12g,\\"high_mps\\":%.12g,\\"old_point_candidate\\":%d,\\"prospective_status\\":\\"%s\\",\\"prospective_available\\":%d}}\\n",r.resetObserved&&r.collision.policyRead,result.status,result.available,result.low,result.high,point.estimate,p.status,p.available);''')
   c.append('if(result.available) { if(result.engineSegment) { baselineSeed=r; baselineTrack=t; } else { ownedSeed=r; ownedTrack=t; } } }')
   cases.append('\n'.join(c))
 tests=(CORE/'tests/contact_speed_checks.inl').read_text()
 harness=header+types+math+helper+'\nint main() { ImpactRecord baselineSeed{},ownedSeed{}; Track baselineTrack{},ownedTrack{};\n'+ '\n'.join(cases)+tests+'\n}\n'
 (BUILD/'replay.cpp').write_text(harness,encoding='utf-8')
 cmd=f'''@echo off
call "C:\\Program Files\\Microsoft Visual Studio\\18\\Community\\Common7\\Tools\\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /I"{CORE/'include'}" /I"{CORE/'src'}" replay.cpp /Fe:replay.exe >build.log 2>&1
if errorlevel 1 exit /b 1
replay.exe >results.jsonl
exit /b %ERRORLEVEL%
'''
 (BUILD/'RUN.cmd').write_text(cmd)
 subprocess.run(['cmd.exe','/d','/c',str(BUILD/'RUN.cmd')],cwd=BUILD,check=True)
 results=[json.loads(line) for line in (BUILD/'results.jsonl').read_text().splitlines()]
 save(OUT/'REPLAY-ROWS.json',results[:-1]); save(OUT/'CAPTURE-EVIDENCE.json',evidence)
 sources=[CORE/'src'/n for n in ['FlightImpact.inl','FlightImpactModel.inl','FlightContactSpeed.inl','FlightImpactJoin.inl','FlightPhysics.cpp']]
 sources+=[CORE/'tests/contact_speed_checks.inl',Path(__file__)]
 report=dict(packet='3U',rows=len(evidence),available_with_historical_metadata=sum(r['range_available'] for r in results[:-1]),
    prospective_available=sum(r['prospective_available'] for r in results[:-1]),old_point_candidates=sum(r['old_point_candidate'] for r in results[:-1]),
    checks=results[-1],source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},harness_sha256=sha(BUILD/'replay.cpp'),
    native_engine_reads='stubbed with historical values or explicitly prospective flags/reset',dll_or_game_loaded=False,
    contact_point_cause_resolved=False,damage_authority=False)
 save(OUT/'REPLAY-RESULT.json',report)
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256']},indent=2))
if __name__=='__main__': main()

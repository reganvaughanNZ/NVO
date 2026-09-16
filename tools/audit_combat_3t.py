"""Offline distance/clock audit. Read stored captures; never attach to the game."""
from pathlib import Path
import hashlib
import json
import math
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'source/combat/step3t'
BUILD = OUT/'out'
CORE = ROOT/'native/NVOCombatCore'
CAPTURES = [
    ('3B3A-VATS','source/combat/step3b3a/captures/2026-09-15-3B3A-vats-2e0346c2642c/NVOCombatCore.log','2e0346c2642c2e3e8dbb9a6a02f515fceb9533431c81627f8205cb65b6851ec8'),
    ('3G2','source/combat/step3g2/captures/2026-09-15-3G2-5c4e764753b7/NVOCombatCore.log','5c4e764753b73c258a176e4270b5b5bdbf8255ac6d35c097daa259cf89fcca63'),
    ('3Q','source/combat/step3q/captures/review-37821ee73c00/NVOCombatCore.log','37821ee73c001055b279fc56af83b8c57471ccefc16caac7e8e9a83fbde30b64'),
    ('3R','source/combat/step3r/captures/passed-5e0d186d6c99/NVOCombatCore.log','5e0d186d6c99525ffb8ecc472fd63634fa7d9b2f22386492ff654196b14cc73a'),
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok, message):
    if not ok: raise ValueError(message)
def save(p, obj): p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def f32(x): return struct.unpack('<f',struct.pack('<f',x))[0]
def ulp32(x):
    bits=struct.unpack('<I',struct.pack('<f',x))[0]
    return struct.unpack('<f',struct.pack('<I',bits+1))[0]-f32(x)

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    source=(CORE/'src/FlightPhysics.cpp').read_text()
    # Actual unchanged production vector functions and integrator. The narrow
    # Track shim supplies only the two profile values used by that calculation.
    vec=source[source.index('struct Vec {'):source.index('struct Track {')]
    math_code=source[source.index('double Cd('):source.index('#include "FlightImpact.inl"')]
    harness='''#include <cmath>
#include <cstdio>
#include <cstdlib>
#include "FlightDragData.hpp"
'''+vec+'''struct Track { unsigned dragModel; double ballisticCoefficient; };
'''+math_code+'''
unsigned checks=0, replayed=0;
double maxSpeedError=0,maxDistanceError=0,maxVerticalError=0;
void Check(bool ok,const char* label) {
 ++checks; if(!ok) {std::fprintf(stderr,"FAIL %s\\n",label);std::exit(1);}
}
void Replay(unsigned model,double bc,double dt,double speed,double vz,double after,double afterZ,double distance,double dz) {
 Track t{model,bc}; Vec v{std::sqrt(speed*speed-vz*vz),0,vz};
 Vec d=Integrate(v,dt,t);
 double se=std::abs(Length(v)-after),de=std::abs(Length(d)*gConfig.units-distance);
 double ze=std::abs(d.z*gConfig.units-dz);
 if(se>maxSpeedError)maxSpeedError=se;if(de>maxDistanceError)maxDistanceError=de;if(ze>maxVerticalError)maxVerticalError=ze;
 // These budgets cover nine-significant-digit text inputs only. They are NOT
 // collision tolerances and do not change runtime acceptance.
 Check(se<=0.00001,"logged final speed");Check(std::abs(v.z-afterZ)<=0.00001,"logged vertical speed");
 Check(de<=0.0001,"logged displacement magnitude");Check(ze<=0.0001,"logged vertical displacement");++replayed;
}
struct Run {Vec v,d;};
Run Advance(const Track& t,double speed,double total,unsigned n) {
 Run r{{speed,0,0},{}};for(unsigned i=0;i<n;++i)r.d=Add(r.d,Integrate(r.v,total/n,t));return r;
}
int main() {
 gConfig={70,9.80665,1.225,340.294};
'''
    summaries=[]; detailed=[]; snapshot_hashes={}
    for label,rel,expected in CAPTURES:
        path=ROOT/rel;check(sha(path)==expected,rel+' capture changed');snapshot_hashes[rel]=expected
        previous={};pending={};tracks={};per_capture=[];clock_pairs=0;clock_equal=0;life_pairs=0;life_still=0
        max_life_error=0;parent_errors=[];baselines=[];missing_parent=[];moving=0
        for line_no,line in enumerate(path.read_text().splitlines(),1):
            tag=line.split(' ',1)[0]
            if tag not in ('PHYSICS_TRACK','PHYSICS_STEP','FLIGHT_STEP'):continue
            d=dict(re.findall(r'(\w+)=([^\s]+)',line));key=(d['session'],d['lifetime'])
            if tag=='PHYSICS_TRACK':
                check(key not in tracks,'duplicate physics track');tracks[key]=d;continue
            if tag=='PHYSICS_STEP':
                check(key not in pending,'overlapping logged movement rows');pending[key]=(d,line_no)
                dt=float(d['dt_s']);adjusted=float(d['movement_dt_s']);clock_pairs+=1;clock_equal+=int(dt==adjusted)
                check(0<dt<=.25 and adjusted>=0,'bad clock delta')
                delta=[float(x) for x in d['world_delta'].strip('()').split(',')]
                distance=math.sqrt(sum(x*x for x in delta))
                if d['phase']=='baseline':
                    ratio=distance/(dt*70)/float(d['speed_before_mps']);baselines.append(abs(ratio-1))
                    check(abs(ratio-1)<1e-7,'baseline coordinate conversion mismatch')
                else:
                    t=tracks[key]
                    values=[t['drag_model'].lstrip('G'),t['bc'],d['dt_s'],d['speed_before_mps'],d['vz_before'],d['speed_after_mps'],d['vz_after'],format(distance,'.17g'),format(delta[2],'.17g')]
                    check(all(math.isfinite(float(x)) for x in values),'nonfinite replay')
                    harness+='Replay('+','.join(values)+');\n'
                    detailed.append(dict(capture=label,session=int(key[0]),lifetime=int(key[1]),step=int(d['step']),source_line=line_no))
                continue
            before=float(d['life_before_s']);after=float(d['life_after_s']);dt=float(d['dt_arg_s'])
            check(before==after,'lifetime changed inside UpdateProjectile sample')
            life_still+=1;moving+=int(d['phase']=='moving')
            if key in previous:
                prev=previous[key]
                check(int(d['step'])==int(prev['step'])+1,'nonconsecutive timing rows')
                # Base update increments lifetime AFTER our observed virtual call.
                expected_life=f32(f32(float(prev['life_after_s']))+f32(float(prev['dt_arg_s'])))
                error=abs(f32(before)-expected_life);max_life_error=max(max_life_error,error)
                check(error<=ulp32(expected_life),'next lifetime differs from previous engine timestep')
                life_pairs+=1
            previous[key]=d
            if key in pending:
                p,pline=pending.pop(key);error=abs(float(p['dt_s'])-dt);parent_errors.append(error)
                check(error==0,'physics clock differs from enclosing update')
                per_capture.append(dict(session=int(key[0]),lifetime=int(key[1]),physics_line=pline,timing_line=line_no,dt=dt))
        # Each observer has its own 64-row budget. A no-motion startup sample
        # can exhaust Timing one update before Physics. Keep that row unpaired;
        # a logged cap is an explanation, never invented timing evidence.
        capped=set()
        for line in path.read_text().splitlines():
            if line.startswith('FLIGHT_TIMING_SHOT ') and 'capped=1 ' in line:
                row=dict(re.findall(r'(\w+)=([^\s]+)',line));capped.add((row['session'],row['lifetime']))
        for key,(row,number) in pending.items():
            check(key in capped,'uncapped physics intent has no enclosing timing return: '+str((label,key,number)))
            missing_parent.append(dict(session=int(key[0]),lifetime=int(key[1]),line=number,reason='timing_observer_capped'))
        summaries.append(dict(capture=label,sha256=expected,timing_rows=life_still,moving_rows=moving,lifetime_next_update_pairs=life_pairs,
            max_lifetime_prediction_error_s=max_life_error,physics_parent_pairs=len(parent_errors),max_parent_dt_error_s=max(parent_errors,default=0),
            movement_clock_pairs=clock_pairs,movement_equals_parent=clock_equal,baseline_roundtrips=len(baselines),
            max_baseline_relative_error=max(baselines,default=0),unpaired_due_to_timing_cap=missing_parent,
            limitation='No per-row VATS mode/global time factor was captured; the 3B3A label and 3Q shot7 are user-reported context.'))
        save(OUT/(label+'-PAIRS.json'),per_capture)
    harness+='''
 // Equal simulated flight time with different scheduling/slow-motion partitions.
 // No claim these synthetic factors were exercised by the installed VATS code.
 double maxPartitionPosition=0,maxPartitionSpeed=0;
 for(Track t : {Track{1,.155},Track{7,.209}}) {
  const double speed=t.dragModel==1?387.1090909090909:849.7709923664122;
  const auto reference=Advance(t,speed,1,240);
  for(unsigned n : {60u,120u,600u,2400u}) {
   const auto r=Advance(t,speed,1,n);
   const double pe=Length(Add(r.d,Mul(reference.d,-1))),se=Length(Add(r.v,Mul(reference.v,-1)));
   if(pe>maxPartitionPosition)maxPartitionPosition=pe;if(se>maxPartitionSpeed)maxPartitionSpeed=se;
   Check(pe<0.001,"partition position within 1mm");Check(se<0.001,"partition velocity within 1mm/s");
   Check(std::abs(Length(r.v)*Length(r.v)/(Length(reference.v)*Length(reference.v))-1)<0.00001,"energy partition relative error");
  }
 }
 // Analytic zero-drag oracle verifies the real integrator's units/gravity.
 gConfig.density=0;
 for(unsigned n : {60u,600u}) {
  const auto r=Advance({1,.155},400,1,n);
  Check(std::abs(r.d.x-400)<1e-9,"metres versus engine coordinates");
  Check(std::abs(r.d.z+4.903325)<1e-9,"analytic gravity distance");
  Check(std::abs(r.v.z+9.80665)<1e-9,"analytic gravity velocity");
 }
 // A synthetic Turbo-style later clock change cannot change the denominator
 // of the earlier displacement. Also exposes a second slow-time multiplier.
 const double parent=.0016, later=.016, displacement=400*70*parent;
 const double correct=displacement/(70*parent),wrong=displacement/(70*later);
 Check(std::abs(correct-400)<1e-10,"parent clock speed");
 Check(std::abs(wrong/correct-.1)<1e-10,"later clock produces wrong speed");
 Check(std::abs(wrong*wrong/(correct*correct)-.01)<1e-10,"wrong clock squares energy error");
 std::printf("{\\"checks_passed\\":%u,\\"logged_applied_steps_replayed\\":%u,\\"max_speed_error_mps\\":%.12g,\\"max_distance_error_units\\":%.12g,\\"max_vertical_error_units\\":%.12g,\\"max_partition_position_error_m\\":%.12g,\\"max_partition_speed_error_mps\\":%.12g,\\"game_loaded\\":false}\\n",checks,replayed,maxSpeedError,maxDistanceError,maxVerticalError,maxPartitionPosition,maxPartitionSpeed);
}
'''
    harness=harness.replace('#include <cstdlib>','#include <cstdlib>\n#include <initializer_list>')
    (BUILD/'clock_checks.cpp').write_text(harness,encoding='utf-8')
    cmd=f'''@echo off
setlocal
cd /d "%~dp0"
call "C:\\Program Files\\Microsoft Visual Studio\\18\\Community\\Common7\\Tools\\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /I"{CORE/'include'}" clock_checks.cpp /Fe:clock_checks.exe /link /INCREMENTAL:NO >build.log 2>&1
if errorlevel 1 exit /b 1
clock_checks.exe >checks.json
exit /b %ERRORLEVEL%
'''
    (BUILD/'RUN.cmd').write_text(cmd,encoding='utf-8')
    subprocess.run(['cmd.exe','/d','/c',str(BUILD/'RUN.cmd')],cwd=BUILD,check=True)
    checks=json.loads((BUILD/'checks.json').read_text())
    captured=ROOT/'source/combat/step3b2/timing-investigation/runtime-20260915-102703'
    manifest=json.loads((captured/'manifest.json').read_text(encoding='utf-8-sig'))
    code=captured/'projectile-code-009B7000.bin'
    check(sha(code)==manifest['code_sha256'],'engine capture changed')
    slices={name:hashlib.sha256(code.read_bytes()[start-0x9B7000:end-0x9B7000]).hexdigest() for name,start,end in [
        ('parent_clock_and_vats_branch',0x9BECCA,0x9BED4F),('virtual_call_then_lifetime_increment',0x9BEF7A,0x9BEFA6),
        ('displacement_built_before_turbo_clock',0x9BF300,0x9BF416)]}
    # No gameplay code was edited. Preserve the normal installed DLL identity.
    frozen=json.loads((ROOT/'source/combat/step3r1/SOURCE-SNAPSHOT.json').read_text())['source_sha256']
    checked={n:h for n,h in frozen.items() if n.startswith(('src/','src\\','include/','include\\','config/','config\\')) or n in ('BUILD.cmd','CMakeLists.txt')}
    check(all(sha(CORE/n)==h for n,h in checked.items()),'production source/config changed')
    installed=json.loads((ROOT/'source/combat/step3r1/INSTALL-3R1-result.json').read_text())['installed']
    game=Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
    check(all(sha(game/item['path'])==item['sha256'] for item in installed),'installed native323 changed')
    refs=Path(r'C:/Users/regan/Desktop/NVO Mod References (Open Source)')
    supporting=[refs/'JIP-LN-NVSE-main/nvse/GameUI.h',refs/'JIP-LN-NVSE-main/nvse/GameForms.h',
        refs/'JIP-LN-NVSE-main/nvse/GameData.h',refs/'Stewie Tweaks 10.00 Source/nvse/nvse/GameAPI.cpp',
        ROOT/'source/combat/step3b2/timing-investigation/BallistXMain-reference.txt']
    result=dict(packet='3T',native_version_unchanged=323,game_files_written=False,game_started=False,
        captures=summaries,cpp_checks=checks,production_inputs_unchanged=len(checked),
        engine_snapshot_sha256=manifest['code_sha256'],engine_slice_sha256=slices,
        supporting_primary_source_sha256={str(p):sha(p) for p in supporting},
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [CORE/'src/FlightPhysics.cpp',CORE/'src/FlightTiming.cpp',CORE/'include/FlightDragData.hpp',Path(__file__),BUILD/'clock_checks.cpp']},
        decisions=dict(world_scale='retain authored 70 units/metre convention; no physical-world calibration claimed',
        clock='use incoming UpdateProjectile timestep once; it already follows parent VATS handling',
        measured_contact_speed=False,damage_authority=False,ultra_gate='HOLD'))
    save(OUT/'RESULT.json',result);save(OUT/'REPLAY-ROWS.json',detailed)
    print(json.dumps(dict(captures=summaries,cpp_checks=checks),indent=2))

if __name__=='__main__': main()

"""Replay immutable impact inputs through the actual C++ diagnostic model.

Generates an offline executable, never loads the DLL/game. Engine reads are
stubbed with captured snapshots; the model, integrator and cache code are real.
"""
from pathlib import Path
import hashlib,json,re,subprocess

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
OUT=ROOT/'source/combat/step3g1/replay'
CAP=ROOT/'source/combat/step3g/captures/2026-09-15-3G-018ec6d9b0b6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vec(s):return '{'+s.strip('()')+'}'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    a=json.loads((CAP/'audit.json').read_text())
    assert sha(CAP/'NVOCombatCore.log')==a['capture']['sha256']
    physics=(PROJECT/'src/FlightPhysics.cpp').read_text()
    helper=(PROJECT/'src/FlightImpact.inl').read_text()
    types=physics[physics.index('struct Vec {'):physics.index('Track gTracks')]
    math=physics[physics.index('double Cd('):physics.index('#include "FlightImpact.inl"')]
    start=helper.index('bool ImpactVector(');end=helper.index('void ImpactReset()')
    helper=helper[:start]+'''ImpactSample fixture{};
ImpactSample ReadImpact(const Track&,const float* =nullptr) noexcept { return fixture; }
'''+helper[end:]
    header='''#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdarg>
#include <cassert>
#include <string>
#include <vector>
using U32=std::uint32_t; using U64=unsigned long long; using DWORD=std::uint32_t;
unsigned gSession=1;
namespace nvo::log { std::vector<std::string> rows;
bool Write(const char* format,...) { char buffer[2048]; va_list args;
va_start(args,format); int n=vsnprintf(buffer,sizeof(buffer),format,args); va_end(args);
assert(n>0 && n<767); rows.emplace_back(buffer); return true; } }
#include "FlightDragData.hpp"
'''
    cases=[]
    for step,g,v in zip(a['impact_steps'],a['impact_geometry'],a['impact_velocity']):
        assert step['lifetime']==g['lifetime']==v['lifetime']
        lines=['{ ImpactRecord r{}; Track t{};']
        for field,key in [('serial','lifetime'),('step','step')]:lines.append(f'r.{field}={step[key]};')
        for field,key in [('ref','projectile'),('source','source'),('weapon','weapon'),('ammo','ammo'),('base','base')]:lines.append(f'r.{field}=0x{step[key]};')
        lines+= [f'r.wrote={step["applied"]}; r.baselineVerified={step["baseline_verified"]}; r.dt={step["dt_s"]}; r.tolerance={g["tolerance"]};']
        for field,key in [('start','start'),('expected','expected')]:lines.append(f'r.{field}={vec(g[key])};')
        lines += [f'r.before={vec(v["before"])}; r.full={vec(v["proposed_full"])};',f'r.bc={v["bc"]}; r.dragModel={v["drag_model"]};']
        for field,key in [('position','position'),('point','contact'),('accounting','accounting_delta')]:lines.append(f'r.collision.{field}={vec(g[key])};')
        lines+=[f'r.collision.valid={step["valid_mask"]}; r.collision.target=0x{step["target"]}; r.collision.region={step["region"]};',
            f'gConfig={{{v["units_per_metre"]},{v["gravity"]},{v["density"]},{v["sound"]}}};',
            '''t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\\"lifetime\\":%llu,\\"status\\":\\"%s\\",\\"candidate\\":%d,\\"time_s\\":%.12g,\\"speed_mps\\":%.12g,\\"model_gap\\":%.12g,\\"tolerance\\":%.12g}\\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(r.serial<=2) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15; ImpactEvent(t,false); ImpactEvent(t,true);
}''']
        cases.append('\n'.join(lines))
    tests='''
assert(seed.serial && gImpactObserved==8 && gImpactCorrelated==8 && gImpactBaselineContacts==2);
auto bad=seed; bad.collision.position.x+=10; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.collision.accounting.y+=10; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.collision.point.z+=10; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.collision.more=true; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.collision.valid=15; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.dt=0; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.before=Mul(seed.before,-1); assert(!EvaluateImpact(bad,seedTrack).estimate);
for(U64 serial=9;serial<=34;++serial) {
seedTrack.serial=serial; ImpactEnroll(seedTrack); fixture=seed.collision;
ImpactCollision(seedTrack,nullptr); fixture.position=fixture.point; fixture.valid=15;
ImpactEvent(seedTrack,false); ImpactEvent(seedTrack,false); ImpactEvent(seedTrack,true);
}
assert(gImpactAdmitted==32 && gImpactOmitted==2 && gImpactObserved==32);
assert(gImpactCallbacks==32 && gImpactCorrelated==32 && gImpactDuplicateCallbacks==24);
assert(gImpactUnpaired==0 && gImpactDestroyWithoutCallback==0);
ImpactFinish("offline_replay"); assert(gImpactAdmitted==0 && gImpactObserved==0);
assert(!ImpactFind(10));
// Independent reset: callback without collision, duplicate dedup, missing callback.
seedTrack.serial=10; ImpactEnroll(seedTrack); ImpactEvent(seedTrack,false); ImpactEvent(seedTrack,false);
assert(gImpactUnpaired==1 && gImpactDuplicateCallbacks==1);
seedTrack.serial=11; ImpactEnroll(seedTrack); fixture=seed.collision;
ImpactCollision(seedTrack,nullptr); ImpactEvent(seedTrack,true); assert(gImpactDestroyWithoutCallback==1);
ImpactReset(); for(const auto& row:nvo::log::rows) assert(row.size()<767);
puts("{\\"negative_guards\\":7,\\"later_lifetimes_through\\":32,\\"omitted\\":2,\\"cache_lifecycle_checks\\":true,\\"game_loaded\\":false}");
}
'''
    source=header+types+math+helper+'\nint main() { ImpactRecord seed{}; Track seedTrack{};\n'+''.join(cases)+tests
    (OUT/'replay.cpp').write_text(source)
    cmd='''@echo off
call "C:\\Program Files\\Microsoft Visual Studio\\18\\Community\\Common7\\Tools\\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /I"'''+str(PROJECT/'include')+'" /I"'+str(PROJECT/'src')+'" replay.cpp /Fe:replay.exe >build.log 2>&1\nif errorlevel 1 exit /b 1\nreplay.exe >results.jsonl\nexit /b %ERRORLEVEL%\n'
    (OUT/'RUN.cmd').write_text(cmd)
    subprocess.run(['cmd.exe','/d','/c',str(OUT/'RUN.cmd')],cwd=OUT,check=True)
    result=[json.loads(line) for line in (OUT/'results.jsonl').read_text().splitlines()]
    info=dict(capture_sha256=a['capture']['sha256'],results=result,
        sources={str(p.relative_to(ROOT)):sha(p) for p in [PROJECT/'src/FlightImpact.inl',PROJECT/'src/FlightImpactModel.inl',PROJECT/'src/FlightPhysics.cpp',PROJECT/'include/FlightDragData.hpp']},
        harness_sha256=sha(OUT/'replay.cpp'),engine_reads='stubbed_with_captured_values',dll_or_game_loaded=False)
    (OUT/'REPLAY-RESULT.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

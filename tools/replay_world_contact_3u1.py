"""Offline 3U1 reader and completed-capture replay; never loads the DLL/game."""
from pathlib import Path
import hashlib,json,re,subprocess

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'native/NVOCombatCore'; OUT=ROOT/'source/combat/step3u1'; BUILD=OUT/'out'
CAP=ROOT/'source/combat/step3u/captures/review-20453d5c1e84/NVOCombatCore.log'
CAP_SHA='20453d5c1e84f965f408d0721c283d2b851e852cdae51b43ca2f2ef376900b08'
PYTHON_SOURCE=Path(__file__).resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def vec(s):return '{'+s.strip('()')+'}'
def run(name,source):
    path=BUILD/(name+'.cpp');path.write_text(source,encoding='utf-8')
    cmd=f'''@echo off
call "C:\\Program Files\\Microsoft Visual Studio\\18\\Community\\Common7\\Tools\\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >{name}-toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /I"{CORE/'include'}" /I"{CORE/'src'}" {name}.cpp /Fe:{name}.exe >{name}-build.log 2>&1
if errorlevel 1 exit /b 1
{name}.exe >{name}-results.jsonl
exit /b %ERRORLEVEL%
'''
    (BUILD/(name+'.cmd')).write_text(cmd)
    subprocess.run(['cmd.exe','/d','/c',str(BUILD/(name+'.cmd'))],cwd=BUILD,check=True)
    return [json.loads(x) for x in (BUILD/(name+'-results.jsonl')).read_text().splitlines()]

def reader_source():
    impact=(CORE/'src/FlightImpact.inl').read_text()
    physics=(CORE/'src/FlightPhysics.cpp').read_text()
    classifier=physics[physics.index('enum class ImpactTargetKind'):physics.index('struct ContactTerrain')]
    sample=impact[impact.index('struct ImpactSample {'):impact.index('struct ImpactRecord {')]
    functions=impact[impact.index('bool ImpactVector('):impact.index('void ImpactReset()')]
    return '''#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
using U32=std::uint32_t; using U64=unsigned long long;
constexpr std::uintptr_t kVtable=0x108FA44;
struct Vec { double x{},y{},z{}; };
'''+classifier+'''
const void* denied{};
template<class T> bool Read(const void* p,std::ptrdiff_t offset,T& value) noexcept {
 if(!p || static_cast<const char*>(p)+offset==denied) return false;
 std::memcpy(&value,static_cast<const char*>(p)+offset,sizeof(value)); return true;
}
namespace nvo::hit { struct Form { U32 id{}; unsigned char type{}; };
bool ReadForm(void* p,Form& result) noexcept {
 result={}; if(!p) return true; if(p==reinterpret_cast<void*>(0xDEAD0000)) return false;
 unsigned char h[16]{}; if(!Read(p,0,h)) return false; result.type=h[4]; std::memcpy(&result.id,h+12,4); return true;
}}
struct Track { void* p{}; U32 ref{},source{},weapon{},base{}; };
'''+sample+functions+'''
template<size_t N,class T> void Put(std::array<unsigned char,N>& a,size_t n,const T& value){std::memcpy(a.data()+n,&value,sizeof(value));}
void FormBytes(unsigned char* p,U32 id,unsigned char type){p[4]=type;std::memcpy(p+12,&id,4);}
int main(){
 std::array<unsigned char,0x120> projectile{}; std::array<unsigned char,0x30> impact{};
 std::array<unsigned char,16> base{},weapon{},source{},target{};
 FormBytes(projectile.data(),0xFF001234,0x3D); FormBytes(base.data(),0xB000806,0x33);
 FormBytes(weapon.data(),0xE3778,0x28); FormBytes(source.data(),0x14,0x3B); FormBytes(target.data(),0x104F0A,0x3B);
 const std::uintptr_t table=kVtable; Put(projectile,0,table);
 void* p=base.data();Put(projectile,0x20,p);p=weapon.data();Put(projectile,0xF8,p);p=source.data();Put(projectile,0xFC,p);
 float xyz[3]={1,2,3};std::memcpy(projectile.data()+0x30,xyz,12);float life=1,dist=2;Put(projectile,0xD8,life);Put(projectile,0x110,dist);
 unsigned char impacted=0;Put(projectile,0x90,impacted);void* first=impact.data();void* next=nullptr;Put(projectile,0x88,first);Put(projectile,0x8C,next);
 float point[3]={4,5,6};std::memcpy(impact.data()+4,point,12);U32 material=2;int region=-1;Put(impact,0x20,material);Put(impact,0x24,region);
 Track t{projectile.data(),0xFF001234,0x14,0xE3778,0xB000806}; unsigned checks=0;
 auto Check=[&](bool ok){++checks;assert(ok);}; auto ReadNow=[&](){return ReadImpact(t);};
 p=nullptr;Put(impact,0,p);auto s=ReadNow();Check(s.valid==15&&s.targetKind==ImpactTargetKind::World&&!s.target&&s.region==-1);
 p=target.data();Put(impact,0,p);s=ReadNow();Check(s.valid==15&&s.targetKind==ImpactTargetKind::Reference&&s.target==0x104F0A);
 FormBytes(target.data(),0,0x3B);s=ReadNow();Check(s.valid==15&&s.targetKind==ImpactTargetKind::Invalid&&!s.target);
 p=reinterpret_cast<void*>(0xDEAD0000);Put(impact,0,p);s=ReadNow();Check(s.valid==7&&s.targetKind==ImpactTargetKind::Invalid);
 p=target.data();Put(impact,0,p);FormBytes(target.data(),0x104F0A,0x3B);denied=impact.data();s=ReadNow();Check(s.valid==7);denied=nullptr;
 p=nullptr;Put(impact,0,p);denied=impact.data()+4;s=ReadNow();Check(s.valid==7);denied=impact.data()+0x20;s=ReadNow();Check(s.valid==7);denied=impact.data()+0x24;s=ReadNow();Check(s.valid==7);denied=nullptr;
 first=nullptr;Put(projectile,0x88,first);s=ReadNow();Check(s.valid==7);first=impact.data();Put(projectile,0x88,first);
 next=impact.data();Put(projectile,0x8C,next);p=nullptr;Put(impact,0,p);s=ReadNow();Check(s.valid==15&&s.more&&s.targetKind==ImpactTargetKind::World);
 Check(ClassifyImpactTarget(nullptr,1)==ImpactTargetKind::Invalid);
 printf("{\\"checks\\":%u,\\"actual_readimpact_body\\":true,\\"world_requires_null_pointer\\":true,\\"nonnull_zero_id_invalid\\":true,\\"game_loaded\\":false}\\n",checks);
}
'''

def capture_source():
    assert sha(CAP)==CAP_SHA
    physics=(CORE/'src/FlightPhysics.cpp').read_text(); impact=(CORE/'src/FlightImpact.inl').read_text()
    types=physics[physics.index('struct Vec {'):physics.index('struct Track {')]
    track=physics[physics.index('struct Track {'):physics.index('Track gTracks')]
    math=physics[physics.index('double Cd('):physics.index('#include "FlightImpact.inl"')]
    model=(CORE/'src/FlightImpactModel.inl').read_text();speed=(CORE/'src/FlightContactSpeed.inl').read_text()
    indexed={}
    for n,line in enumerate(CAP.read_text().splitlines(),1):
        tag=line.split(' ',1)[0];d=dict(re.findall(r'(\w+)=([^\s]+)',line))
        if tag in ['IMPACT_STEP','IMPACT_GEOMETRY','IMPACT_VELOCITY','IMPACT_TERRAIN']:
            indexed.setdefault(int(d['lifetime']),{})[tag]=(d,n)
    cases=[]
    for life in range(1,7):
        rows=indexed[life];s,_=rows['IMPACT_STEP'];g,_=rows['IMPACT_GEOMETRY'];v,_=rows['IMPACT_VELOCITY'];terrain,_=rows['IMPACT_TERRAIN']
        c=['{ ImpactRecord r{}; Track t{};']
        c.append(f'r.serial={life}; r.step={s["step"]}; r.wrote={s["applied"]}; r.baselineVerified={s["baseline_verified"]}; r.resetObserved=true; r.dt={s["dt_s"]}; r.tolerance={g["tolerance"]};')
        c.append(f'r.start={vec(g["start"])};r.expected={vec(g["expected"])};r.before={vec(v["before"])};r.full={vec(v["proposed_full"])};r.bc={v["bc"]};r.dragModel={v["drag_model"]};')
        c.append(f'r.collision.valid=31;r.collision.policyRead=true;r.collision.flags=0x{s["flags"] if "flags" in s else terrain["flags"]};r.collision.target=0x{s["target"]};r.collision.region={s["region"]};r.collision.more=false;')
        for field,key in [('position','position'),('point','contact'),('accounting','accounting_delta')]:c.append(f'r.collision.{field}={vec(g[key])};')
        c.append(f'r.terrain.samples={terrain["samples"]};r.terrain.valid={terrain["valid"]};r.terrain.queryOk={terrain["query_ok"]};r.terrain.position={vec(terrain["candidate"])};r.terrain.floor={terrain["floor"]};r.terrain.target=0x{terrain["target"]};r.terrain.region={terrain["region"]};r.terrain.flags=0x{terrain["flags"]};r.terrain.point={vec(terrain["contact"])};')
        c.append(f't.dragModel=r.dragModel;t.ballisticCoefficient=r.bc;gConfig={{{v["units_per_metre"]},{v["gravity"]},{v["density"]},{v["sound"]}}};')
        c.append('r.collision.targetKind=r.collision.target?ImpactTargetKind::Reference:ImpactTargetKind::Invalid;r.terrain.targetKind=r.collision.targetKind;auto historical=EvaluateContactSpeed(r,t);')
        c.append('auto prospective=r;if(!prospective.collision.target&&prospective.collision.region==-1){prospective.collision.targetKind=ImpactTargetKind::World;prospective.terrain.targetKind=ImpactTargetKind::World;}auto world=EvaluateContactSpeed(prospective,t);')
        c.append('auto invalid=prospective;invalid.collision.targetKind=ImpactTargetKind::Invalid;invalid.terrain.targetKind=ImpactTargetKind::Invalid;auto rejected=EvaluateContactSpeed(invalid,t);')
        c.append(f'''printf("{{\\"shot\\":{life},\\"recorded_target\\":\\"{s['target']}\\",\\"historical_kind_ambiguous\\":%d,\\"historical_available\\":%d,\\"prospective_available\\":%d,\\"prospective_status\\":\\"%s\\",\\"terrain_explained\\":%d,\\"invalid_classification_available\\":%d}}\\n",!r.collision.target,historical.available,world.available,world.status,world.terrainExplained,rejected.available);''')
        c.append(f'Check(historical.available=={1 if int(s["target"],16) else 0},"historical ambiguity retained");')
        c.append(f'Check(world.available==1,"prospective shot available");Check(!rejected.available,"invalid zero-id rejected");Check(world.terrainExplained=={1 if life in [2,3] else 0},"terrain classification");}}')
        cases.append('\n'.join(c))
    header='''#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include "FlightDragData.hpp"
#include "FlightPhysics.hpp"
using U32=std::uint32_t;using U64=unsigned long long;using DWORD=std::uint32_t;unsigned checks=0;
void Check(bool ok,const char* label){++checks;if(!ok){fprintf(stderr,"FAIL:%s\\n",label);exit(1);}}
'''
    record='''struct ImpactSample { unsigned valid{};U32 target{},material{};ImpactTargetKind targetKind{ImpactTargetKind::Invalid};int region{-1};bool more{},policyRead{};U32 flags{};unsigned char impacted{};float life{},distance{};Vec position{},point{},accounting{};};
struct ImpactRecord { U64 serial{};U32 ref{},source{},weapon{},ammo{},base{};unsigned step{},dragModel{};bool collisionCaptured{},callbackReported{},wrote{},baselineVerified{},resetObserved{},modelCandidate{};double modelTime{},modelSpeed{};const char* modelStatus{"no_collision_sample"};bool speedAvailable{},speedEngineSegment{};double speedLow{},speedHigh{},speedMean{};const char* speedStatus{"no_collision_sample"};ContactTerrain terrain{};Vec start{},expected{},before{},full{};double dt{},bc{},tolerance{};ImpactSample collision{};};
'''
    return header+types+track+math+record+model+speed+'\nint main(){\n'+'\n'.join(cases)+'\nprintf("{\\"checks\\":%u,\\"capture_sha256\\":\\"'+CAP_SHA+'\\",\\"historical_pointer_kind_logged\\":false,\\"prospective_fixture\\":true,\\"game_loaded\\":false}\\n",checks);}\n'

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    reader=run('reader_checks',reader_source());capture=run('capture_replay',capture_source())
    assert reader[-1]['checks']==11 and capture[-1]['checks']==24
    result=dict(packet='3U1',capture_sha256=CAP_SHA,reader=reader[-1],capture_rows=capture[:-1],capture_checks=capture[-1],
      historical_world_classification='ambiguous and unavailable',prospective_all_contacts_available=sum(x['prospective_available'] for x in capture[:-1]),
      prospective_anonymous_world_contacts_available=sum(x['prospective_available'] for x in capture[:-1] if x['recorded_target']=='00000000'),
      prospective_terrain_clamps=sum(x['terrain_explained'] for x in capture[:-1]),damage_authority=False,dll_or_game_loaded=False,
      source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [CORE/'src/FlightImpact.inl',CORE/'src/FlightContactSpeed.inl',CORE/'src/FlightImpactJoin.inl',CORE/'src/FlightPhysics.cpp',PYTHON_SOURCE]},
      harness_sha256={'reader':sha(BUILD/'reader_checks.cpp'),'capture':sha(BUILD/'capture_replay.cpp')})
    save(OUT/'OFFLINE-RESULT.json',result);save(OUT/'REPLAY-ROWS.json',capture[:-1])
    print(json.dumps({k:v for k,v in result.items() if k not in ['capture_rows','source_sha256','harness_sha256']},indent=2))
if __name__=='__main__':main()

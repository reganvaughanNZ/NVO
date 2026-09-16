#include <cmath>
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
struct Vec { double x{}, y{}, z{}; };
Vec Add(Vec a, Vec b) noexcept { return {a.x+b.x,a.y+b.y,a.z+b.z}; }
Vec Mul(Vec a, double b) noexcept { return {a.x*b,a.y*b,a.z*b}; }
double Length(Vec a) noexcept { return std::sqrt(a.x*a.x+a.y*a.y+a.z*a.z); }
struct Config { double units{}, gravity{}, density{}, sound{}; } gConfig;
struct Track {
    void* p{}; U64 serial{}; U32 ref{}, source{}, weapon{}, base{}, ammo{};
    unsigned profile{}, steps{}, movementEntries{}, accountingEntries{}, missingRouteReported{};
    unsigned dragModel{};
    double ballisticCoefficient{};
    Vec velocity{};
    double baseline{}, elapsed{};
    float life{-1}, distance{-1};
    bool stopped{}, logged{}, baselineVerified{}, pending{}, wrote{};
    unsigned verifiedSteps{};
    std::uintptr_t frame{};
    DWORD thread{};
    Vec expected{}, startPos{}, proposedVelocity{};
    double pendingDt{}, pendingBaseline{};
    Vec submitted{};
    unsigned commitEntries{}, nodeEntries{};
    unsigned controllerEntries{}, controllerReturns{};
    void* controller{};
    std::uintptr_t controllerFrame{}, controllerArgs{}, controllerState{}, controllerTarget{};
    bool controllerPending{};
    unsigned resetEntries{}, resetPreserved{};
    bool stepResetObserved{};
    bool terrainAdjusted{};
};
double Cd(double mach, unsigned dragModel) noexcept
{
    const auto* table = dragModel == 7 ? nvo::physics::data::G7 : nvo::physics::data::G1;
    const double index = mach*10;
    if (index >= 50) return table[50];
    const unsigned i = static_cast<unsigned>(index);
    return table[i]+(table[i+1]-table[i])*(index-i);
}
Vec Acceleration(Vec v, const Track& profile) noexcept
{
    const double speed=Length(v);
    // BallistX mass/area/sectional-density equation, algebraically reduced to BC.
    constexpr double coefficient = 3.14159265358979323846*0.0254*0.0254/(8*0.45359237);
    const double drag=gConfig.density*coefficient/profile.ballisticCoefficient*Cd(speed/gConfig.sound,profile.dragModel)*speed;
    auto a=Mul(v,-drag); a.z-=gConfig.gravity; return a;
}
Vec Integrate(Vec& v, double dt, const Track& profile) noexcept
{
    Vec displacement{};
    const unsigned count=static_cast<unsigned>(std::ceil(dt*240));
    const double h=dt/count;
    for (unsigned i=0;i<count;++i) {
        const Vec a1=Acceleration(v,profile), v2=Add(v,Mul(a1,h/2));
        const Vec a2=Acceleration(v2,profile), v3=Add(v,Mul(a2,h/2));
        const Vec a3=Acceleration(v3,profile), v4=Add(v,Mul(a3,h));
        const Vec a4=Acceleration(v4,profile);
        displacement=Add(displacement,Mul(Add(Add(v,Mul(v2,2)),Add(Mul(v3,2),v4)),h/6));
        v=Add(v,Mul(Add(Add(a1,Mul(a2,2)),Add(Mul(a3,2),a4)),h/6));
    }
    return displacement;
}

// Included inside FlightPhysics.cpp's private namespace, after Integrate.
// Read-only diagnostics: the only mutations are this module's cache/counters.
// No impact estimate is exposed as damage authority or written into Track.
struct ImpactSample {
    unsigned valid{};
    U32 target{}, material{};
    int region{-1};
    bool more{};
    unsigned char impacted{};
    float life{}, distance{};
    Vec position{}, point{}, accounting{};
};
struct ImpactRecord {
    U64 serial{};
    U32 ref{}, source{}, weapon{}, ammo{}, base{};
    unsigned step{}, dragModel{};
    bool collisionCaptured{}, callbackReported{}, wrote{}, baselineVerified{};
    Vec start{}, expected{}, before{}, full{};
    double dt{}, bc{}, tolerance{};
    ImpactSample collision{};
};
#include "FlightImpactModel.inl"

constexpr unsigned kImpactLives=32;
ImpactRecord gImpactRecords[kImpactLives]{};
unsigned gImpactAdmitted{},gImpactOmitted{},gImpactBaselineContacts{};
unsigned gImpactObserved{}, gImpactCandidates{}, gImpactUnavailable{}, gImpactReadFailures{};
unsigned gImpactCallbacks{}, gImpactCorrelated{}, gImpactUnpaired{}, gImpactLogFailures{};
unsigned gImpactDuplicateCollisions{}, gImpactDuplicateCallbacks{}, gImpactDestroyWithoutCallback{};

ImpactSample fixture{};
ImpactSample ReadImpact(const Track&,const float* =nullptr) noexcept { return fixture; }
void ImpactReset() noexcept
{
    for (auto& r:gImpactRecords) r={};
    gImpactAdmitted=gImpactOmitted=gImpactBaselineContacts=0;
    gImpactObserved=gImpactCandidates=gImpactUnavailable=gImpactReadFailures=0;
    gImpactCallbacks=gImpactCorrelated=gImpactUnpaired=gImpactLogFailures=0;
    gImpactDuplicateCollisions=gImpactDuplicateCallbacks=gImpactDestroyWithoutCallback=0;
}
ImpactRecord* ImpactFind(U64 serial) noexcept
{
    for (auto& r:gImpactRecords) if (r.serial==serial) return &r;
    return nullptr;
}
void ImpactEnroll(const Track& t) noexcept
{
    // Independent of first-eight per-frame logs. Retain admitted slots until
    // load reset so late duplicate callbacks cannot reuse an empty slot.
    if (gImpactAdmitted==kImpactLives) { ++gImpactOmitted; return; }
    auto& r=gImpactRecords[gImpactAdmitted++]; r.serial=t.serial;
}
void ImpactCollision(const Track& t,const float* delta) noexcept
{
    // Caller already holds the physics lock and checked stack, thread and
    // movement/accounting pairing. Retain only the first collision per life.
    auto* record=ImpactFind(t.serial);
    if (!record) return;
    if (record->collisionCaptured) { ++gImpactDuplicateCollisions; return; }
    auto& r=*record;
    r.collisionCaptured=true;
    r.serial=t.serial; r.ref=t.ref; r.source=t.source; r.weapon=t.weapon; r.ammo=t.ammo; r.base=t.base;
    r.step=t.steps; r.dragModel=t.dragModel; r.wrote=t.wrote; r.baselineVerified=t.baselineVerified;
    r.start=t.startPos; r.expected=t.expected; r.before=t.wrote?t.velocity:t.proposedVelocity;
    r.full=t.proposedVelocity; r.dt=t.pendingDt; r.bc=t.ballisticCoefficient;
    const double coordinate=std::fmax(std::fmax(std::abs(r.start.x),std::abs(r.start.y)),std::abs(r.start.z));
    r.tolerance=0.002+coordinate*0.0000005+Length(r.expected)*0.00002;
    r.collision=ReadImpact(t,delta); ++gImpactObserved;
    const auto& s=r.collision;
    if (s.valid!=31) ++gImpactReadFailures;
    if (!r.wrote || !r.baselineVerified) ++gImpactBaselineContacts;
    const auto m=EvaluateImpact(r,t);
    if (m.estimate) ++gImpactCandidates; else ++gImpactUnavailable;
    if (!nvo::log::Write("IMPACT_STEP session=%u lifetime=%llu step=%u projectile=%08X source=%08X weapon=%08X ammo=%08X base=%08X target=%08X region=%d material=%u valid_mask=%u more_contacts=%u impacted=%u applied=%u baseline_verified=%u dt_s=%.9g speed_before_mps=%.9g proposed_full_step_mps=%.9g life_s=%.9g travel_units=%.9g observer_writes=0",
        gSession,r.serial,r.step,r.ref,r.source,r.weapon,r.ammo,r.base,s.target,s.region,s.material,s.valid,s.more?1u:0u,
        static_cast<unsigned>(s.impacted),r.wrote?1u:0u,r.baselineVerified?1u:0u,r.dt,Length(r.before),Length(r.full),
        static_cast<double>(s.life),static_cast<double>(s.distance))) ++gImpactLogFailures;
    if (!nvo::log::Write("IMPACT_GEOMETRY session=%u lifetime=%llu step=%u start=(%.9g,%.9g,%.9g) expected=(%.9g,%.9g,%.9g) position=(%.9g,%.9g,%.9g) contact=(%.9g,%.9g,%.9g) accounting_delta=(%.9g,%.9g,%.9g) tolerance=%.9g observer_writes=0",
        gSession,r.serial,r.step,r.start.x,r.start.y,r.start.z,r.expected.x,r.expected.y,r.expected.z,s.position.x,s.position.y,s.position.z,
        s.point.x,s.point.y,s.point.z,s.accounting.x,s.accounting.y,s.accounting.z,r.tolerance)) ++gImpactLogFailures;
    if (!nvo::log::Write("IMPACT_VELOCITY session=%u lifetime=%llu step=%u before=(%.9g,%.9g,%.9g) proposed_full=(%.9g,%.9g,%.9g) drag_model=%u bc=%.9g gravity=%.9g density=%.9g sound=%.9g units_per_metre=%.9g units_calibrated=0 observer_writes=0",
        gSession,r.serial,r.step,r.before.x,r.before.y,r.before.z,r.full.x,r.full.y,r.full.z,r.dragModel,r.bc,gConfig.gravity,gConfig.density,gConfig.sound,gConfig.units)) ++gImpactLogFailures;
    if (!nvo::log::Write("IMPACT_MODEL session=%u lifetime=%llu step=%u status=%s geometry_valid=%u chord_fraction=%.9g off_chord_units=%.9g position_contact_gap=%.9g candidate_valid=%u candidate_time_s=%.9g candidate_speed_mps=%.9g model_contact_gap=%.9g contact_time_measured=0 speed_authority=0 damage_replacement=0 observer_writes=0",
        gSession,r.serial,r.step,m.status,m.geometry?1u:0u,m.fraction,m.offChord,m.pointGap,m.estimate?1u:0u,m.estimateTime,m.estimateSpeed,m.modelGap)) ++gImpactLogFailures;
    if (!nvo::log::Write("IMPACT_BOUNDARY session=%u lifetime=%llu step=%u endpoint_matches=%u accounting_matches=%u endpoint_error=%.9g accounting_error=%.9g tolerance=%.9g endpoint_kind=full_step contact_kind=first_collision observer_writes=0",
        gSession,r.serial,r.step,m.endpointMatches?1u:0u,m.accountingMatches?1u:0u,m.endpointError,m.accountingError,r.tolerance)) ++gImpactLogFailures;
}
void ImpactEvent(const Track& t,bool destroyed) noexcept
{
    // Called synchronously for the same p/serial, before existing retirement.
    auto* r=ImpactFind(t.serial);
    if (!r) return;
    if (destroyed) {
        if (r->collisionCaptured && !r->callbackReported) {
            ++gImpactDestroyWithoutCallback;
            if (!nvo::log::Write("IMPACT_END session=%u lifetime=%llu collision_without_impact_callback=1 observer_writes=0",gSession,t.serial)) ++gImpactLogFailures;
        }
        return;
    }
    if (r->callbackReported) { ++gImpactDuplicateCallbacks; return; }
    r->callbackReported=true;
    ++gImpactCallbacks;
    if (!r->collisionCaptured) {
        ++gImpactUnpaired;
        if (!nvo::log::Write("IMPACT_CALLBACK session=%u lifetime=%llu status=no_collision_sample target=unknown contact_time_measured=0 speed_authority=0 observer_writes=0",gSession,t.serial)) ++gImpactLogFailures;
        return;
    }
    const auto s=ReadImpact(t);
    if (s.valid!=15) ++gImpactReadFailures;
    const double contactGap=Length(Add(s.point,Mul(r->collision.point,-1)));
    const bool correlated=s.valid==15 && r->collision.valid==31 && !s.more && !r->collision.more
        && s.target==r->collision.target && s.region==r->collision.region && contactGap<=r->tolerance;
    if (correlated) ++gImpactCorrelated; else ++gImpactUnpaired;
    if (!nvo::log::Write("IMPACT_CALLBACK session=%u lifetime=%llu step=%u status=%s valid_mask=%u target=%08X region=%d contact=(%.9g,%.9g,%.9g) position=(%.9g,%.9g,%.9g) life_s=%.9g travel_units=%.9g contact_change_units=%.9g age_since_collision_s=%.9g contact_time_measured=0 speed_authority=0 observer_writes=0",
        gSession,t.serial,r->step,correlated?"correlated":"contact_changed_or_unavailable",s.valid,s.target,s.region,
        s.point.x,s.point.y,s.point.z,s.position.x,s.position.y,s.position.z,static_cast<double>(s.life),static_cast<double>(s.distance),
        contactGap,static_cast<double>(s.life)-r->collision.life)) ++gImpactLogFailures;
}
void ImpactFinish(const char* reason) noexcept
{
    nvo::log::Write("IMPACT_SUMMARY session=%u reason=%s collision_samples=%u model_candidates=%u unavailable_candidates=%u optional_read_failures=%u impact_callbacks=%u correlated_callbacks=%u unpaired_callbacks=%u duplicate_collisions=%u duplicate_callbacks=%u destroy_without_callback=%u log_write_failures=%u max_lifetimes=%u speed_authority=0 damage_replacement=0 observer_writes=0",
        gSession,reason,gImpactObserved,gImpactCandidates,gImpactUnavailable,gImpactReadFailures,gImpactCallbacks,gImpactCorrelated,gImpactUnpaired,
        gImpactDuplicateCollisions,gImpactDuplicateCallbacks,gImpactDestroyWithoutCallback,gImpactLogFailures,kImpactLives);
    nvo::log::Write("IMPACT_COVERAGE_SUMMARY session=%u reason=%s admitted_lifetimes=%u omitted_lifetimes=%u baseline_contacts=%u max_lifetimes=%u max_extra_detail_rows=224 speed_authority=0 observer_writes=0",
        gSession,reason,gImpactAdmitted,gImpactOmitted,gImpactBaselineContacts,kImpactLives);
    ImpactReset();
}

int main() { ImpactRecord seed{}; Track seedTrack{};
{ ImpactRecord r{}; Track t{};
r.serial=1;
r.step=0;
r.ref=0xFF001994;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=0; r.baselineVerified=0; r.dt=0.0310000014; r.tolerance=0.0725994371;
r.start={-67438.75,4600.65967,8465.75586};
r.expected={-1836.59287,-164.137602,18.2463753};
r.before={-846.356125,-75.6394446,8.40846749}; r.full={-846.356125,-75.6394446,8.40846749};
r.bc=0.209; r.dragModel=7;
r.collision.position={-69275.3438,4436.52197,8484.00195};
r.collision.point={-67462.7344,4598.52197,8465.99316};
r.collision.accounting={-1836.59375,-164.137695,18.2460938};
r.collision.valid=31; r.collision.target=0x001055E0; r.collision.region=-1;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(r.serial<=2) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15; ImpactEvent(t,false); ImpactEvent(t,true);
}{ ImpactRecord r{}; Track t{};
r.serial=2;
r.step=0;
r.ref=0xFF001994;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=0; r.baselineVerified=0; r.dt=0.0150000006; r.tolerance=0.0528937582;
r.start={-66097.1328,1722.63623,8486.63184};
r.expected={-341.498027,-823.743455,-30.8705635};
r.before={-325.236204,-784.517545,-29.4005355}; r.full={-325.236204,-784.517545,-29.4005355};
r.bc=0.209; r.dragModel=7;
r.collision.position={-66438.6328,898.8927,8455.76074};
r.collision.point={-66375.4141,1051.36609,8461.33594};
r.collision.accounting={-341.5,-823.74353,-30.8710938};
r.collision.valid=31; r.collision.target=0xFF001978; r.collision.region=0;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(r.serial<=2) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15; ImpactEvent(t,false); ImpactEvent(t,true);
}{ ImpactRecord r{}; Track t{};
r.serial=3;
r.step=7;
r.ref=0xFF001994;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=1; r.baselineVerified=1; r.dt=0.0310000014; r.tolerance=0.0689800017;
r.start={-67391.9141,-2018.77185,8317.31934};
r.expected={-518.065693,-1579.09901,-87.3116117};
r.before={-241.387376,-735.764928,-40.5293814}; r.full={-236.122423,-719.716997,-39.9460714};
r.bc=0.209; r.dragModel=7;
r.collision.position={-67909.9766,-3597.87085,8230.00781};
r.collision.point={-67429.8516,-2134.49072,8310.88574};
r.collision.accounting={-518.0625,-1579.099,-87.3115234};
r.collision.valid=31; r.collision.target=0x001070C1; r.collision.region=-1;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(r.serial<=2) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15; ImpactEvent(t,false); ImpactEvent(t,true);
}{ ImpactRecord r{}; Track t{};
r.serial=4;
r.step=7;
r.ref=0xFF001994;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=1; r.baselineVerified=1; r.dt=0.0160000008; r.tolerance=0.0529499464;
r.start={-67358.9766,-2028.60583,8305.82129};
r.expected={-265.270052,-820.442034,-46.6741942};
r.before={-238.204056,-736.730809,-41.8333366}; r.full={-235.500378,-728.368722,-41.5145324};
r.bc=0.209; r.dragModel=7;
r.collision.position={-67624.2422,-2849.04785,8259.14746};
r.collision.point={-67392.3906,-2132.0376,8299.93164};
r.collision.accounting={-265.265625,-820.442017,-46.6738281};
r.collision.valid=31; r.collision.target=0x001070C1; r.collision.region=-1;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(r.serial<=2) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15; ImpactEvent(t,false); ImpactEvent(t,true);
}{ ImpactRecord r{}; Track t{};
r.serial=5;
r.step=4;
r.ref=0xFF001994;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=1; r.baselineVerified=1; r.dt=0.0150000006; r.tolerance=0.0520852329;
r.start={-66294.6953,1301.73523,8490.62793};
r.expected={-262.211824,-803.988073,-45.5854384};
r.before={-251.098486,-769.912601,-43.5797035}; r.full={-248.360238,-761.516646,-43.2507606};
r.bc=0.209; r.dragModel=7;
r.collision.position={-66556.9141,497.747284,8445.04199};
r.collision.point={-66373.5625,1059.90808,8476.93066};
r.collision.accounting={-262.21875,-803.987915,-45.5859375};
r.collision.valid=31; r.collision.target=0xFF001978; r.collision.region=1;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(r.serial<=2) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15; ImpactEvent(t,false); ImpactEvent(t,true);
}{ ImpactRecord r{}; Track t{};
r.serial=6;
r.step=7;
r.ref=0xFF001994;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=1; r.baselineVerified=1; r.dt=0.0310000014; r.tolerance=0.0689933665;
r.start={-67418.6641,-2093.88477,8315.07324};
r.expected={-518.547227,-1578.95873,-86.9797441};
r.before={-241.611741,-735.699564,-40.3747511}; r.full={-236.341895,-719.653061,-39.7948139};
r.bc=0.209; r.dragModel=7;
r.collision.position={-67937.2188,-3672.84326,8228.09277};
r.collision.point={-67432.2109,-2135.19482,8312.76172};
r.collision.accounting={-518.554688,-1578.9585,-86.9804688};
r.collision.valid=31; r.collision.target=0x001070C1; r.collision.region=-1;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(r.serial<=2) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15; ImpactEvent(t,false); ImpactEvent(t,true);
}{ ImpactRecord r{}; Track t{};
r.serial=7;
r.step=7;
r.ref=0xFF001994;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=1; r.baselineVerified=1; r.dt=0.0160000008; r.tolerance=0.0529671056;
r.start={-67393.1484,-2100.13965,8277.76855};
r.expected={-266.273389,-819.984696,-49.0072835};
r.before={-239.105024,-736.320144,-43.928377}; r.full={-236.391113,-727.962699,-43.5857925};
r.bc=0.209; r.dragModel=7;
r.collision.position={-67659.4219,-2920.12427,8228.76172};
r.collision.point={-67402.3828,-2128.67383,8276.05762};
r.collision.accounting={-266.273438,-819.984619,-49.0068359};
r.collision.valid=31; r.collision.target=0x001070C1; r.collision.region=-1;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(r.serial<=2) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15; ImpactEvent(t,false); ImpactEvent(t,true);
}{ ImpactRecord r{}; Track t{};
r.serial=8;
r.step=7;
r.ref=0xFF001994;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=1; r.baselineVerified=1; r.dt=0.0150000006; r.tolerance=0.0518996904;
r.start={-67405.8828,-2098.2959,8319.30469};
r.expected={-251.058881,-768.802832,-41.813128};
r.before={-240.38687,-736.12256,-39.962054}; r.full={-237.827546,-728.285293,-39.6829066};
r.bc=0.209; r.dragModel=7;
r.collision.position={-67656.9453,-2867.09888,8277.49219};
r.collision.point={-67418.7812,-2137.8623,8317.11719};
r.collision.accounting={-251.0625,-768.802979,-41.8125};
r.collision.valid=31; r.collision.target=0x001070C1; r.collision.region=-1;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(r.serial<=2) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15; ImpactEvent(t,false); ImpactEvent(t,true);
}
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
puts("{\"negative_guards\":7,\"later_lifetimes_through\":32,\"omitted\":2,\"cache_lifecycle_checks\":true,\"game_loaded\":false}");
}

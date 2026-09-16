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
#include "FlightPhysics.hpp"
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
    bool modelCandidate{};
    double modelTime{},modelSpeed{};
    const char* modelStatus{"no_collision_sample"};
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
void ResetImpactHits() noexcept;

ImpactSample fixture{};
ImpactSample ReadImpact(const Track&,const float* =nullptr) noexcept { return fixture; }
void ImpactReset() noexcept
{
    ResetImpactHits();
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
    r.modelCandidate=m.estimate; r.modelStatus=m.status;
    r.modelTime=m.estimate?m.estimateTime:0; r.modelSpeed=m.estimate?m.estimateSpeed:0;
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
        const auto early=ReadImpact(t);
        if (early.valid!=15) ++gImpactReadFailures;
        const bool immediate=early.valid==15 && !early.more && !t.movementEntries && !t.accountingEntries;
        if (!nvo::log::Write("IMPACT_CALLBACK session=%u lifetime=%llu status=%s valid_mask=%u target=%08X region=%d movement_entries=%u accounting_entries=%u contact_time_measured=0 speed_authority=0 observer_writes=0",
            gSession,t.serial,immediate?"pre_movement_contact":"no_collision_sample",early.valid,early.target,early.region,t.movementEntries,t.accountingEntries)) ++gImpactLogFailures;
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
#include "FlightImpactJoin.inl"

void ImpactFinish(const char* reason) noexcept
{
    SummarizeImpactHits(reason);
    nvo::log::Write("IMPACT_SUMMARY session=%u reason=%s collision_samples=%u model_candidates=%u unavailable_candidates=%u optional_read_failures=%u impact_callbacks=%u correlated_callbacks=%u unpaired_callbacks=%u duplicate_collisions=%u duplicate_callbacks=%u destroy_without_callback=%u log_write_failures=%u max_lifetimes=%u speed_authority=0 damage_replacement=0 observer_writes=0",
        gSession,reason,gImpactObserved,gImpactCandidates,gImpactUnavailable,gImpactReadFailures,gImpactCallbacks,gImpactCorrelated,gImpactUnpaired,
        gImpactDuplicateCollisions,gImpactDuplicateCallbacks,gImpactDestroyWithoutCallback,gImpactLogFailures,kImpactLives);
    nvo::log::Write("IMPACT_COVERAGE_SUMMARY session=%u reason=%s admitted_lifetimes=%u omitted_lifetimes=%u baseline_contacts=%u max_lifetimes=%u max_extra_detail_rows=416 speed_authority=0 observer_writes=0",
        gSession,reason,gImpactAdmitted,gImpactOmitted,gImpactBaselineContacts,kImpactLives);
    ImpactReset();
}

int main() { ImpactRecord seed{}; Track seedTrack{};
{ ImpactRecord r{}; Track t{};
const int observedHitRegion=1;
r.serial=2;
r.step=5;
r.ref=0xFF001996;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=1; r.baselineVerified=1; r.dt=0.0150000006; r.tolerance=0.0520854894;
r.start={-66295.3594,1288.15259,8474.95312};
r.expected={-263.803831,-803.713268,-40.9391881};
r.before={-252.623015,-769.649433,-39.130375}; r.full={-249.868148,-761.256368,-38.8499534};
r.bc=0.209; r.dragModel=7;
r.collision.position={-66559.1719,484.439362,8434.01367};
r.collision.point={-66371.4688,1056.29651,8463.12207};
r.collision.accounting={-263.8125,-803.713257,-40.9394531};
r.collision.valid=31; r.collision.target=0xFF001978; r.collision.region=0;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(!r.wrote) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15;
nvo::physics::HitQuery q{gSession,static_cast<unsigned>(r.serial),r.serial,r.ref,r.source,r.collision.target,r.weapon,r.ammo,observedHitRegion,0,{}};
const unsigned beforeCandidates=gImpactHitCandidates;
ImpactHit(&t,q); assert(gImpactHitCandidates==beforeCandidates+(m.estimate?1:0));
ImpactEvent(t,false); ImpactEvent(t,true);
}{ ImpactRecord r{}; Track t{};
const int observedHitRegion=0;
r.serial=3;
r.step=4;
r.ref=0xFF001996;
r.source=0x00000014;
r.weapon=0x00004333;
r.ammo=0x0006B53C;
r.base=0x0C000807;
r.wrote=1; r.baselineVerified=1; r.dt=0.0160000008; r.tolerance=0.0532246123;
r.start={-66301.9297,1294.15088,8472.15137};
r.expected={-284.732476,-856.438149,-45.6392468};
r.before={-255.716845,-769.162914,-40.9097777}; r.full={-252.742844,-760.217508,-40.589988};
r.bc=0.209; r.dragModel=7;
r.collision.position={-66586.6562,437.712646,8426.51172};
r.collision.point={-66374.4375,1076.05615,8460.45801};
r.collision.accounting={-284.726562,-856.438232,-45.6396484};
r.collision.valid=31; r.collision.target=0xFF001978; r.collision.region=0;
gConfig={70,9.80665,1.225,340.294};
t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified;
t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
t.ballisticCoefficient=r.bc; t.dragModel=r.dragModel; t.logged=false;
auto m=EvaluateImpact(r,t);
printf("{\"lifetime\":%llu,\"status\":\"%s\",\"candidate\":%d,\"time_s\":%.12g,\"speed_mps\":%.12g,\"model_gap\":%.12g,\"tolerance\":%.12g}\n",r.serial,m.status,m.estimate,m.estimateTime,m.estimateSpeed,m.modelGap,r.tolerance);
if(!r.wrote) assert(!m.estimate && std::string(m.status)=="engine_baseline_contact");
if(m.estimate) { assert(m.estimateTime>=0 && m.estimateTime<=r.dt);
assert(m.estimateSpeed<=Length(r.before) && m.estimateSpeed>=Length(r.full)); seed=r; seedTrack=t; }
ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
fixture.position=fixture.point; fixture.valid=15;
nvo::physics::HitQuery q{gSession,static_cast<unsigned>(r.serial),r.serial,r.ref,r.source,r.collision.target,r.weapon,r.ammo,observedHitRegion,0,{}};
const unsigned beforeCandidates=gImpactHitCandidates;
ImpactHit(&t,q); assert(gImpactHitCandidates==beforeCandidates+(m.estimate?1:0));
ImpactEvent(t,false); ImpactEvent(t,true);
}
assert(seed.serial && gImpactObserved==2 && gImpactCorrelated==2 && gImpactBaselineContacts==0);
auto bad=seed; bad.collision.position.x+=10; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.collision.accounting.y+=10; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.collision.point.z+=10; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.collision.more=true; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.collision.valid=15; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.dt=0; assert(!EvaluateImpact(bad,seedTrack).estimate);
bad=seed; bad.before=Mul(seed.before,-1); assert(!EvaluateImpact(bad,seedTrack).estimate);
for(U64 serial=10;serial<=41;++serial) {
seedTrack.serial=serial; ImpactEnroll(seedTrack); fixture=seed.collision;
ImpactCollision(seedTrack,nullptr); fixture.position=fixture.point; fixture.valid=15;
ImpactEvent(seedTrack,false); ImpactEvent(seedTrack,false); ImpactEvent(seedTrack,true);
}
assert(gImpactAdmitted==32 && gImpactOmitted==2 && gImpactObserved==32);
assert(gImpactCallbacks==32 && gImpactCorrelated==32 && gImpactDuplicateCallbacks==30);
assert(gImpactUnpaired==0 && gImpactDestroyWithoutCallback==0);
ImpactFinish("offline_replay"); assert(gImpactAdmitted==0 && gImpactObserved==0);
assert(!ImpactFind(10));
// Independent reset: callback without collision, duplicate dedup, missing callback.
seedTrack.serial=10; ImpactEnroll(seedTrack); ImpactEvent(seedTrack,false); ImpactEvent(seedTrack,false);
assert(gImpactUnpaired==1 && gImpactDuplicateCallbacks==1);
seedTrack.serial=11; ImpactEnroll(seedTrack); fixture=seed.collision;
ImpactCollision(seedTrack,nullptr); ImpactEvent(seedTrack,true); assert(gImpactDestroyWithoutCallback==1);
ImpactReset();
// Recreate the captured candidate before the later callback, then prove an
// ordinary head/torso disagreement remains diagnostic rather than a veto.
seedTrack.serial=100; ImpactEnroll(seedTrack); fixture=seed.collision;
ImpactCollision(seedTrack,nullptr); fixture.valid=15; fixture.position=fixture.point;
nvo::physics::HitQuery q{gSession,1,100,seedTrack.ref,seedTrack.source,fixture.target,seedTrack.weapon,seedTrack.ammo,1,0,{}};
ImpactHit(&seedTrack,q); assert(gImpactHitCandidates==1 && gImpactHitRegionDifferences==1);
// Wrong identity/target, changed contact, after-callback and no-track queries
// must never expose the earlier valid candidate as available.
auto badQuery=q; badQuery.ammo+=1; ImpactHit(&seedTrack,badQuery); assert(gImpactHitCandidates==1);
badQuery=q; badQuery.target+=1; ImpactHit(&seedTrack,badQuery); assert(gImpactHitCandidates==1);
fixture.point.x+=10; ImpactHit(&seedTrack,q); assert(gImpactHitCandidates==1);
fixture.point.x-=10; ImpactEvent(seedTrack,false); ImpactHit(&seedTrack,q); assert(gImpactHitCandidates==1);
ImpactHit(nullptr,q); assert(gImpactHitCandidates==1);
// Early contact at hit boundary is classified and can carry its actual target
// without inventing a model. Both no-sample and optional-read cases stay unavailable.
seedTrack.serial=101; seedTrack.movementEntries=seedTrack.accountingEntries=0; ImpactEnroll(seedTrack);
q.lifetime=101; ImpactHit(&seedTrack,q); assert(gImpactHitImmediate==1 && gImpactHitCandidates==1);
fixture.valid=0; ImpactHit(&seedTrack,q); assert(gImpactHitReads==1);
fixture.valid=15; fixture.more=true; ImpactHit(&seedTrack,q); assert(gImpactHitCandidates==1); fixture.more=false;
for(unsigned i=0;i<64;++i) ImpactHit(nullptr,q);
assert(gImpactHitSeen==64 && gImpactHitOmitted==9);
ResetImpactHits(); assert(gImpactHitSeen==0 && gImpactHitCandidates==0);
ImpactReset(); for(const auto& row:nvo::log::rows) assert(row.size()<767);

puts("{\"negative_guards\":7,\"admitted_lifetimes\":32,\"omitted\":2,\"cache_and_join_checks\":true,\"game_loaded\":false}");
}

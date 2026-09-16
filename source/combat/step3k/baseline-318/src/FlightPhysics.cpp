#include "FlightPhysics.hpp"
#include "FlightDragData.hpp"
#include "CurrentHit.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwchar>

namespace {
using U32 = std::uint32_t;
using U64 = unsigned long long;
constexpr std::uintptr_t kSite = 0x9BF461, kOriginal = 0x9C4E60, kVtable = 0x108FA44;
constexpr std::uintptr_t kMoveSite = 0x9BF411, kMoveOriginal = 0x92F260;
constexpr std::uintptr_t kCommitSite = 0x930475, kCommitOriginal = 0x575830;
constexpr std::uintptr_t kNodeSite = 0x92F5DC, kNodeOriginal = 0x440460;
constexpr std::uintptr_t kDispatchSite = 0x92FFEA;
constexpr std::uintptr_t kDirectSite = 0x92FFD4, kDirectOriginal = 0xC70B60;
constexpr std::uintptr_t kAfterControllerSite = 0x92FFFB, kAfterControllerOriginal = 0x9304B0;
constexpr std::uintptr_t kLocalZSite = 0xC73517, kControllerTarget = 0xC73170;
constexpr std::uintptr_t kControllerVtable = 0x1090594;
constexpr std::uintptr_t kTerrainSite = 0x930150, kTerrainOriginal = 0x4572E0;
constexpr unsigned kCapacity = 128, kLoggedLives = 8, kLoggedSteps = 64;
SRWLOCK gLock = SRWLOCK_INIT;
struct Lock { Lock() noexcept { AcquireSRWLockExclusive(&gLock); } ~Lock() { ReleaseSRWLockExclusive(&gLock); } };
struct ErrorGuard { DWORD old = GetLastError(); ~ErrorGuard() { SetLastError(old); } };
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
Track gTracks[kCapacity]{};
std::atomic<bool> gActive{false};
bool gInstalled{}, gAttempted{};
unsigned gSession{}, gAccepted{}, gApplied{}, gRejected{}, gOverflow{};
unsigned gMoveEntries{}, gAccountingEntries{}, gMoveUntracked{}, gAccountingUntracked{};
unsigned gMissingRoute{}, gBaselines{}, gVerified{}, gMismatched{}, gUnpaired{};
unsigned gResetEntries{}, gResetPreserved{};
// NVO_3F1_DIAGNOSTICS_BEGIN
constexpr unsigned kFailureReports = 16;
unsigned gFailureReportsWritten{}, gFailureWriteFailures{};
// NVO_3F1_DIAGNOSTICS_END
unsigned gTerrainQueries{}, gTerrainFailed{}, gTerrainCorrected{}, gTerrainVerified{};
unsigned gTerrainCollisionExcluded{}, gTerrainLogFailures{};
unsigned char gTerrainPatch[5]{};
void* gOriginalTerrain = reinterpret_cast<void*>(kTerrainOriginal);
unsigned char gPatch[5]{};
unsigned char gMovePatch[5]{};
unsigned char gCommitPatch[5]{}, gNodePatch[5]{};
unsigned char gDispatchPatch[8]{}, gDirectPatch[5]{}, gAfterControllerPatch[5]{};
unsigned char gLocalZPatch[6]{};
void* gOriginalAccounting = reinterpret_cast<void*>(kOriginal);
void* gOriginalMovement = reinterpret_cast<void*>(kMoveOriginal);
void* gOriginalCommit = reinterpret_cast<void*>(kCommitOriginal);
void* gOriginalNode = reinterpret_cast<void*>(kNodeOriginal);
void* gOriginalDirect = reinterpret_cast<void*>(kDirectOriginal);
void* gOriginalAfterController = reinterpret_cast<void*>(kAfterControllerOriginal);

template<class T> bool Read(const void* p, std::ptrdiff_t offset, T& value) noexcept
{ return p && nvo::hit::ReadBytes(static_cast<const char*>(p)+offset, &value, sizeof(value)); }
bool OnStack(std::uintptr_t p, unsigned bytes) noexcept
{
    const auto* tib = reinterpret_cast<const NT_TIB*>(NtCurrentTeb());
    return p >= reinterpret_cast<std::uintptr_t>(tib->StackLimit)
        && p < reinterpret_cast<std::uintptr_t>(tib->StackBase)
        && bytes <= reinterpret_cast<std::uintptr_t>(tib->StackBase)-p;
}
bool WriteVector(float* p, const float* value) noexcept
{
    // Only the checked caller-owned 12-byte stack argument reaches this function.
    __try { std::memcpy(p, value, sizeof(float)*3); return true; }
    __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
Track* Find(void* p, U64 serial = 0) noexcept
{ for (auto& t : gTracks) if (t.serial && t.p == p && (!serial || t.serial == serial)) return &t; return nullptr; }
void Summary(const Track& t, const char* reason) noexcept
{
    if (t.logged) nvo::log::Write("PHYSICS_SHOT session=%u lifetime=%llu reason=%s movement_entries=%u accounting_entries=%u baseline_verified=%u steps=%u verified_steps=%u pending=%u elapsed_s=%.9g speed_mps=%.9g stopped=%u commit_entries=%u node_entries=%u controller_entries=%u controller_returns=%u controller_pending=%u reset_entries=%u reset_preserved=%u",
        gSession,t.serial,reason,t.movementEntries,t.accountingEntries,t.baselineVerified?1u:0u,t.steps,t.verifiedSteps,t.pending?1u:0u,t.elapsed,Length(t.velocity),t.stopped?1u:0u,t.commitEntries,t.nodeEntries,t.controllerEntries,t.controllerReturns,t.controllerPending?1u:0u,t.resetEntries,t.resetPreserved);
}
void MissingRoute(Track& t, const char* reason) noexcept
{
    if (t.steps || t.missingRouteReported) return;
    t.missingRouteReported=1; ++gMissingRoute;
    if (gMissingRoute<=16) nvo::log::Write("PHYSICS_NO_UPDATE session=%u lifetime=%llu reason=%s movement_entries=%u accounting_entries=%u baseline_verified=%u writes=0",
        gSession,t.serial,reason,t.movementEntries,t.accountingEntries,t.baselineVerified?1u:0u);
}
void Reject(Track& t, const char* reason) noexcept
{
    if (t.stopped) return;
    t.stopped=true; t.pending=false; ++gRejected;
    if (gRejected<=16) nvo::log::Write("PHYSICS_REJECT session=%u lifetime=%llu reason=%s subsequent_engine_movement=unchanged",gSession,t.serial,reason);
}
// NVO_3F1_DIAGNOSTICS_BEGIN
void LogDisplacementFailure(const Track& t, Vec measured, const float* pos,
    const float* returned, float life, float distance, double vectorError,
    double positionError, double tolerance) noexcept
{
    // The caller holds the physics lock. Only validated values already read by
    // BeforeAccounting and our own Track are used; no extra engine dereference.
    // REJECT routes these bounded rows through NativeLog's priority reserve.
    if (gMismatched > kFailureReports) {
        if (gMismatched == kFailureReports+1)
            nvo::log::Write("PHYSICS_REJECT_DETAIL_LIMIT session=%u reports_limit=%u further_failure_details=omitted physics_rules_unchanged=1",gSession,kFailureReports);
        return;
    }
    const Vec position{pos[0],pos[1],pos[2]};
    const Vec positionDelta=Add(position,Mul(t.startPos,-1));
    const Vec residual=Add(positionDelta,Mul(measured,-1));
    const bool metrics=nvo::log::Write("PHYSICS_REJECT_METRICS session=%u lifetime=%llu report=%u step=%u phase=%s projectile=%08X source=%08X weapon=%08X ammo=%08X base=%08X profile=%u vector_error=%.9g position_error=%.9g tolerance=%.9g vector_failed=%u position_failed=%u routine_lifetime_logged=%u routine_step_logged=%u",
        gSession,t.serial,gMismatched,t.steps,t.wrote?"apply":"baseline",t.ref,t.source,t.weapon,t.ammo,t.base,t.profile,
        vectorError,positionError,tolerance,vectorError>tolerance?1u:0u,positionError>tolerance?1u:0u,
        t.logged?1u:0u,t.logged && t.accountingEntries<=kLoggedSteps?1u:0u);
    const bool motion=nvo::log::Write("PHYSICS_REJECT_MOTION session=%u lifetime=%llu report=%u step=%u expected_delta=(%.9g,%.9g,%.9g) actual_delta=(%.9g,%.9g,%.9g) velocity_before_mps=(%.9g,%.9g,%.9g) velocity_proposed_mps=(%.9g,%.9g,%.9g) dt_s=%.9g accepted_elapsed_s=%.9g engine_life_s=%.9g engine_travel_units=%.9g",
        gSession,t.serial,gMismatched,t.steps,t.expected.x,t.expected.y,t.expected.z,measured.x,measured.y,measured.z,
        t.velocity.x,t.velocity.y,t.velocity.z,t.proposedVelocity.x,t.proposedVelocity.y,t.proposedVelocity.z,
        t.pendingDt,t.elapsed,static_cast<double>(life),static_cast<double>(distance));
    const bool positions=nvo::log::Write("PHYSICS_REJECT_POSITION session=%u lifetime=%llu report=%u step=%u start_pos=(%.9g,%.9g,%.9g) end_pos=(%.9g,%.9g,%.9g) position_delta=(%.9g,%.9g,%.9g) position_residual=(%.9g,%.9g,%.9g) observer_writes=0",
        gSession,t.serial,gMismatched,t.steps,t.startPos.x,t.startPos.y,t.startPos.z,position.x,position.y,position.z,
        positionDelta.x,positionDelta.y,positionDelta.z,residual.x,residual.y,residual.z);
    const bool context=nvo::log::Write("PHYSICS_REJECT_CONTEXT session=%u lifetime=%llu report=%u step=%u submitted_local=(%.9g,%.9g,%.9g) returned_local=(%.9g,%.9g,%.9g) movement_entries=%u accounting_entries=%u controller_entries=%u controller_returns=%u commit_entries=%u node_entries=%u reset_observed=%u controller_pending=%u controller_target=%08X controller=%p controller_state=%08X thread=%u contacts_observed=0 impacted_observed=0",
        gSession,t.serial,gMismatched,t.steps,t.submitted.x,t.submitted.y,t.submitted.z,
        static_cast<double>(returned[0]),static_cast<double>(returned[1]),static_cast<double>(returned[2]),
        t.movementEntries,t.accountingEntries,t.controllerEntries,t.controllerReturns,t.commitEntries,t.nodeEntries,
        t.stepResetObserved?1u:0u,t.controllerPending?1u:0u,static_cast<U32>(t.controllerTarget),t.controller,
        static_cast<U32>(t.controllerState),static_cast<unsigned>(t.thread));
    if (metrics && motion && positions && context) ++gFailureReportsWritten;
    else ++gFailureWriteFailures;
}
// NVO_3F1_DIAGNOSTICS_END
bool Snapshot(Track& t, float& life, float& distance) noexcept
{
    std::uintptr_t table{}; void *base{}, *weapon{}, *source{}, *contacts{};
    nvo::hit::Form f{}, b{}, w{}, s{}; unsigned char impacted{}; U32 flags{};
    float gravity{};
    return Read(t.p,0,table) && table==kVtable && nvo::hit::ReadForm(t.p,f) && f.id==t.ref
        && Read(t.p,0x20,base) && Read(t.p,0xF8,weapon) && Read(t.p,0xFC,source)
        && nvo::hit::ReadForm(base,b) && b.id==t.base && b.type==0x33
        && nvo::hit::ReadForm(weapon,w) && w.id==t.weapon && w.type==0x28
        && nvo::hit::ReadForm(source,s) && s.id==t.source
        && Read(t.p,0x88,contacts) && !contacts && Read(t.p,0x90,impacted) && !impacted
        && Read(t.p,0xC8,flags) && !(flags&1) && Read(base,0x64,gravity) && gravity==0
        && Read(t.p,0xD8,life) && std::isfinite(life) && life>=0
        && Read(t.p,0x110,distance) && std::isfinite(distance) && distance>=0;
}
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

#include "FlightImpact.inl"

// Engine source direction: Rz(heading at +2C) * Rx(pitch at +24).
// Forward is local +Y; positive pitch points down. Rotation Y is not used by
// this verified matrix pair. Reject nonzero roll rather than generalize it.
struct Rotation {
    double cp{}, sp{}, cy{}, sy{};
    Vec World(Vec v) const noexcept {
        const double y=cp*v.y+sp*v.z, z=-sp*v.y+cp*v.z;
        return {cy*v.x+sy*y,-sy*v.x+cy*y,z};
    }
    Vec Local(Vec v) const noexcept {
        const double x=cy*v.x-sy*v.y, y=sy*v.x+cy*v.y;
        return {x,cp*y-sp*v.z,sp*y+cp*v.z};
    }
};
bool RotationOf(void* owner, Rotation& r, float (&angles)[3]) noexcept
{
    if (!Read(owner,0x24,angles)) return false;
    for (float a:angles) if (!std::isfinite(a) || std::abs(a)>100) return false;
    if (std::abs(angles[1])>0.00001f) return false;
    r={std::cos(angles[0]),std::sin(angles[0]),std::cos(angles[2]),std::sin(angles[2])};
    return true;
}
void __cdecl BeforeMovement(void* owner,float adjustedDt,float* input,std::uintptr_t frame) noexcept
{
    const ErrorGuard error;
    if (!gActive.load(std::memory_order_acquire)) return;
    const Lock lock;
    if (!gActive.load(std::memory_order_relaxed)) return;
    ++gMoveEntries;
    auto* t=Find(owner);
    if (!t) { ++gMoveUntracked; return; }
    ++t->movementEntries;
    if (t->stopped) return;
    if (t->pending) { Reject(*t,"missing_accounting_or_overlapping_call"); return; }
    std::uintptr_t caller{},wrapper{},wrapperCaller{}; void *frameOwner{},*wrapperOwner{};
    float dt{},frameDt{};
    if (frame<0x2C || !OnStack(frame-0x2C,0x44)
        || reinterpret_cast<std::uintptr_t>(input)!=frame+0xC
        || !Read(reinterpret_cast<void*>(frame),4,caller) || caller!=0x9BF35D
        || !Read(reinterpret_cast<void*>(frame),-0x2C,frameOwner) || frameOwner!=owner
        || !Read(reinterpret_cast<void*>(frame),8,frameDt) || frameDt!=adjustedDt
        || !Read(reinterpret_cast<void*>(frame),0,wrapper) || wrapper<0x18 || !OnStack(wrapper-0x18,0x24)
        || !Read(reinterpret_cast<void*>(wrapper),4,wrapperCaller) || (wrapperCaller!=0x9B83EA && wrapperCaller!=0x9B8481)
        || !Read(reinterpret_cast<void*>(wrapper),-0x14,wrapperOwner) || wrapperOwner!=owner
        || !Read(reinterpret_cast<void*>(wrapper),8,dt)) { Reject(*t,"movement_stack_contract"); return; }
    if (!std::isfinite(dt) || dt<0 || dt>0.25f || !std::isfinite(adjustedDt) || adjustedDt<0) { Reject(*t,"unsupported_timestep"); return; }
    if (dt==0) return;
    float local[3]{},life{},distance{},pos[3]{},angles[3]{}; Rotation rotation{};
    if (!Read(input,0,local) || !Read(owner,0x30,pos) || !Snapshot(*t,life,distance)) { Reject(*t,"identity_or_collision_or_layout"); return; }
    for (float v:pos) if (!std::isfinite(v) || std::abs(v)>1e7f) { Reject(*t,"invalid_position"); return; }
    if (!RotationOf(owner,rotation,angles)) { Reject(*t,"unsupported_rotation"); return; }
    if (local[0]!=0 || local[2]!=0 || !std::isfinite(local[1]) || local[1]<=0) { Reject(*t,"unsupported_input_vector"); return; }
    if (life<t->life || distance<t->distance || (life==t->life && distance==t->distance)) { Reject(*t,"duplicate_or_reversed_step"); return; }
    const double baseline=local[1]/(static_cast<double>(dt)*gConfig.units);
    if (!std::isfinite(baseline) || baseline<10 || baseline>gConfig.sound*4.9) { Reject(*t,"unsupported_engine_speed"); return; }
    if (t->baselineVerified && std::abs(baseline/t->baseline-1)>0.001) { Reject(*t,"engine_speed_changed"); return; }
    const Vec world=rotation.World({local[0],local[1],local[2]});
    Vec velocity=t->baselineVerified?t->velocity:Mul(world,1/(dt*gConfig.units));
    const Vec before=velocity;
    Vec displacement=world;
    float submitted[3]={local[0],local[1],local[2]};
    if (t->baselineVerified) {
        displacement=Mul(Integrate(velocity,dt,*t),gConfig.units);
        const Vec replacement=rotation.Local(displacement);
        float values[3]={static_cast<float>(replacement.x),static_cast<float>(replacement.y),static_cast<float>(replacement.z)};
        for (float v:values) if (!std::isfinite(v) || std::abs(v)>1e7f) { Reject(*t,"integration_out_of_range"); return; }
        if (!WriteVector(input,values)) { Reject(*t,"stack_write_failed"); return; }
        if (!Read(input,0,submitted) || std::memcmp(submitted,values,sizeof(values))) {
            Reject(*t,"stack_write_readback_failed"); return;
        }
        ++t->steps; ++gApplied;
    }
    t->pending=true; t->wrote=t->baselineVerified; t->frame=frame; t->thread=GetCurrentThreadId();
    t->expected=displacement; t->proposedVelocity=velocity; t->startPos={pos[0],pos[1],pos[2]};
    t->pendingDt=dt; t->pendingBaseline=baseline; t->life=life; t->distance=distance;
    t->submitted={submitted[0],submitted[1],submitted[2]};
    t->stepResetObserved=false;
    t->terrainAdjusted=false;
    if (t->logged && t->movementEntries<=kLoggedSteps) nvo::log::Write("PHYSICS_STEP session=%u lifetime=%llu step=%u phase=%s profile=%u dt_s=%.9g movement_dt_s=%.9g speed_before_mps=%.9g speed_after_mps=%.9g vz_before=%.9g vz_after=%.9g world_delta=(%.9g,%.9g,%.9g) pitch=%.9g heading=%.9g argument_write=%u damage_write=0",
        gSession,t->serial,t->steps,t->wrote?"apply":"baseline",t->profile,static_cast<double>(dt),static_cast<double>(adjustedDt),
        Length(before),Length(velocity),before.z,velocity.z,displacement.x,displacement.y,displacement.z,
        static_cast<double>(angles[0]),static_cast<double>(angles[2]),t->wrote?1u:0u);
    if (t->logged && t->movementEntries<=kLoggedSteps) nvo::log::Write("PHYSICS_ARGUMENT session=%u lifetime=%llu step=%u phase=%s readback=(%.9g,%.9g,%.9g) write_verified=%u observer_writes=0",
        gSession,t->serial,t->steps,t->wrote?"apply":"baseline",t->submitted.x,t->submitted.y,t->submitted.z,t->wrote?1u:0u);
}

// Observe two existing movement exits, without changing their arguments or
// invoking extra engine functions. EBX is the generic move's saved argument
// frame (not its aligned EBP); the enclosing bullet frame stays alive here.
void __cdecl BeforeBoundary(std::uintptr_t frame,std::uintptr_t args,U32 phase) noexcept
{
    const ErrorGuard error;
    if (!gActive.load(std::memory_order_acquire)) return;
    if (frame<0x30 || !OnStack(frame-0x30,0x34) || !OnStack(args,0x14)) return;
    void* owner{}; std::uintptr_t caller{},input{};
    if (!Read(reinterpret_cast<void*>(args),4,caller) || caller!=0x9BF416
        || !Read(reinterpret_cast<void*>(frame),-0x18,owner)
        || !Read(reinterpret_cast<void*>(args),0xC,input)) return;
    const Lock lock;
    if (!gActive.load(std::memory_order_relaxed)) return;
    auto* t=Find(owner);
    if (!t || t->stopped || !t->pending || t->thread!=GetCurrentThreadId()
        || input!=t->frame+0xC || !OnStack(input,12)) return;
    if (phase==0) ++t->commitEntries; else ++t->nodeEntries;
    // Read-only evidence. The optional controller's address is not dereferenced.
    float argument[3]{},position[3]{},current[3]{}; void* controller{};
    if (!Read(reinterpret_cast<void*>(input),0,argument)
        || !Read(reinterpret_cast<void*>(frame),-0x30,position)
        || !Read(reinterpret_cast<void*>(frame),-0x20,controller)
        || !Read(owner,0x30,current)) { Reject(*t,"boundary_read_failed"); return; }
    for (float v:argument) if (!std::isfinite(v)) { Reject(*t,"boundary_nonfinite"); return; }
    for (float v:position) if (!std::isfinite(v)) { Reject(*t,"boundary_nonfinite"); return; }
    for (float v:current) if (!std::isfinite(v)) { Reject(*t,"boundary_nonfinite"); return; }
    if (t->logged && t->movementEntries<=kLoggedSteps) nvo::log::Write("PHYSICS_BOUNDARY session=%u lifetime=%llu step=%u path=%s controller_present=%u argument=(%.9g,%.9g,%.9g) candidate_delta=(%.9g,%.9g,%.9g) current_delta=(%.9g,%.9g,%.9g) observer_writes=0",
        gSession,t->serial,t->steps,phase==0?"position_commit":"node_commit",controller?1u:0u,
        static_cast<double>(argument[0]),static_cast<double>(argument[1]),static_cast<double>(argument[2]),
        position[0]-t->startPos.x,position[1]-t->startPos.y,position[2]-t->startPos.z,
        current[0]-t->startPos.x,current[1]-t->startPos.y,current[2]-t->startPos.z);
}
// phase 0: immediately before the existing virtual C8 dispatch (actual target).
// phase 1: immediately before the alternate C70B60 direct call.
// phase 2: both paths have returned, before the existing listener flag query.
// The request remains stack-owned at generic EBP-208. Read initialized fields
// individually so padding never becomes purported evidence.
void __cdecl ObserveController(std::uintptr_t frame,std::uintptr_t args,void* receiver,
    std::uintptr_t state,std::uintptr_t target,U32 phase) noexcept
{
    const ErrorGuard error;
    if (!gActive.load(std::memory_order_acquire)) return;
    if (phase>2 || frame<0x208 || !OnStack(frame-0x208,0x20C) || !OnStack(args,0x14)) return;
    void* owner{}; void* controller{}; std::uintptr_t caller{},input{};
    if (!Read(reinterpret_cast<void*>(args),4,caller) || caller!=0x9BF416
        || !Read(reinterpret_cast<void*>(frame),-0x18,owner)
        || !Read(reinterpret_cast<void*>(frame),-0x20,controller)
        || !Read(reinterpret_cast<void*>(args),0xC,input)) return;
    const Lock lock;
    if (!gActive.load(std::memory_order_relaxed)) return;
    auto* t=Find(owner);
    if (!t || t->stopped || !t->pending || t->thread!=GetCurrentThreadId()
        || input!=t->frame+0xC || !OnStack(input,12)) return;
    const auto controllerAddress=reinterpret_cast<std::uintptr_t>(controller);
    const auto receiverAddress=reinterpret_cast<std::uintptr_t>(receiver);
    if (!controllerAddress || (phase<2 && (receiver!=controller || state!=frame-0x208))
        || (phase==2 && (controllerAddress>UINTPTR_MAX-0x410 || receiverAddress!=controllerAddress+0x410))) {
        Reject(*t,"controller_stack_contract"); return;
    }
    if (phase==2) {
        if (!t->controllerPending || t->controller!=controller || t->controllerFrame!=frame
            || t->controllerArgs!=args || t->controllerState!=frame-0x208) {
            Reject(*t,"controller_return_unpaired"); return;
        }
        state=t->controllerState; target=t->controllerTarget;
        t->controllerPending=false; ++t->controllerReturns;
    } else {
        if (t->controllerPending) { Reject(*t,"controller_dispatch_overlap"); return; }
        t->controllerPending=true; t->controller=controller; t->controllerFrame=frame;
        t->controllerArgs=args; t->controllerState=state; t->controllerTarget=target;
        ++t->controllerEntries;
    }
    std::uintptr_t table{},virtualTarget{}; float request[7]{},argument[3]{},aux{};
    U32 flags{}; unsigned char active{};
    if (!Read(controller,0,table) || !Read(reinterpret_cast<void*>(table),0xC8,virtualTarget)
        || (phase==0 && virtualTarget!=target)
        || !Read(reinterpret_cast<void*>(state),0,request)
        || !Read(reinterpret_cast<void*>(state),0x1C,flags)
        || !Read(reinterpret_cast<void*>(state),0x20,aux)
        || !Read(reinterpret_cast<void*>(state),0x24,active)
        || !Read(reinterpret_cast<void*>(input),0,argument)) { Reject(*t,"controller_request_read"); return; }
    for (float v:request) if (!std::isfinite(v)) { Reject(*t,"controller_request_nonfinite"); return; }
    if (t->logged && t->movementEntries<=kLoggedSteps) {
        nvo::log::Write("PHYSICS_CONTROLLER session=%u lifetime=%llu step=%u phase=%s controller=%08X vtable=%08X target=%08X virtual_c8=%08X dt_s=%.9g rotation=(%.9g,%.9g,%.9g) request=(%.9g,%.9g,%.9g) flags=%08X aux=%.9g active=%u observer_writes=0",
            gSession,t->serial,t->steps,phase==0?"virtual_enter":phase==1?"direct_enter":"return",
            static_cast<U32>(controllerAddress),static_cast<U32>(table),static_cast<U32>(target),static_cast<U32>(virtualTarget),
            static_cast<double>(request[0]),static_cast<double>(request[1]),static_cast<double>(request[2]),static_cast<double>(request[3]),
            static_cast<double>(request[4]),static_cast<double>(request[5]),static_cast<double>(request[6]),flags,static_cast<double>(aux),static_cast<unsigned>(active));
        nvo::log::Write("PHYSICS_CONTROLLER_ARGUMENT session=%u lifetime=%llu step=%u phase=%u argument=(%.9g,%.9g,%.9g) observer_writes=0",
            gSession,t->serial,t->steps,phase,static_cast<double>(argument[0]),static_cast<double>(argument[1]),static_cast<double>(argument[2]));
    }
}

void __cdecl BeforeAccounting(void* owner,const float* delta,U32 accumulate,std::uintptr_t frame) noexcept
{
    const ErrorGuard error;
    if (!gActive.load(std::memory_order_acquire)) return;
    const Lock lock;
    if (!gActive.load(std::memory_order_relaxed)) return;
    ++gAccountingEntries;
    auto* t=Find(owner);
    if (!t) { ++gAccountingUntracked; return; }
    ++t->accountingEntries;
    if (t->stopped) return;
    if (!t->pending) { ++gUnpaired; Reject(*t,"accounting_without_movement"); return; }
    if (t->controllerPending) { Reject(*t,"controller_return_missing"); return; }
    std::uintptr_t caller{}; void* frameOwner{};
    if (t->frame!=frame || t->thread!=GetCurrentThreadId() || frame<0x2C || !OnStack(frame-0x2C,0x44)
        || !OnStack(reinterpret_cast<std::uintptr_t>(delta),12) || accumulate!=1
        || !Read(reinterpret_cast<void*>(frame),4,caller) || caller!=0x9BF35D
        || !Read(reinterpret_cast<void*>(frame),-0x2C,frameOwner) || frameOwner!=owner) { Reject(*t,"accounting_stack_contract"); return; }
    float returned[3]{};
    if (!Read(reinterpret_cast<void*>(frame),0xC,returned)) { Reject(*t,"returned_argument_read_failed"); return; }
    if (t->logged && t->accountingEntries<=kLoggedSteps) nvo::log::Write("PHYSICS_ARGUMENT_RETURN session=%u lifetime=%llu step=%u argument=(%.9g,%.9g,%.9g) observer_writes=0",
        gSession,t->serial,t->steps,static_cast<double>(returned[0]),static_cast<double>(returned[1]),static_cast<double>(returned[2]));
    // A collision is not a direction failure. Impact/destruction events retire
    // the track; neither this observer nor the movement hook changes collision data.
    void* contacts{}; unsigned char impacted{};
    if (!Read(owner,0x88,contacts) || !Read(owner,0x90,impacted)) { Reject(*t,"accounting_collision_read"); return; }
    if (contacts || impacted) {
        if (t->terrainAdjusted) ++gTerrainCollisionExcluded;
        ImpactCollision(*t,delta);
        t->pending=false; return;
    }
    float actual[3]{},pos[3]{},life{},distance{};
    if (!Read(delta,0,actual) || !Read(owner,0x30,pos) || !Snapshot(*t,life,distance)) { Reject(*t,"accounting_identity_or_read"); return; }
    for (float v:actual) if (!std::isfinite(v)) { Reject(*t,"accounting_nonfinite"); return; }
    for (float v:pos) if (!std::isfinite(v)) { Reject(*t,"accounting_nonfinite_position"); return; }
    const Vec measured{actual[0],actual[1],actual[2]};
    const double vectorError=Length(Add(measured,Mul(t->expected,-1)));
    const double positionError=Length(Add(Add({pos[0],pos[1],pos[2]},Mul(t->startPos,-1)),Mul(measured,-1)));
    const double coordinate=std::fmax(std::fmax(std::abs(t->startPos.x),std::abs(t->startPos.y)),std::abs(t->startPos.z));
    const double tolerance=0.002+coordinate*0.0000005+Length(t->expected)*0.00002;
    const bool matched=vectorError<=tolerance && positionError<=tolerance;
    if (t->logged && t->accountingEntries<=kLoggedSteps) nvo::log::Write("PHYSICS_ACTUAL session=%u lifetime=%llu step=%u phase=%s matched=%u actual_delta=(%.9g,%.9g,%.9g) vector_error=%.9g position_error=%.9g tolerance=%.9g writes=0",
        gSession,t->serial,t->steps,t->wrote?"apply":"baseline",matched?1u:0u,measured.x,measured.y,measured.z,vectorError,positionError,tolerance);
    t->pending=false;
    if (!matched) { ++gMismatched;
        // NVO_3F1_DIAGNOSTICS_BEGIN
        LogDisplacementFailure(*t,measured,pos,returned,life,distance,vectorError,positionError,tolerance);
        // NVO_3F1_DIAGNOSTICS_END
        Reject(*t,t->wrote?"applied_displacement_mismatch":"baseline_direction_mismatch"); return; }
    if (!t->wrote && !t->stepResetObserved) { Reject(*t,"baseline_reset_boundary_not_observed"); return; }
    if (t->terrainAdjusted) {
        ++gTerrainVerified;
        if (gTerrainVerified<=16 && !nvo::log::Write("PHYSICS_TERRAIN_REJECT_DEFAULT_VERIFIED session=%u lifetime=%llu step=%u vector_error=%.9g position_error=%.9g tolerance=%.9g actual_z=%.9g",
            gSession,t->serial,t->steps,vectorError,positionError,tolerance,static_cast<double>(pos[2]))) ++gTerrainLogFailures;
    }
    t->velocity=t->proposedVelocity; t->baseline=t->pendingBaseline;
    if (t->wrote) { t->elapsed+=t->pendingDt; ++t->verifiedSteps; ++gVerified; }
    else { t->baselineVerified=true; ++gBaselines; }
}
// Called only when the engine actually reaches its conditional local-Z reset.
// A true result preserves the already-copied vector; it never writes an actor,
// controller, request, position or collision field. False replays FLDZ/FSTP.
U32 __cdecl PreserveLocalZ(void* controller,std::uintptr_t state,
    std::uintptr_t frame,std::uintptr_t stack) noexcept
{
    const ErrorGuard error;
    if (!gActive.load(std::memory_order_acquire)) return 0;
    const Lock lock;
    if (!gActive.load(std::memory_order_relaxed)) return 0;
    Track* t=nullptr;
    for (auto& entry:gTracks) if (entry.serial && !entry.stopped && entry.pending
        && entry.controllerPending && entry.controller==controller
        && entry.controllerState==state && entry.thread==GetCurrentThreadId()) {
        if (t) { Reject(*t,"reset_identity_ambiguous"); Reject(entry,"reset_identity_ambiguous"); return 0; }
        t=&entry;
    }
    if (!t) return 0;
    ++t->resetEntries; ++gResetEntries;
    // C73170: conventional incoming EBP, aligned locals, A4 bytes + 3 saved
    // registers. ESP here is before our CALL's extra return-address push.
    std::uintptr_t parent{},caller{},request{},table{},target{},vectorPointer{};
    if (t->stepResetObserved || t->controllerTarget!=kControllerTarget
        || frame<0xB0 || stack!=(frame&~std::uintptr_t(15))-0xB0
        || !OnStack(stack,static_cast<unsigned>(frame-stack)+12)
        || !OnStack(state,0x28)
        || !Read(reinterpret_cast<void*>(frame),0,parent) || parent!=t->controllerFrame
        || !Read(reinterpret_cast<void*>(frame),4,caller) || caller!=kDispatchSite+5
        || !Read(reinterpret_cast<void*>(frame),8,request) || request!=state
        || !Read(reinterpret_cast<void*>(stack),0x48,vectorPointer) || vectorPointer!=state+0x10
        || !Read(controller,0,table) || table!=kControllerVtable
        || !Read(reinterpret_cast<void*>(table),0xC8,target) || target!=kControllerTarget) {
        Reject(*t,"reset_stack_or_controller_contract"); return 0;
    }
    float working[3]{},input[7]{},original[3]{},dt{},angles[3]{},life{},distance{};
    Rotation rotation{}; U32 flags{};
    if (!Read(reinterpret_cast<void*>(stack),0x50,working)
        || !Read(reinterpret_cast<void*>(state),0,input)
        || !Read(reinterpret_cast<void*>(t->frame),0xC,original)
        || !Read(reinterpret_cast<void*>(t->controllerArgs),8,dt)
        || !Read(controller,0x414,flags)
        || !RotationOf(t->p,rotation,angles) || !Snapshot(*t,life,distance)) {
        Reject(*t,"reset_read_or_identity"); return 0;
    }
    const float submitted[3]={static_cast<float>(t->submitted.x),static_cast<float>(t->submitted.y),static_cast<float>(t->submitted.z)};
    for (float v:input) if (!std::isfinite(v)) { Reject(*t,"reset_nonfinite_request"); return 0; }
    if (!(dt>0) || input[0]!=dt || input[1]!=angles[0] || input[2]!=angles[1] || input[3]!=angles[2]
        || (flags&(1u<<11)) || std::memcmp(working,submitted,sizeof(working))
        || std::memcmp(input+4,submitted,sizeof(working)) || std::memcmp(original,submitted,sizeof(working))) {
        Reject(*t,"reset_vector_or_timestep_contract"); return 0;
    }
    t->stepResetObserved=true;
    const bool preserve=t->wrote && t->baselineVerified;
    if (preserve) { ++t->resetPreserved; ++gResetPreserved; }
    if (t->logged && t->movementEntries<=kLoggedSteps) nvo::log::Write("PHYSICS_LOCAL_Z session=%u lifetime=%llu step=%u phase=%s site=00C73517 reset_branch_observed=1 working=(%.9g,%.9g,%.9g) preserve=%u original_reset=%u dt_s=%.9g flags=%08X direct_object_writes=0",
        gSession,t->serial,t->steps,t->wrote?"apply":"baseline",static_cast<double>(working[0]),static_cast<double>(working[1]),static_cast<double>(working[2]),
        preserve?1u:0u,preserve?0u:1u,static_cast<double>(dt),flags);
    return preserve?1u:0u;
}

// Original six bytes: FLDZ; FSTP [ESP+58]. CALL bridge + NOP leaves the
// original fall-through at C7351D. Both epilogues restore GP/flags/FP state.
// On fallback ESP still includes our return address, hence +5C (not +58).
__declspec(naked) void LocalZBridge()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        lea eax, [ebx+40]
        push eax
        push dword ptr [ebx+8]
        push dword ptr [ebx+4]
        push dword ptr [ebx+16]
        call PreserveLocalZ
        add esp, 16
        test eax, eax
        jz original_reset
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        ret
    original_reset:
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        fldz
        fstp dword ptr [esp+05Ch]
        ret
    }
}

// This runs AFTER the engine's original terrain query, exactly once per call.
// The engine ignores AL and applies its -2048 default even when the query fails.
// For an identified private applied step only, suppress that invalid clamp by
// replacing its stack-local height result with the already computed candidate Z.
// A successful query, collision, baseline or foreign movement is untouched.
bool WriteTerrainHeight(volatile float* height,float value) noexcept
{
    __try { *height=value; return *height==value; }
    __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
void __cdecl AfterTerrainQuery(std::uintptr_t frame,std::uintptr_t args,
    const float* candidate,float* height,U32 result) noexcept
{
    const ErrorGuard error;
    if (!gActive.load(std::memory_order_acquire)) return;
    if (frame<0x2B4 || !OnStack(frame-0x2B4,0x2B8) || !OnStack(args,0x14)
        || reinterpret_cast<std::uintptr_t>(candidate)!=frame-0x30
        || reinterpret_cast<std::uintptr_t>(height)!=frame-0x2B4) return;
    void* owner{}; std::uintptr_t caller{},input{};
    if (!Read(reinterpret_cast<void*>(args),4,caller) || caller!=0x9BF416
        || !Read(reinterpret_cast<void*>(frame),-0x18,owner)
        || !Read(reinterpret_cast<void*>(args),0xC,input)) return;
    const Lock lock;
    if (!gActive.load(std::memory_order_relaxed)) return;
    auto* t=Find(owner);
    if (!t || t->stopped || !t->pending || !t->wrote || !t->baselineVerified
        || t->thread!=GetCurrentThreadId() || input!=t->frame+0xC
        || t->controllerPending || !t->stepResetObserved
        || t->controllerTarget!=kControllerTarget || t->controllerFrame!=frame
        || t->controllerArgs!=args) return;
    ++gTerrainQueries;
    if (result&0xFFu) return; // Preserve the successful engine query and its AL.
    ++gTerrainFailed;
    float proposed[3]{},floor{},life{},distance{};
    if (!Read(candidate,0,proposed) || !Read(height,0,floor)) { Reject(*t,"terrain_result_read"); return; }
    for (float v:proposed) if (!std::isfinite(v)) { Reject(*t,"terrain_candidate_nonfinite"); return; }
    if (floor!=-2048.0f) { Reject(*t,"terrain_failed_result_changed"); return; }
    // Match the inspected engine's strict (>30 units) correction threshold.
    if (static_cast<double>(floor)-proposed[2]<=30.0) return;
    if (t->terrainAdjusted) { Reject(*t,"terrain_adjustment_duplicate"); return; }
    // Includes exact projectile identity and absence of contact/impact state.
    if (!Snapshot(*t,life,distance)) return;
    const double coordinate=std::fmax(std::fmax(std::abs(t->startPos.x),std::abs(t->startPos.y)),std::abs(t->startPos.z));
    const double tolerance=0.002+coordinate*0.0000005+Length(t->expected)*0.00002;
    const double candidateError=Length(Add(Add({proposed[0],proposed[1],proposed[2]},Mul(t->startPos,-1)),Mul(t->expected,-1)));
    if (candidateError>tolerance) { Reject(*t,"terrain_candidate_displacement_mismatch"); return; }
    if (!WriteTerrainHeight(height,proposed[2])) { Reject(*t,"terrain_result_write"); return; }
    t->terrainAdjusted=true; ++gTerrainCorrected;
    if (gTerrainCorrected<=16 && !nvo::log::Write("PHYSICS_TERRAIN_REJECT_DEFAULT session=%u lifetime=%llu step=%u query_ok=0 default_z=%.9g candidate_z=%.9g prevented_raise=%.9g candidate_error=%.9g tolerance=%.9g stack_height_write=1 position_write=0 result_preserved=1",
        gSession,t->serial,t->steps,static_cast<double>(floor),static_cast<double>(proposed[2]),
        static_cast<double>(floor)-proposed[2],candidateError,tolerance)) ++gTerrainLogFailures;
}
__declspec(naked) void TerrainBridge()
{
    __asm {
        // The guarded call site belongs to generic movement, whose EBX is its
        // argument frame. Non-projectile callers take the original call directly.
        pushfd
        cmp dword ptr [ebx+4], 09BF416h
        je projectileCaller
        popfd
        jmp dword ptr [gOriginalTerrain]
    projectileCaller:
        popfd
        // Duplicate the two arguments. Original __thiscall consumes these copies.
        push dword ptr [esp+8]
        push dword ptr [esp+8]
        call dword ptr [gOriginalTerrain]
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push dword ptr [ebx+28] // original query EAX (AL is bool)
        push dword ptr [ebx+44] // original height output argument
        push dword ptr [ebx+40] // original candidate argument
        push dword ptr [ebx+16] // generic function's saved EBX argument frame
        push dword ptr [ebx+8]  // generic function EBP
        call AfterTerrainQuery
        add esp, 20
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        ret 8
    }
}

__declspec(naked) void CommitBridge()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push 0
        push dword ptr [ebx+16]
        push dword ptr [ebx+8]
        call BeforeBoundary
        add esp, 12
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginalCommit]
    }
}
__declspec(naked) void NodeBridge()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push 1
        push dword ptr [ebx+16]
        push dword ptr [ebx+8]
        call BeforeBoundary
        add esp, 12
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginalNode]
    }
}
__declspec(naked) void MovementBridge()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push dword ptr [ebx+8]
        push dword ptr [ebx+44]
        push dword ptr [ebx+40]
        push dword ptr [ebx+24]
        call BeforeMovement
        add esp, 16
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginalMovement]
    }
}
__declspec(naked) void AccountingBridge()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push dword ptr [ebx+8]
        push dword ptr [ebx+52]
        lea eax, [ebx+40]
        push eax
        push dword ptr [ebx+24]
        call BeforeAccounting
        add esp, 16
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginalAccounting]
    }
}

// The eight-byte virtual load/call is replaced by CALL bridge + three NOPs.
// Reproduce its original load, then tail-jump to that exact target. The returned
// address traverses those NOPs to 0092FFF2; the original thiscall owns its argument.
__declspec(naked) void ControllerDispatchBridge()
{
    __asm {
        mov eax, dword ptr [edx+0C8h]
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push 0
        push dword ptr [ebx+28]
        push dword ptr [ebx+40]
        push dword ptr [ebx+24]
        push dword ptr [ebx+16]
        push dword ptr [ebx+8]
        call ObserveController
        add esp, 24
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp eax
    }
}
__declspec(naked) void ControllerDirectBridge()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push 1
        push 0C70B60h
        push dword ptr [ebx+40]
        push dword ptr [ebx+24]
        push dword ptr [ebx+16]
        push dword ptr [ebx+8]
        call ObserveController
        add esp, 24
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginalDirect]
    }
}
__declspec(naked) void ControllerReturnBridge()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push 2
        push 0
        push 0
        push dword ptr [ebx+24]
        push dword ptr [ebx+16]
        push dword ptr [ebx+8]
        call ObserveController
        add esp, 24
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginalAfterController]
    }
}

bool Fingerprint(std::uintptr_t address, unsigned size, std::uint64_t expected) noexcept
{
    unsigned char bytes[4700]{};
    if (size>sizeof(bytes) || !nvo::hit::ReadBytes(reinterpret_cast<void*>(address),bytes,size)) return false;
    if (!nvo::physics::NormalizeOwnedHooks(address,bytes,size)) return false;
    std::uint64_t h=14695981039346656037ull;
    for (unsigned i=0;i<size;++i) h=(h^bytes[i])*1099511628211ull;
    return h==expected;
}
bool Guard() noexcept
{
    const auto game=GetModuleHandleW(nullptr);
    IMAGE_DOS_HEADER dos{}; IMAGE_NT_HEADERS32 nt{};
    if (reinterpret_cast<std::uintptr_t>(game)!=0x400000 || !Read(game,0,dos)
        || dos.e_magic!=IMAGE_DOS_SIGNATURE || dos.e_lfanew<0x40 || dos.e_lfanew>0x1000
        || !Read(game,dos.e_lfanew,nt) || nt.Signature!=IMAGE_NT_SIGNATURE
        || nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_I386 || nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR32_MAGIC
        || nt.FileHeader.TimeDateStamp!=0x4E0D50ED || nt.OptionalHeader.SizeOfImage!=0x107B000) return false;
    return Fingerprint(0x0092F260,0x123C,0xDEFD795E42FB0C4Eull)
        && Fingerprint(0x004B4500,0xAC,0x21E78198D3719E46ull)
        && Fingerprint(0x004A0C90,0x300,0xEC266DFC1B55BBDCull)
        && Fingerprint(0x009BF300,0x16C,0x0267E4DCAFB26157ull)
        && Fingerprint(0x009B8030,0x865,0xA1B80FE6DF917F84ull)
        && Fingerprint(0x009C4E60,0x5E,0xD82BC9F26A9C40F5ull)
        && Fingerprint(0x00430830,0x11,0x22C5CAF119221249ull)
        && Fingerprint(0x00931D70,0x15,0xB917B8CF60D822D8ull)
        && Fingerprint(0x0080F790,0x18,0x5A6DD9F715394886ull)
        && Fingerprint(0x00524AC0,0x73,0x8502BBFDBBBD29A0ull)
        && Fingerprint(kControllerTarget,2048,0x0193951146A4412Cull)
        && Fingerprint(kTerrainOriginal,0x104,0x467D34370ECFAF82ull)
        && Fingerprint(0x1017824,4,0x4D25317F9DCD9EB6ull)
        && Fingerprint(0x101DB88,8,0xA8031C3227732F3Bull);
}

const char* ReadConfig() noexcept
{
    wchar_t path[32768]{};
    if (!GetModuleFileNameW(nullptr,path,32768)) return "config_path";
    auto* slash=std::wcsrchr(path,L'\\'); if (!slash) return "config_path";
    slash[1]=0;
    if (wcscat_s(path,L"Data\\NVSE\\Plugins\\NVOFlightPhysics.ini")) return "config_path";
    wchar_t wide[2048]{};
    const DWORD n=GetPrivateProfileSectionW(L"Physics",wide,2048,path);
    if (!n || n>=2046) return "missing_or_large_config";
    unsigned fields=0; Config c{}; bool enabled=false;
    for (const wchar_t* entry=wide;*entry;entry+=std::wcslen(entry)+1) {
        const auto* equal=std::wcschr(entry,L'='); if (!equal) return "invalid_config_entry";
        wchar_t key[64]{}; const auto count=equal-entry;
        if (count<=0 || count>=64) return "invalid_config_key";
        std::wmemcpy(key,entry,count);
        wchar_t* end{}; const double v=std::wcstod(equal+1,&end);
        while (*end==L' ' || *end==L'\t') ++end;
        if (end==equal+1 || *end || !std::isfinite(v)) return "invalid_config_value";
        unsigned bit=0;
        if (!std::wcscmp(key,L"schema")) { bit=1; if (v!=2) return "unsupported_schema"; }
        else if (!std::wcscmp(key,L"enabled")) { bit=2; if (v!=0 && v!=1) return "invalid_enabled"; enabled=v==1; }
        else if (!std::wcscmp(key,L"units_per_metre")) { bit=4; c.units=v; if (v<1 || v>1000) return "invalid_scale"; }
        else if (!std::wcscmp(key,L"gravity_mps2")) { bit=8; c.gravity=v; if (v<0 || v>30) return "invalid_gravity"; }
        else if (!std::wcscmp(key,L"air_density_kg_m3")) { bit=16; c.density=v; if (v<0 || v>5) return "invalid_density"; }
        else if (!std::wcscmp(key,L"speed_of_sound_mps")) { bit=32; c.sound=v; if (v<250 || v>450) return "invalid_sound_speed"; }
        else return "unknown_config_key";
        if (fields&bit) return "duplicate_config_key";
        fields|=bit;
    }
    if (fields!=63) return "incomplete_config";
    if (!enabled) return "disabled_by_config";
    gConfig=c; return nullptr;
}
struct Hook {
    std::uintptr_t site;
    unsigned length;
    unsigned char original[8];
    unsigned char* patch;
    void (*bridge)();
};
const Hook gHooks[]={
    {kSite,5,{0xE8,0xFA,0x59,0,0},gPatch,AccountingBridge},
    {kMoveSite,5,{0xE8,0x4A,0xFE,0xF6,0xFF},gMovePatch,MovementBridge},
    {kCommitSite,5,{0xE8,0xB6,0x53,0xC4,0xFF},gCommitPatch,CommitBridge},
    {kNodeSite,5,{0xE8,0x7F,0x0E,0xB1,0xFF},gNodePatch,NodeBridge},
    {kDispatchSite,8,{0x8B,0x82,0xC8,0,0,0,0xFF,0xD0},gDispatchPatch,ControllerDispatchBridge},
    {kDirectSite,5,{0xE8,0x87,0x0B,0x34,0},gDirectPatch,ControllerDirectBridge},
    {kAfterControllerSite,5,{0xE8,0xB0,0x04,0,0},gAfterControllerPatch,ControllerReturnBridge},
    {kLocalZSite,6,{0xD9,0xEE,0xD9,0x5C,0x24,0x58},gLocalZPatch,LocalZBridge},
    {kTerrainSite,5,{0xE8,0x8B,0x71,0xB2,0xFF},gTerrainPatch,TerrainBridge}
};
} // namespace

bool nvo::physics::NormalizeOwnedHooks(std::uintptr_t address, unsigned char* bytes, unsigned size) noexcept
{
    if (!gInstalled) return true;
    for (const auto& h:gHooks) {
        if (address>h.site) {
            if (address-h.site<h.length) return false; // Partially overlapping owned span.
            continue;
        }
        const auto offset=h.site-address;
        if (offset>=size) continue;
        if (size-offset<h.length || std::memcmp(bytes+offset,h.patch,h.length)) return false;
        std::memcpy(bytes+offset,h.original,h.length);
    }
    return true;
}

void nvo::physics::Initialize() noexcept
{
    const ErrorGuard error; const Lock lock;
    if (gAttempted) return; gAttempted=true;
    if (!Guard()) { nvo::log::Write("PHYSICS_DISABLED reason=unsupported_code_before_install"); return; }
    for (const auto& h:gHooks) {
        std::memset(h.patch,0x90,h.length);
        h.patch[0]=0xE8;
        const auto delta=static_cast<U32>(reinterpret_cast<std::uintptr_t>(h.bridge)-(h.site+5));
        std::memcpy(h.patch+1,&delta,4);
    }
    // Nine spans occupy four distinct pages. The generic span ends exactly at
    // 00930000; the controller reset has its own separately protected page.
    struct Page { std::uintptr_t start; unsigned span; DWORD original{}; };
    Page pages[]={{kMoveSite,static_cast<unsigned>(kSite+5-kMoveSite)}, {kTerrainSite,static_cast<unsigned>(kCommitSite+5-kTerrainSite)},
        {kNodeSite,static_cast<unsigned>(kAfterControllerSite+5-kNodeSite)}, {kLocalZSite,6}};
    constexpr unsigned pageCount=sizeof(pages)/sizeof(pages[0]);
    for (const auto& h:gHooks) if (std::memcmp(reinterpret_cast<void*>(h.site),h.original,h.length)) {
        nvo::log::Write("PHYSICS_DISABLED reason=hook_bytes_changed_before_commit"); return;
    }
    unsigned opened=0;
    for (;opened<pageCount;++opened) {
        auto& p=pages[opened];
        if (!VirtualProtect(reinterpret_cast<void*>(p.start),p.span,PAGE_EXECUTE_READWRITE,&p.original)) break;
    }
    if (opened!=pageCount) {
        bool restored=true; DWORD ignored{};
        for (unsigned i=0;i<opened;++i) {
            const auto& p=pages[i];
            if (!VirtualProtect(reinterpret_cast<void*>(p.start),p.span,p.original,&ignored)) restored=false;
        }
        nvo::log::Write("PHYSICS_DISABLED reason=hook_page_protection previous_pages_restored=%u",restored?1u:0u); return;
    }
    for (const auto& h:gHooks) std::memcpy(reinterpret_cast<void*>(h.site),h.patch,h.length);
    bool ok=true;
    for (const auto& p:pages) if (!FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(p.start),p.span)) ok=false;
    DWORD ignored{};
    for (const auto& p:pages) if (!VirtualProtect(reinterpret_cast<void*>(p.start),p.span,p.original,&ignored)) ok=false;
    if (!ok) {
        bool restored=true;
        for (const auto& p:pages) {
            if (!VirtualProtect(reinterpret_cast<void*>(p.start),p.span,PAGE_EXECUTE_READWRITE,&ignored)) { restored=false; continue; }
            for (const auto& h:gHooks) if (h.site>=p.start && h.site+h.length<=p.start+p.span
                && !std::memcmp(reinterpret_cast<void*>(h.site),h.patch,h.length)) {
                std::memcpy(reinterpret_cast<void*>(h.site),h.original,h.length);
            }
            if (!FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(p.start),p.span)) restored=false;
            if (!VirtualProtect(reinterpret_cast<void*>(p.start),p.span,p.original,&ignored)) restored=false;
        }
        nvo::log::Write("PHYSICS_DISABLED reason=hook_commit_failed rollback_restored=%u",restored?1u:0u); return;
    }
    gInstalled=true;
    nvo::log::Write("PHYSICS_HOOK_READY movement_site=009BF411 movement_original=0092F260 accounting_site=009BF461 accounting_original=009C4E60 commit_observer=00930475 node_observer=0092F5DC controller_dispatch=0092FFEA controller_direct=0092FFD4 controller_return=0092FFFB local_z_guard=00C73517 terrain_query_guard=00930150 terrain_stack_height_fix=1 boundary_observer_writes=0 generic_matrix_hook=0 installed_at=deferred_init execution_observed=0");
}
void nvo::physics::BeginCapture(unsigned session) noexcept
{
    const ErrorGuard error; const Lock lock;
    gActive.store(false); gSession=session; gAccepted=gApplied=gRejected=gOverflow=0;
    gMoveEntries=gAccountingEntries=gMoveUntracked=gAccountingUntracked=0;
    gMissingRoute=gBaselines=gVerified=gMismatched=gUnpaired=0;
    gResetEntries=gResetPreserved=0;
    // NVO_3F1_DIAGNOSTICS_BEGIN
    gFailureReportsWritten=gFailureWriteFailures=0;
    gTerrainQueries=gTerrainFailed=gTerrainCorrected=gTerrainVerified=0;
    gTerrainCollisionExcluded=gTerrainLogFailures=0;
    ImpactReset();
    // NVO_3F1_DIAGNOSTICS_END
    for (auto& t:gTracks) t={};
    const char* reason=ReadConfig();
    if (!reason && (!gInstalled || !nvo::hit::ProjectileLayoutReady() || !Guard())) reason="unsupported_code_or_hook_ownership";
    if (reason) { nvo::log::Write("PHYSICS_DISABLED session=%u reason=%s",session,reason); return; }
    gActive.store(true,std::memory_order_release);
    nvo::log::Write("PHYSICS_TERRAIN_READY session=%u query_site=00930150 original_query=004572E0 scope=private_applied_failed_query default_z=-2048 threshold=30 stack_height_only=1 damage_replacement=0",session);
    nvo::log::Write("PHYSICS_ARMED session=%u scope=explicit_profiles units_per_metre=%.9g scale_calibrated=0 gravity_mps2=%.9g density_kg_m3=%.9g sound_mps=%.9g coefficients=per_lifetime active_capacity=%u log_limits_do_not_stop_physics=1 baseline_steps_per_lifetime=1 execution_observed=0 damage_replacement=0",
        session,gConfig.units,gConfig.gravity,gConfig.density,gConfig.sound,kCapacity);
    // NVO_3F1_DIAGNOSTICS_BEGIN
    nvo::log::Write("PHYSICS_DIAGNOSTIC_READY session=%u schema=1 report_limit=%u rows_per_report=4 failure_rows_use_priority_reserve=1 routine_lifetimes=%u routine_entries=%u failure_snapshot_extra_engine_reads=0",
        session,kFailureReports,kLoggedLives,kLoggedSteps);
    // NVO_3F1_DIAGNOSTICS_END
}
bool nvo::physics::Ready(double units) noexcept
{
    const ErrorGuard error; const Lock lock;
    return gActive.load() && units==gConfig.units;
}
void nvo::physics::Suspend(const char* reason) noexcept
{
    const ErrorGuard error; const Lock lock;
    if (gActive.exchange(false)) {
        ImpactFinish(reason);
        unsigned open=0; for (auto& t:gTracks) if (t.serial) { ++open; MissingRoute(t,reason); Summary(t,reason); }
        nvo::log::Write("PHYSICS_TERRAIN_SUMMARY session=%u eligible_queries=%u failed_queries=%u corrected=%u verified=%u collision_excluded=%u log_write_failures=%u detail_limit=16 damage_replacement=0",gSession,gTerrainQueries,gTerrainFailed,gTerrainCorrected,gTerrainVerified,gTerrainCollisionExcluded,gTerrainLogFailures);
        nvo::log::Write("PHYSICS_SUMMARY session=%u reason=%s accepted=%u applied_steps=%u rejected=%u overflow=%u open=%u damage_replacement=0",gSession,reason,gAccepted,gApplied,gRejected,gOverflow,open);
        nvo::log::Write("PHYSICS_ROUTE_SUMMARY session=%u reason=%s move_entries_all=%u move_untracked=%u accounting_entries_all=%u accounting_untracked=%u baselines_verified=%u applied_verified=%u mismatches=%u accounting_unpaired=%u lives_without_update=%u reset_entries=%u reset_preserved=%u",
            gSession,reason,gMoveEntries,gMoveUntracked,gAccountingEntries,gAccountingUntracked,gBaselines,gVerified,gMismatched,gUnpaired,gMissingRoute,gResetEntries,gResetPreserved);
        // NVO_3F1_DIAGNOSTICS_BEGIN
        nvo::log::Write("PHYSICS_DIAGNOSTIC_SUMMARY session=%u reason=%s mismatches=%u complete_failure_reports=%u report_write_failures=%u reports_omitted_by_limit=%u report_limit=%u routine_lifetimes_omitted=%u damage_replacement=0",
            gSession,reason,gMismatched,gFailureReportsWritten,gFailureWriteFailures,
            gMismatched>kFailureReports?gMismatched-kFailureReports:0u,kFailureReports,
            gAccepted>kLoggedLives?gAccepted-kLoggedLives:0u);
        // NVO_3F1_DIAGNOSTICS_END
    }
    for (auto& t:gTracks) t={};
}
void nvo::physics::Track(void* p,U64 serial,U32 source,U32 weapon,U32 ammo,U32 base,unsigned profile,
    unsigned dragModel,double ballisticCoefficient) noexcept
{
    const ErrorGuard error; const Lock lock;
    if (!gActive.load() || !serial || !p || (dragModel!=1 && dragModel!=7)
        || !std::isfinite(ballisticCoefficient) || ballisticCoefficient<0.05 || ballisticCoefficient>2) return;
    if (auto* old=Find(p)) { Reject(*old,"identity_replaced"); *old={}; }
    nvo::hit::Form f{}; if (!nvo::hit::ReadForm(p,f) || !f.id) return;
    for (auto& t:gTracks) if (!t.serial) {
        t={}; t.p=p; t.serial=serial; t.ref=f.id; t.source=source; t.weapon=weapon; t.ammo=ammo; t.base=base; t.profile=profile;
        t.dragModel=dragModel; t.ballisticCoefficient=ballisticCoefficient;
        t.logged=gAccepted++<kLoggedLives;
        ImpactEnroll(t);
        if (t.logged) nvo::log::Write("PHYSICS_TRACK session=%u lifetime=%llu projectile=%08X weapon=%08X ammo=%08X base=%08X profile=%u drag_model=G%u bc=%.9g",gSession,serial,f.id,weapon,ammo,base,profile,dragModel,ballisticCoefficient);
        return;
    }
    if (++gOverflow<=4) nvo::log::Write("PHYSICS_REJECT session=%u lifetime=%llu reason=active_capacity original_engine_movement=1",gSession,serial);
}
void nvo::physics::Event(void* p,U64 serial,bool destroyed) noexcept
{
    const ErrorGuard error; const Lock lock;
    if (!gActive.load() || !serial) return;
    if (auto* t=Find(p,serial)) {
        ImpactEvent(*t,destroyed);
        MissingRoute(*t,destroyed?"destroy":"impact");
        if (destroyed) { Summary(*t,"destroy"); *t={}; }
        else if (!t->stopped) { Summary(*t,"impact"); t->stopped=true; }
    }
}
void nvo::physics::ObserveHit(void* p,const HitQuery& query) noexcept
{
    const ErrorGuard error; const Lock lock;
    if (!gActive.load() || query.session!=gSession || !query.lifetime) return;
    ImpactHit(Find(p,query.lifetime),query);
}

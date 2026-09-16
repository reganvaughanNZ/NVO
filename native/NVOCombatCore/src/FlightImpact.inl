// Included inside FlightPhysics.cpp's private namespace, after Integrate.
// Read-only diagnostics: the only mutations are this module's cache/counters.
// No impact estimate is exposed as damage authority or written into Track.
struct ImpactSample {
    unsigned valid{};
    U32 target{}, material{};
    ImpactTargetKind targetKind{ImpactTargetKind::Invalid};
    int region{-1};
    bool more{};
    bool policyRead{};
    U32 flags{};
    unsigned char impacted{};
    float life{}, distance{};
    Vec position{}, point{}, accounting{};
};
struct ImpactRecord {
    U64 serial{};
    U32 ref{}, source{}, weapon{}, ammo{}, base{};
    unsigned step{}, dragModel{};
    bool collisionCaptured{}, callbackReported{}, wrote{}, baselineVerified{};
    bool resetObserved{};
    bool modelCandidate{};
    double modelTime{},modelSpeed{};
    const char* modelStatus{"no_collision_sample"};
    bool speedAvailable{}, speedEngineSegment{};
    double speedLow{}, speedHigh{}, speedMean{};
    const char* speedStatus{"no_collision_sample"};
    ContactTerrain terrain{};
    Vec start{}, expected{}, before{}, full{};
    double dt{}, bc{}, tolerance{};
    ImpactSample collision{};
};
#include "FlightImpactModel.inl"
#include "FlightContactSpeed.inl"

constexpr unsigned kImpactLives=32;
ImpactRecord gImpactRecords[kImpactLives]{};
unsigned gImpactAdmitted{},gImpactOmitted{},gImpactBaselineContacts{};
unsigned gImpactObserved{}, gImpactCandidates{}, gImpactUnavailable{}, gImpactReadFailures{};
unsigned gImpactCallbacks{}, gImpactCorrelated{}, gImpactUnpaired{}, gImpactLogFailures{};
unsigned gImpactDuplicateCollisions{}, gImpactDuplicateCallbacks{}, gImpactDestroyWithoutCallback{};
unsigned gImpactSpeedRanges{},gImpactEngineSegments{};
void ResetImpactHits() noexcept;

bool ImpactVector(const void* p, unsigned offset, Vec& value) noexcept
{
    float data[3]{};
    if (!Read(p,offset,data)) return false;
    for (float f:data) if (!std::isfinite(f) || std::abs(f)>1e7f) return false;
    value={data[0],data[1],data[2]}; return true;
}
ImpactSample ReadImpact(const Track& t, const float* delta=nullptr) noexcept
{
    ImpactSample s{};
    std::uintptr_t table{}; void *base{},*weapon{},*source{};
    nvo::hit::Form f{},b{},w{},a{};
    if (!Read(t.p,0,table) || table!=kVtable || !nvo::hit::ReadForm(t.p,f) || f.id!=t.ref
        || !Read(t.p,0x20,base) || !Read(t.p,0xF8,weapon) || !Read(t.p,0xFC,source)
        || !nvo::hit::ReadForm(base,b) || b.id!=t.base || b.type!=0x33
        || !nvo::hit::ReadForm(weapon,w) || w.id!=t.weapon || w.type!=0x28
        || !nvo::hit::ReadForm(source,a) || a.id!=t.source) return s;
    s.valid|=1;
    s.policyRead=Read(t.p,0xC8,s.flags);
    if (ImpactVector(t.p,0x30,s.position) && Read(t.p,0xD8,s.life) && Read(t.p,0x110,s.distance)
        && Read(t.p,0x90,s.impacted) && std::isfinite(s.life) && s.life>=0 && s.life<=1e7f
        && std::isfinite(s.distance) && s.distance>=0 && s.distance<=1e12f) s.valid|=2;
    else { s.position={}; s.life=s.distance=0; s.impacted=0; }
    void *first{},*next{};
    if (Read(t.p,0x88,first) && Read(t.p,0x8C,next)) {
        s.valid|=4; s.more=next!=nullptr;
        void* target{}; nvo::hit::Form form{};
        if (first && Read(first,0,target) && (!target || nvo::hit::ReadForm(target,form))
            && ImpactVector(first,4,s.point) && Read(first,0x20,s.material) && Read(first,0x24,s.region)) {
            s.target=form.id; s.targetKind=ClassifyImpactTarget(target,form.id); s.valid|=8;
        } else { s.point={}; s.target=s.material=0; s.region=-1; s.targetKind=ImpactTargetKind::Invalid; }
    }
    if (delta && ImpactVector(delta,0,s.accounting)) s.valid|=16;
    return s;
}
void ImpactReset() noexcept
{
    ResetImpactHits();
    for (auto& r:gImpactRecords) r={};
    gImpactAdmitted=gImpactOmitted=gImpactBaselineContacts=0;
    gImpactObserved=gImpactCandidates=gImpactUnavailable=gImpactReadFailures=0;
    gImpactCallbacks=gImpactCorrelated=gImpactUnpaired=gImpactLogFailures=0;
    gImpactDuplicateCollisions=gImpactDuplicateCallbacks=gImpactDestroyWithoutCallback=0;
    gImpactSpeedRanges=gImpactEngineSegments=0;
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
    r.resetObserved=t.stepResetObserved;
    r.terrain=t.contactTerrain;
    r.start=t.startPos; r.expected=t.expected; r.before=t.wrote?t.velocity:t.proposedVelocity;
    r.full=t.proposedVelocity; r.dt=t.pendingDt; r.bc=t.ballisticCoefficient;
    const double coordinate=std::fmax(std::fmax(std::abs(r.start.x),std::abs(r.start.y)),std::abs(r.start.z));
    r.tolerance=0.002+coordinate*0.0000005+Length(r.expected)*0.00002;
    r.collision=ReadImpact(t,delta); ++gImpactObserved;
    const auto& s=r.collision;
    if (s.valid!=31) ++gImpactReadFailures;
    if (!r.wrote || !r.baselineVerified) ++gImpactBaselineContacts;
    const auto m=EvaluateImpact(r,t);
    const auto speed=EvaluateContactSpeed(r,t);
    r.speedAvailable=speed.available; r.speedEngineSegment=speed.engineSegment; r.speedStatus=speed.status;
    r.speedLow=speed.available?speed.low:0; r.speedHigh=speed.available?speed.high:0;
    r.speedMean=speed.available?speed.mean:0;
    if (speed.available) { ++gImpactSpeedRanges; if (speed.engineSegment) ++gImpactEngineSegments; }
    r.modelCandidate=m.estimate; r.modelStatus=m.status;
    r.modelTime=m.estimate?m.estimateTime:0; r.modelSpeed=m.estimate?m.estimateSpeed:0;
    if (m.estimate) ++gImpactCandidates; else ++gImpactUnavailable;
    if (!nvo::log::Write("IMPACT_STEP session=%u lifetime=%llu step=%u projectile=%08X source=%08X weapon=%08X ammo=%08X base=%08X target=%08X target_kind=%u region=%d material=%u valid_mask=%u more_contacts=%u impacted=%u applied=%u baseline_verified=%u dt_s=%.9g speed_before_mps=%.9g proposed_full_step_mps=%.9g life_s=%.9g travel_units=%.9g observer_writes=0",
        gSession,r.serial,r.step,r.ref,r.source,r.weapon,r.ammo,r.base,s.target,static_cast<unsigned>(s.targetKind),s.region,s.material,s.valid,s.more?1u:0u,
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
    if (!nvo::log::Write("IMPACT_SPEED session=%u lifetime=%llu step=%u status=%s available=%u engine_segment=%u low_mps=%.9g high_mps=%.9g mean_segment_mps=%.9g interval_dt_s=%.9g flags_read=%u flags=%08X reset_observed=%u point_model_valid=%u contact_time_measured=0 point_association_proven=0 speed_authority=0 damage_replacement=0 observer_writes=0",
        gSession,r.serial,r.step,speed.status,speed.available?1u:0u,speed.engineSegment?1u:0u,
        r.speedLow,r.speedHigh,r.speedMean,speed.available?r.dt:0,s.policyRead?1u:0u,s.flags,r.resetObserved?1u:0u,m.estimate?1u:0u)) ++gImpactLogFailures;
    if (!nvo::log::Write("IMPACT_TERRAIN session=%u lifetime=%llu step=%u samples=%u valid=%u query_ok=%u candidate=(%.9g,%.9g,%.9g) floor=%.9g target=%08X target_kind=%u region=%d flags=%08X contact=(%.9g,%.9g,%.9g) explained_clamp=%u observer_writes=0",
        gSession,r.serial,r.step,r.terrain.samples,r.terrain.valid?1u:0u,r.terrain.queryOk?1u:0u,
        r.terrain.position.x,r.terrain.position.y,r.terrain.position.z,r.terrain.floor,r.terrain.target,static_cast<unsigned>(r.terrain.targetKind),r.terrain.region,r.terrain.flags,
        r.terrain.point.x,r.terrain.point.y,r.terrain.point.z,speed.terrainExplained?1u:0u)) ++gImpactLogFailures;
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
        && s.targetKind==r->collision.targetKind && s.target==r->collision.target
        && s.region==r->collision.region && contactGap<=r->tolerance;
    if (correlated) ++gImpactCorrelated; else ++gImpactUnpaired;
    if (!nvo::log::Write("IMPACT_CALLBACK session=%u lifetime=%llu step=%u status=%s valid_mask=%u target=%08X target_kind=%u region=%d contact=(%.9g,%.9g,%.9g) position=(%.9g,%.9g,%.9g) life_s=%.9g travel_units=%.9g contact_change_units=%.9g age_since_collision_s=%.9g contact_time_measured=0 speed_authority=0 observer_writes=0",
        gSession,t.serial,r->step,correlated?"correlated":"contact_changed_or_unavailable",s.valid,s.target,static_cast<unsigned>(s.targetKind),s.region,
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
    nvo::log::Write("IMPACT_COVERAGE_SUMMARY session=%u reason=%s admitted_lifetimes=%u omitted_lifetimes=%u baseline_contacts=%u max_lifetimes=%u max_extra_detail_rows=544 speed_authority=0 observer_writes=0",
        gSession,reason,gImpactAdmitted,gImpactOmitted,gImpactBaselineContacts,kImpactLives);
    nvo::log::Write("IMPACT_SPEED_SUMMARY session=%u reason=%s available_segment_ranges=%u observed_engine_segments=%u owned_step_ranges=%u damage_replacement=0 observer_writes=0",
        gSession,reason,gImpactSpeedRanges,gImpactEngineSegments,gImpactSpeedRanges-gImpactEngineSegments);
    ImpactReset();
}

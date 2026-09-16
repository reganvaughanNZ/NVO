// Existing observer -> physics -> logger lock order. Only copied hit scalars
// and guarded live projectile reads; no engine callback, damage or Track write.
constexpr unsigned kImpactHitLimit=64;
unsigned gImpactHitSeen{},gImpactHitOmitted{},gImpactHitCandidates{},gImpactHitUnavailable{};
unsigned gImpactHitRegionDifferences{},gImpactHitImmediate{},gImpactHitReads{},gImpactHitLogFailures{};
void ResetImpactHits() noexcept
{
    gImpactHitSeen=gImpactHitOmitted=gImpactHitCandidates=gImpactHitUnavailable=0;
    gImpactHitRegionDifferences=gImpactHitImmediate=gImpactHitReads=gImpactHitLogFailures=0;
}
void ImpactHit(const Track* t,const nvo::physics::HitQuery& q) noexcept
{
    if (gImpactHitSeen==kImpactHitLimit) { ++gImpactHitOmitted; return; }
    ++gImpactHitSeen;
    const auto* r=t?ImpactFind(t->serial):nullptr;
    ImpactSample s{};
    const char* status="untracked_profile";
    bool paired=false,candidate=false;
    const bool identity=t && t->serial==q.lifetime && t->ref==q.projectile && t->source==q.source
        && t->weapon==q.weapon && q.ammo && t->ammo==q.ammo;
    if (t && !identity) status="identity_mismatch";
    else if (identity && !r) status="impact_capture_limit";
    else if (identity) {
        s=ReadImpact(*t);
        if (s.valid!=15) { ++gImpactHitReads; status="contact_read_unavailable"; }
        else if (s.more) status="multiple_contacts";
        else if (s.target!=q.target) status="contact_target_differs";
        else if (t->stopped || r->callbackReported) status="after_impact_callback";
        else if (!r->collisionCaptured) {
            const bool immediate=!t->movementEntries && !t->accountingEntries;
            status=immediate?"pre_movement_contact":"no_collision_sample";
            if (immediate) ++gImpactHitImmediate;
        } else {
            const bool stable=r->collision.valid==31 && !r->collision.more
                && r->collision.target==s.target && r->collision.region==s.region
                && Length(Add(s.point,Mul(r->collision.point,-1)))<=r->tolerance;
            paired=stable;
            candidate=paired && r->modelCandidate;
            status=!stable?"collision_snapshot_changed":candidate?"paired_model_candidate":"paired_model_unavailable";
        }
    }
    const bool contactValid=(s.valid&8)!=0;
    const bool regionsKnown=identity && contactValid && !s.more && s.target==q.target
        && s.region>=0 && q.region>=0;
    const bool differs=regionsKnown && s.region!=q.region;
    if (differs) ++gImpactHitRegionDifferences;
    if (candidate) ++gImpactHitCandidates; else ++gImpactHitUnavailable;
    bool hitPositionValid=true;
    for (float value:q.position) if (!std::isfinite(value) || std::abs(value)>1e7f) hitPositionValid=false;
    const Vec hitPosition=hitPositionValid?Vec{q.position[0],q.position[1],q.position[2]}:Vec{};
    if (!nvo::log::Write("IMPACT_HIT session=%u context=%u lifetime=%llu phase=copy_input status=%s projectile=%08X source=%08X target=%08X weapon=%08X ammo=%08X hit_region=%d contact_region=%d contact_valid=%u regions_known=%u regions_differ=%u hit_flags=%08X observer_writes=0",
        gSession,q.context,q.lifetime,status,q.projectile,q.source,q.target,q.weapon,q.ammo,q.region,s.region,contactValid?1u:0u,regionsKnown?1u:0u,differs?1u:0u,q.flags)) ++gImpactHitLogFailures;
    if (!nvo::log::Write("IMPACT_HIT_MODEL session=%u context=%u lifetime=%llu collision_paired=%u candidate_available=%u model_status=%s candidate_speed_mps=%.9g candidate_time_s=%.9g callback_seen=%u contact_time_measured=0 speed_authority=0 region_authority=0 damage_replacement=0 observer_writes=0",
        gSession,q.context,q.lifetime,paired?1u:0u,candidate?1u:0u,r?r->modelStatus:"unavailable",candidate?r->modelSpeed:0,candidate?r->modelTime:0,r && r->callbackReported?1u:0u)) ++gImpactHitLogFailures;
    if (!nvo::log::Write("IMPACT_HIT_POSITION session=%u context=%u lifetime=%llu hit_position_valid=%u hit=(%.9g,%.9g,%.9g) contact_valid=%u contact=(%.9g,%.9g,%.9g) observer_writes=0",
        gSession,q.context,q.lifetime,hitPositionValid?1u:0u,hitPosition.x,hitPosition.y,hitPosition.z,contactValid?1u:0u,s.point.x,s.point.y,s.point.z)) ++gImpactHitLogFailures;
}
void SummarizeImpactHits(const char* reason) noexcept
{
    nvo::log::Write("IMPACT_HIT_SUMMARY session=%u reason=%s queries=%u candidates=%u unavailable=%u region_differences=%u pre_movement_contacts=%u optional_read_failures=%u omitted_queries=%u log_write_failures=%u max_queries=%u speed_authority=0 region_authority=0 damage_replacement=0 observer_writes=0",
        gSession,reason,gImpactHitSeen,gImpactHitCandidates,gImpactHitUnavailable,gImpactHitRegionDifferences,gImpactHitImmediate,gImpactHitReads,gImpactHitOmitted,gImpactHitLogFailures,kImpactHitLimit);
}

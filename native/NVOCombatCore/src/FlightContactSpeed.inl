// Diagnostic segment-speed evidence. No contact-time/point/region authority.
// An off-curve surface point cannot select a time on our RK4 trajectory. Keep
// the entire verified step's speed interval instead of widening point tolerance.
struct ContactSpeed {
    const char* status{"snapshot_unavailable"};
    bool available{}, engineSegment{}, terrainExplained{};
    double low{}, high{}, mean{}, duration{};
    static constexpr bool damageAuthority=false;
};
bool ContactFinite(Vec v) noexcept
{ return std::isfinite(v.x) && std::isfinite(v.y) && std::isfinite(v.z); }
ContactSpeed EvaluateContactSpeed(const ImpactRecord& r,const Track& profile) noexcept
{
    ContactSpeed out{};
    const auto& s=r.collision;
    if (s.valid!=31 || !s.policyRead) return out;
    const bool world=s.targetKind==ImpactTargetKind::World && !s.target && s.region==-1;
    const bool reference=s.targetKind==ImpactTargetKind::Reference && s.target;
    if (!world && !reference) return out;
    out.status="unsupported_contact";
    // Hitscan, stuck, engine-gravity and AlwaysHit/redirected contacts do not
    // inherit this ordinary, zero-engine-gravity bullet segment contract.
    if (s.more || (s.flags&0x1047u)) return out;
    out.status="invalid_inputs";
    if (!(std::isfinite(r.dt) && r.dt>0 && r.dt<=0.25)
        || !(std::isfinite(r.tolerance) && r.tolerance>0)
        || !(std::isfinite(gConfig.units) && gConfig.units>0)
        || !(std::isfinite(gConfig.gravity) && gConfig.gravity>=0 && gConfig.gravity<=30)
        || !ContactFinite(r.start) || !ContactFinite(r.expected)
        || !ContactFinite(r.before) || !ContactFinite(r.full)
        || !ContactFinite(s.position) || !ContactFinite(s.point) || !ContactFinite(s.accounting)) return out;
    const double length=Length(r.expected),before=Length(r.before),after=Length(r.full);
    if (!(std::isfinite(length) && length>0 && std::isfinite(before) && before>0
        && std::isfinite(after) && after>0)) return out;
    out.status="movement_unverified";
    // Exact pending call / identity / no prior contacts are checked by the
    // caller. These are the same full-endpoint/accounting checks used in flight.
    if (!r.resetObserved) return out;
    const Vec endpoint=Add(r.start,r.expected);
    const bool ordinary=Length(Add(s.position,Mul(endpoint,-1)))<=r.tolerance
        && Length(Add(s.accounting,Mul(r.expected,-1)))<=r.tolerance;
    if (!ordinary) {
        const auto& terrain=r.terrain;
        // Inspected engine 00930155..00930186 copies floor into Z iff
        // floor-candidate.Z > 30, even if the height query returned false.
        // An actual same-contact snapshot is mandatory: never infer this from
        // a conveniently vertical error alone, or modify the engine's clamp.
        if (terrain.samples!=1 || !terrain.valid || terrain.targetKind!=s.targetKind
            || terrain.target!=s.target
            || terrain.region!=s.region || terrain.flags!=s.flags
            || !ContactFinite(terrain.position) || !ContactFinite(terrain.point)
            || !std::isfinite(terrain.floor)
            || Length(Add(terrain.point,Mul(s.point,-1)))>r.tolerance
            || Length(Add(terrain.position,Mul(endpoint,-1)))>r.tolerance
            || !(terrain.floor-terrain.position.z>30.0)) return out;
        const Vec corrected{terrain.position.x,terrain.position.y,terrain.floor};
        if (Length(Add(s.position,Mul(corrected,-1)))>r.tolerance
            || Length(Add(s.accounting,Mul(Add(corrected,Mul(r.start,-1)),-1)))>r.tolerance) return out;
        out.terrainExplained=true;
    }
    out.duration=r.dt;
    out.mean=length/(r.dt*gConfig.units);
    // Numerical comparison allowance only, not a new collision-point tolerance
    // or a certified floating-point error bound for the physical world.
    constexpr double numericSpeed=0.00001;
    if (!r.wrote && !r.baselineVerified && r.step==0) {
        out.status="baseline_vector_mismatch";
        if (Length(Add(r.before,Mul(r.full,-1)))>numericSpeed
            || Length(Add(Mul(r.before,r.dt*gConfig.units),Mul(r.expected,-1)))>r.tolerance) return out;
        // The first step is an unchanged, observed engine translation. Report
        // its mean speed; do not backdate NVO drag, claim a launch speed, or
        // promote baselineVerified on a projectile that has already collided.
        out.low=std::fmax(0.0,out.mean-numericSpeed);
        out.high=out.mean+numericSpeed;
        out.engineSegment=true;
        out.status="observed_engine_segment";
    } else {
        out.status="owned_segment_unverified";
        if (!r.wrote || !r.baselineVerified
            || (profile.dragModel!=1 && profile.dragModel!=7)
            || !std::isfinite(profile.ballisticCoefficient) || profile.ballisticCoefficient<0.05
            || profile.ballisticCoefficient>2 || !std::isfinite(gConfig.density)
            || gConfig.density<0 || gConfig.density>5 || !std::isfinite(gConfig.sound)
            || gConfig.sound<250 || gConfig.sound>450 || before>gConfig.sound*4.9) return out;
        Vec reproduced=r.before;
        const Vec displacement=Mul(Integrate(reproduced,r.dt,profile),gConfig.units);
        if (!ContactFinite(reproduced) || !ContactFinite(displacement)
            || Length(Add(reproduced,Mul(r.full,-1)))>numericSpeed
            || Length(Add(displacement,Mul(r.expected,-1)))>r.tolerance) return out;
        // Drag always opposes velocity, so d|v|/dt <= g. Applying that inequality
        // forward from the start AND backwards from the end encloses every
        // intermediate speed: max(0, end-g*dt) <= |v(t)| <= start+g*dt.
        // Unlike min/max of endpoint speeds this also covers an upward shot
        // slowing through its apex. Still an estimate of the authored ODE.
        out.low=std::fmax(0.0,after-gConfig.gravity*r.dt-numericSpeed);
        out.high=before+gConfig.gravity*r.dt+numericSpeed;
        if (out.low>before || after>out.high || out.low>out.high) return out;
        out.status="owned_step_speed_range";
    }
    out.available=true;
    return out;
}

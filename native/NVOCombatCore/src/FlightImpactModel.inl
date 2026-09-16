// Pure diagnostic calculation, included by FlightImpact.inl and offline replay.
// No engine calls, writes, or exact contact timestamp. Profile units uncalibrated.
struct ImpactModel {
    const char* status{"optional_snapshot_unavailable"};
    bool geometry{}, estimate{}, endpointMatches{}, accountingMatches{};
    double fraction{}, offChord{}, pointGap{}, endpointError{}, accountingError{};
    double estimateTime{}, estimateSpeed{}, modelGap{};
};
double ImpactDot(Vec a, Vec b) noexcept { return a.x*b.x+a.y*b.y+a.z*b.z; }
ImpactModel EvaluateImpact(const ImpactRecord& r,const Track& profile) noexcept
{
    ImpactModel m{}; const auto& s=r.collision;
    const double length=Length(r.expected);
    if (s.valid!=31 || !(length>0) || !std::isfinite(length)) return m;
    const Vec toPoint=Add(s.point,Mul(r.start,-1));
    m.fraction=ImpactDot(toPoint,r.expected)/(length*length);
    m.offChord=Length(Add(toPoint,Mul(r.expected,-m.fraction)));
    m.pointGap=Length(Add(s.position,Mul(s.point,-1)));
    // BeforeAccounting retains the full endpoint. ShowOff later relocates the
    // projectile to contact before dispatching its impact callback.
    m.endpointError=Length(Add(s.position,Mul(Add(r.start,r.expected),-1)));
    m.accountingError=Length(Add(s.accounting,Mul(r.expected,-1)));
    m.endpointMatches=m.endpointError<=r.tolerance;
    m.accountingMatches=m.accountingError<=r.tolerance;
    m.geometry=std::isfinite(m.fraction) && m.fraction>=0 && m.fraction<=1
        && m.offChord<=r.tolerance && m.endpointMatches && m.accountingMatches && !s.more;
    m.status=s.more?"multiple_contacts":!r.wrote || !r.baselineVerified?"engine_baseline_contact":
        !m.geometry?"contact_geometry_unverified":"model_candidate_unavailable";
    if (!m.geometry || !r.wrote || !r.baselineVerified || !(r.dt>0 && r.dt<=0.25)
        || !(ImpactDot(r.before,r.expected)>0 && ImpactDot(r.full,r.expected)>0)) return m;
    const Vec direction=Mul(r.expected,1/length);
    const double desired=m.fraction*length;
    double low=0,high=r.dt;
    for (unsigned i=0;i<24;++i) {
        const double mid=(low+high)*0.5;
        Vec velocity=r.before;
        const Vec displacement=Mul(Integrate(velocity,mid,profile),gConfig.units);
        if (ImpactDot(displacement,direction)<desired) low=mid; else high=mid;
    }
    m.estimateTime=(low+high)*0.5;
    Vec velocity=r.before;
    const Vec displacement=Mul(Integrate(velocity,m.estimateTime,profile),gConfig.units);
    m.estimateSpeed=Length(velocity);
    m.modelGap=Length(Add(Add(r.start,displacement),Mul(s.point,-1)));
    m.estimate=std::isfinite(m.estimateSpeed) && m.estimateSpeed>0 && m.modelGap<=r.tolerance;
    m.status=m.estimate?"model_estimate_only":"model_path_differs";
    return m;
}

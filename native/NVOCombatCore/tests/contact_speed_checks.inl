Check(baselineSeed.serial && ownedSeed.serial,"both captured producer kinds available");
static_assert(!ContactSpeed::damageAuthority,"diagnostics cannot authorize damage");
auto good=ownedSeed; auto profile=ownedTrack;
auto negative=[&](ImpactRecord bad,const char* why) { Check(!EvaluateContactSpeed(bad,profile).available,why); };
auto bad=good; bad.collision.valid=15; negative(bad,"partial snapshot");
bad=good; bad.collision.policyRead=false; negative(bad,"unread flags");
for (unsigned flag:{1u,2u,4u,0x40u,0x1000u}) { bad=good; bad.collision.flags|=flag; negative(bad,"unsupported projectile policy"); }
bad=good; bad.collision.more=true; negative(bad,"multiple contacts");
bad=good; bad.collision.target=0; negative(bad,"missing target");
bad=good; bad.collision.targetKind=ImpactTargetKind::Invalid; negative(bad,"invalid target classification");
bad=good; bad.collision.targetKind=ImpactTargetKind::World; negative(bad,"nonzero world target");
bad=good; bad.collision.target=0; bad.collision.targetKind=ImpactTargetKind::World; bad.collision.region=0; negative(bad,"world contact with body region");
bad=good; bad.resetObserved=false; negative(bad,"unobserved movement reset branch");
bad=good; bad.collision.position.x+=10; negative(bad,"full endpoint changed");
bad=good; bad.collision.accounting.y+=10; negative(bad,"accounting changed");
bad=good; bad.expected.x+=10; negative(bad,"expected displacement changed");
bad=good; bad.full.z+=1; negative(bad,"solver endpoint velocity changed");
bad=good; bad.before.x+=1; negative(bad,"solver start velocity changed");
for(double dt:{0.0,-1.0,0.251,std::numeric_limits<double>::quiet_NaN()}) { bad=good; bad.dt=dt; negative(bad,"invalid timestep"); }
bad=good; bad.collision.point.x=std::numeric_limits<double>::infinity(); negative(bad,"invalid surface point");
bad=good; bad.wrote=false; negative(bad,"inconsistent movement ownership");
bad=good; bad.baselineVerified=false; negative(bad,"missing baseline");
auto base=EvaluateContactSpeed(baselineSeed,baselineTrack);
Check(base.available && base.engineSegment && base.low<=base.mean && base.high>=base.mean,"observed engine mean enclosed");
bad=baselineSeed; bad.before.x+=1;
Check(!EvaluateContactSpeed(bad,baselineTrack).available,"baseline vector must reconstruct actual translation");
// A surface point outside the curve must not be promoted into a point estimate.
bad=good; bad.collision.point.z+=10;
auto off=EvaluateContactSpeed(bad,profile);
Check(off.available && !EvaluateImpact(bad,profile).estimate,"off-path retains segment range only");
auto original=EvaluateContactSpeed(good,profile);
Check(off.low==original.low && off.high==original.high,"untrusted point cannot select speed/time");
// Separately observed pre-clamp candidate, unchanged contact and exact Z-only
// correction are required to explain a later full-endpoint discrepancy.
auto clamp=good;
clamp.terrain.samples=1; clamp.terrain.valid=true; clamp.terrain.queryOk=true;
clamp.terrain.position=clamp.collision.position; clamp.terrain.floor=clamp.terrain.position.z+100;
clamp.terrain.target=clamp.collision.target; clamp.terrain.flags=clamp.collision.flags;
clamp.terrain.targetKind=clamp.collision.targetKind;
clamp.terrain.region=clamp.collision.region; clamp.terrain.point=clamp.collision.point;
clamp.collision.position.z=clamp.terrain.floor;
clamp.collision.accounting=Add(clamp.collision.position,Mul(clamp.start,-1));
auto explained=EvaluateContactSpeed(clamp,profile);
Check(explained.available && explained.terrainExplained,"explicit observed terrain clamp");
Check(explained.low==original.low && explained.high==original.high,"post-collision clamp adds no flight energy");
bad=clamp; bad.terrain.valid=false; negative(bad,"no inferred terrain evidence");
bad=clamp; bad.terrain.samples=2; negative(bad,"duplicate terrain observation");
bad=clamp; ++bad.terrain.target; negative(bad,"terrain target mismatch");
bad=clamp; bad.terrain.targetKind=ImpactTargetKind::World; negative(bad,"terrain target kind mismatch");
bad=clamp; ++bad.terrain.region; negative(bad,"terrain region mismatch");
bad=clamp; bad.terrain.flags^=0x100; negative(bad,"terrain flags mismatch");
bad=clamp; bad.terrain.point.z+=10; negative(bad,"terrain contact mismatch");
bad=clamp; bad.terrain.position.x+=10; negative(bad,"terrain candidate mismatch");
bad=clamp; bad.terrain.floor+=10; negative(bad,"terrain final height mismatch");
bad=clamp; bad.collision.accounting.x+=10; negative(bad,"unrelated final accounting mutation");
bad=clamp; bad.terrain.floor=bad.terrain.position.z+30; negative(bad,"strict terrain threshold");
// Failed queries still take this engine branch. Keep their actual result flag.
auto failedQuery=clamp; failedQuery.terrain.queryOk=false;
Check(EvaluateContactSpeed(failedQuery,profile).terrainExplained,"observed failed-query clamp");
// A separate numerical trajectory samples the ENTIRE interval, including an
// upward low-speed gravity-only trajectory with an interior zero-speed apex.
unsigned numericalCases=0,numericalSamples=0;
for (unsigned drag:{1u,7u}) for(double density:{0.0,1.225,5.0})
for (double dt:{0.001,0.016,0.079,0.25}) for (double bc:{0.05,0.155,0.209,2.0})
for (Vec initial:{Vec{387.0,0,1},Vec{0,0,0.8},Vec{0,0,-40},Vec{1600,0,300}}) {
    gConfig={70,9.80665,density,340.294};
    auto r=good; auto t=profile; t.dragModel=drag; t.ballisticCoefficient=bc;
    r.dt=dt; r.before=initial; r.full=initial; r.expected=Mul(Integrate(r.full,dt,t),70);
    r.collision.position=Add(r.start,r.expected); r.collision.accounting=r.expected;
    const auto range=EvaluateContactSpeed(r,t);
    Check(range.available,"synthetic supported step"); ++numericalCases;
    Vec v=initial;
    for(unsigned i=0;i<=100;++i) {
        const auto speed=Length(v);
        Check(speed>=range.low-0.00001 && speed<=range.high+0.00001,"sampled speed inside whole-step range"); ++numericalSamples;
        if(i<100) Integrate(v,dt/100,t);
    }
}
gConfig={70,9.80665,1.225,340.294};
// Exercise the production cache and hit join with fixture reads, including
// stale identity and changed point/flags. No speed evidence survives reload.
auto cache=[&](const ImpactRecord& r,Track t) {
    ImpactReset(); nvo::log::rows.clear();
    t.serial=r.serial; t.ref=r.ref; t.source=r.source; t.weapon=r.weapon; t.ammo=r.ammo; t.base=r.base;
    t.steps=r.step; t.wrote=r.wrote; t.baselineVerified=r.baselineVerified; t.stepResetObserved=r.resetObserved;
    t.contactTerrain=r.terrain;
    t.pendingDt=r.dt; t.startPos=r.start; t.expected=r.expected; t.velocity=r.before; t.proposedVelocity=r.full;
    ImpactEnroll(t); fixture=r.collision; ImpactCollision(t,nullptr);
    fixture.valid=15; fixture.position=fixture.point;
    nvo::physics::HitQuery q{gSession,1,r.serial,r.ref,r.source,r.collision.target,r.weapon,r.ammo,r.collision.region,0,{}};
    auto available=[&](Track* track,const nvo::physics::HitQuery& query) {
        ImpactHit(track,query);
        return nvo::log::rows.back().find("available=1 ")!=std::string::npos;
    };
    Check(available(&t,q),"paired hit exposes only bounded evidence");
    auto wrong=q; ++wrong.ammo; Check(!available(&t,wrong),"wrong ammo refuses range");
    wrong=q; ++wrong.lifetime; Check(!available(&t,wrong),"wrong lifetime refuses range");
    wrong=q; ++wrong.target; Check(!available(&t,wrong),"wrong target refuses range");
    wrong=q; wrong.target=0; Check(!available(&t,wrong),"zero actor query refuses range");
    fixture.targetKind=ImpactTargetKind::World; Check(!available(&t,q),"world contact cannot pair to actor hit"); fixture.targetKind=r.collision.targetKind;
    fixture.target=0; fixture.targetKind=ImpactTargetKind::World; wrong=q; wrong.target=0;
    Check(!available(&t,wrong),"world zero-id contact cannot pair to zero-id actor query");
    fixture.target=r.collision.target; fixture.targetKind=r.collision.targetKind;
    fixture.flags|=0x1000; Check(!available(&t,q),"changed projectile policy refuses range"); fixture.flags=r.collision.flags;
    fixture.point.z+=10; Check(!available(&t,q),"changed contact refuses cached range"); fixture.point=r.collision.point;
    ImpactEvent(t,false); Check(!available(&t,q),"after callback refuses range");
    ImpactReset(); Check(!available(&t,q),"reload clears cached evidence");
    ImpactEnroll(t); t.movementEntries=t.accountingEntries=0;
    Check(!available(&t,q),"pre-movement contact remains unknown");
    Check(!available(nullptr,q),"untracked projectile remains unknown");
};
cache(baselineSeed,baselineTrack); cache(ownedSeed,ownedTrack); cache(clamp,ownedTrack);
// Callback correlation also carries contact kind, even when numeric IDs match.
ImpactReset(); auto correlationTrack=ownedTrack; correlationTrack.serial=900;
auto correlation=ownedSeed; correlation.serial=900; ImpactEnroll(correlationTrack);
fixture=correlation.collision; ImpactCollision(correlationTrack,nullptr);
fixture.valid=15; fixture.position=fixture.point; fixture.targetKind=ImpactTargetKind::World;
ImpactEvent(correlationTrack,false); Check(gImpactCorrelated==0 && gImpactUnpaired==1,"callback target kind mismatch");
// Diagnostic cap must refuse rather than recycling an earlier lifetime.
ImpactReset();
for(U64 id=1;id<=33;++id) { auto t=ownedTrack; t.serial=id; ImpactEnroll(t); }
Check(gImpactAdmitted==32 && gImpactOmitted==1 && !ImpactFind(33),"bounded cache cannot reuse or exceed capacity");
ImpactReset(); Check(!ImpactFind(1),"clear cache after cap");
printf("{\"checks\":%u,\"numerical_cases\":%u,\"numerical_samples\":%u,\"cache_join_checks\":true,\"game_loaded\":false}\n",checks,numericalCases,numericalSamples);

#include "ArmourModel.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <random>
using namespace nvo::model;
namespace {
unsigned checks{};
void Check(bool pass, const char* name) {
    if (!pass) { std::printf("FAIL %s\n", name); std::exit(1); }
    ++checks; std::printf("PASS %s\n", name);
}
bool Near(double x, double y) { return std::abs(x-y) <= 1e-9 * (1 + std::abs(y)); }
Measurement M(double x, Unit u) { return {x,u,true}; }
Context ContextOf() {
    Context c; c.session=1; c.component=1; c.application=1; c.source=20; c.target=30;
    c.actualRegion=Region::Torso; c.mode=Mode::RealTime;
    c.identitiesVerified=c.pathVerified=c.modifierOwnershipVerified=c.armourComplete=true; return c;
}
Threat Bullet() {
    Threat t; t.family=Family::Kinetic; t.construction=Construction::Ball;
    t.mass=M(0.01,Unit::Kilograms); t.diameter=M(0.01,Unit::Metres);
    t.impactSpeed=M(std::sqrt(200000.0),Unit::MetresPerSecond);
    t.profileVerified=t.contactVerified=t.unitsCalibrated=true; t.woundPayload=true; return t;
}
TargetProfile Target(Unit unit=Unit::Joules) {
    TargetProfile a; a.anatomy=Anatomy::Biological; a.verified=true; a.inputUnit=unit;
    a.directHpPerUnit=0.1; a.bluntHpPerJoule=0.01; a.limbPerHp=0.5; a.tissueCoupling=1; return a;
}
Layer Armour(std::uint64_t id=1, Region region=Region::Torso) {
    Layer l; l.instance=id; l.coverage=Cover(region); l.condition=1; l.profileVerified=true;
    auto& k=l.response[0]; k.supported=true; k.unit=Unit::Joules;
    k.resistanceJ={{800,500,1200,800}}; k.bluntFraction=0.1; k.wearPerAbsorbedUnit=0.0001;
    for (unsigned i=1;i<5;++i) {
        auto& r=l.response[i]; r.supported=true; r.unit=Unit::Dose;
        r.shieldFraction=i==1 ? 0.8 : i==2 ? 0.4 : i==3 ? 0.75 : 0.25;
        r.wearPerAbsorbedUnit=0;
    }
    return l;
}
Threat Dose(Family f, double dose=100) {
    Threat t; t.family=f; t.profileVerified=true; t.dose=M(dose,Unit::Dose);
    t.doseRate=M(dose,Unit::DosePerGameSecond); t.duration=M(1,Unit::GameSeconds); return t;
}
bool EmptyRejected(const Preview& p) {
    return p.status!=Status::PreviewOnly && p.directHp==0 && p.limb==0 && p.incident==0 &&
           p.wear.empty() && !p.biologicalWoundEligible && !p.woundPayloadEligible;
}
}
int main() {
    static_assert(!kGameplayWrites);
    auto c=ContextOf(); auto b=Bullet(); auto a=Target(); auto l=Armour();
    const auto bare=Resolve(c,b,a,{});
    Check(bare.status==Status::PreviewOnly && Near(bare.incident,1000) && Near(bare.directHp,100),"bare kinetic preview with explicit SI inputs");
    const auto covered=Resolve(c,b,a,{l});
    Check(Near(covered.residual,200) && Near(covered.bluntJoules,80) && Near(covered.directHp,20.8),"layer separates residual wound energy from transmitted blunt energy");
    Check(Near(covered.limb,10.4) && Near(covered.wear[0].loss,0.08),"limb and instance-specific wear remain separate preview fields");
    auto hp=b; hp.construction=Construction::HP;
    const auto stopped=Resolve(c,hp,a,{l});
    Check(stopped.residual==0 && Near(stopped.directHp,1) && !stopped.armourPenetrated && !stopped.woundPayloadEligible,
          "stopped HP can transmit blunt trauma but cannot deliver wound poison");
    auto ap=b; ap.construction=Construction::AP;
    Check(Resolve(c,ap,a,{l}).residual>covered.residual && stopped.residual<covered.residual,
          "explicit AP Ball HP response distinctions");
    c.actualRegion=Region::Head;
    Check(Near(Resolve(c,b,a,{l}).directHp,bare.directHp),"body armour does not cover head");
    Check(Near(Resolve(c,b,a,{l,Armour(2,Region::Head)}).directHp,covered.directHp),"helmet covers reported head separately");
    c=ContextOf(); auto damaged=l; damaged.condition=0.25;
    Check(Resolve(c,b,a,{damaged}).residual>covered.residual,"damaged fixture armour offers less resistance");
    auto broken=l; broken.condition=0;
    const auto brokenResult=Resolve(c,b,a,{broken});
    Check(Near(brokenResult.directHp,bare.directHp) && brokenResult.wear[0].loss==0,"zero condition has no fixture resistance or further wear");
    Check(Resolve(c,b,a,{l,Armour(2)}).residual==0,"layers absorb without increasing incident energy");
    auto robot=a; robot.anatomy=Anatomy::Mechanical;
    auto mechanical=Resolve(c,b,robot,{});
    Check(mechanical.mechanicalDamage && !mechanical.biologicalWoundEligible && !mechanical.woundPayloadEligible,"robot receives mechanical preview without biological payload");
    auto vats=c; vats.mode=Mode::Vats;
    Check(Near(Resolve(vats,b,a,{l}).directHp,covered.directHp),"pure model has identical VATS and real-time armour rules");
    auto doseTarget=Target(Unit::Dose);
    const auto laser=Resolve(c,Dose(Family::Laser),doseTarget,{l});
    const auto plasma=Resolve(c,Dose(Family::Plasma),doseTarget,{l});
    const auto blast=Resolve(c,Dose(Family::Blast),doseTarget,{l});
    Check(Near(laser.directHp,2) && Near(plasma.directHp,6) && Near(blast.directHp,7.5),"laser plasma blast select different authored responses");
    Check(!laser.armourPenetrated && !plasma.woundPayloadEligible && laser.unit==Unit::Dose,"non-kinetic dose is not joules or bullet penetration");
    auto badPayload=Dose(Family::Plasma); badPayload.woundPayload=true;
    Check(EmptyRejected(Resolve(c,badPayload,doseTarget,{l})),"unmodelled non-kinetic wound payload is rejected rather than discarded");
    auto flame=Dose(Family::Flame,80); flame.duration=M(2,Unit::GameSeconds);
    auto full=Resolve(c,flame,doseTarget,{l});
    flame.duration=M(0.02,Unit::GameSeconds); double sum=0;
    for (unsigned i=0;i<100;++i) sum+=Resolve(c,flame,doseTarget,{l}).directHp;
    Check(Near(full.directHp,4) && Near(sum,full.directHp),"fixed-state flame dose independent of interval partition");
    double beams=0;
    for (unsigned i=1;i<=3;++i) { auto cc=c; cc.component=i; beams+=Resolve(cc,Dose(Family::Laser),doseTarget,{}).directHp; }
    Check(Near(beams,30),"three distinct beam previews preserve component multiplicity");
    auto pellet=b; pellet.construction=Construction::Pellet; pellet.mass.value/=8;
    double pelletEnergy=0; for (unsigned i=0;i<8;++i) pelletEnergy+=Resolve(c,pellet,a,{}).incident;
    Check(Near(pelletEnergy,bare.incident),"per-pellet mass conserves total fixture energy");
    auto zero=b; zero.impactSpeed.value=0;
    Check(Resolve(c,zero,a,{l}).directHp==0 && !Resolve(c,zero,a,{l}).biologicalWoundEligible,"zero incident is not a wound");
    for (double bad : {unknown,-1.0,std::numeric_limits<double>::infinity()}) {
        auto t=b; t.mass.value=bad; Check(EmptyRejected(Resolve(c,t,a,{l})),"invalid mass rejected without partial result");
    }
    auto t=b; t.mass.unit=Unit::Joules;
    Check(EmptyRejected(Resolve(c,t,a,{l})),"mixed units rejected");
    t=b; t.impactSpeed.verified=false;
    Check(EmptyRejected(Resolve(c,t,a,{l})),"missing speed is not zero or muzzle speed");
    t=b; t.contactVerified=false;
    Check(EmptyRejected(Resolve(c,t,a,{l})),"geometry-rejected contact cannot acquire authority");
    t=b; t.unitsCalibrated=false;
    Check(EmptyRejected(Resolve(c,t,a,{l})),"uncalibrated game units rejected");
    t=b; t.impactSpeed.value=std::numeric_limits<double>::max();
    Check(EmptyRejected(Resolve(c,t,a,{l})),"incident arithmetic overflow rejected");
    auto cc=c; cc.actualRegion=Region::Unknown;
    Check(EmptyRejected(Resolve(cc,b,a,{l})),"unknown actual region is not torso");
    cc=c; cc.mode=Mode::Unknown;
    Check(EmptyRejected(Resolve(cc,b,a,{l})),"unknown VATS mode rejected");
    cc=c; cc.modifierOwnershipVerified=false;
    Check(EmptyRejected(Resolve(cc,b,a,{l})),"unowned critical or difficulty modifier rejects preview");
    cc=c; cc.armourComplete=false;
    Check(EmptyRejected(Resolve(cc,b,a,{})),"missing armour snapshot is not bare skin");
    auto invalid=l; invalid.condition=1.1;
    Check(EmptyRejected(Resolve(c,b,a,{invalid})),"condition outside normalized domain rejected");
    invalid=l; invalid.profileVerified=false;
    Check(EmptyRejected(Resolve(c,b,a,{invalid})),"unknown worn armour is unsupported");
    Check(EmptyRejected(Resolve(c,b,a,{l,l})),"duplicate armour instance cannot absorb twice");
    invalid=l; invalid.response[0].unit=Unit::Dose;
    Check(EmptyRejected(Resolve(c,b,a,{invalid})),"material and incident units must agree");
    invalid=l; invalid.response[1].shieldFraction=1.1;
    Check(EmptyRejected(Resolve(c,Dose(Family::Laser),doseTarget,{invalid})),"amplifying shield fraction rejected");
    invalid=l; invalid.response[0].wearPerAbsorbedUnit=10;
    Check(Resolve(c,b,a,{invalid}).wear[0].loss==1,"wear is capped by remaining condition");
    invalid=Armour(2); invalid.response[0].wearPerAbsorbedUnit=unknown;
    Check(EmptyRejected(Resolve(c,b,a,{l,invalid})),"late invalid layer returns no earlier partial result");
    t=Dose(Family::Flame); t.duration.unit=Unit::Metres;
    Check(EmptyRejected(Resolve(c,t,doseTarget,{l})),"flame duration requires simulated seconds");
    t=b; t.family=Family::Unsupported;
    Check(EmptyRejected(Resolve(c,t,a,{l})),"unsupported family cannot become a bullet");
    t=b; t.family=static_cast<Family>(255);
    Check(EmptyRejected(Resolve(c,t,a,{l})),"out of range family rejected before array access");
    auto aa=a; aa.directHpPerUnit=std::numeric_limits<double>::max();
    Check(EmptyRejected(Resolve(c,b,aa,{l})),"HP overflow returns no partial result");
    // Conservation/monotonicity beyond a few hand-picked fixtures.
    std::mt19937 rng(0x3A3B3C); std::uniform_real_distribution<double> value(0,1);
    bool conserved=true, monotonic=true;
    for (unsigned i=0;i<4000;++i) {
        auto q=b; q.mass.value=0.001+value(rng)*0.1; q.impactSpeed.value=value(rng)*2000;
        auto x=l; x.condition=value(rng); x.response[0].resistanceJ[0]=value(rng)*10000;
        auto y=Armour(2); y.condition=value(rng);
        auto r=Resolve(c,q,a,{x,y});
        conserved &= r.status==Status::PreviewOnly && Near(r.residual+r.absorbed,r.incident) && r.bluntJoules<=r.absorbed;
        auto less=x; less.condition*=0.5;
        monotonic &= Resolve(c,q,a,{less}).residual+1e-8>=Resolve(c,q,a,{x}).residual;
    }
    Check(conserved,"4000 seeded layered cases conserve energy");
    Check(monotonic,"4000 seeded cases retain more energy through weaker fixture armour");
    bool deterministic=true;
    for (unsigned i=0;i<10000;++i) deterministic &= Near(Resolve(c,b,a,{l}).directHp,covered.directHp);
    Check(deterministic,"10000 previews unchanged with no diagnostic budget dependency");
    std::printf("RESULT checks=%u failures=0 gameplay_writes=0 synthetic_fixtures=1\n",checks);
    return 0;
}

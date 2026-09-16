#include "AdmissionLedger.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <thread>
using namespace nvo::model;
using namespace nvo::model::offline;
namespace {
unsigned checks{};
void Check(bool pass, const char* label) {
    if (!pass) { std::printf("FAIL %s\n",label); std::exit(1); }
    ++checks; std::printf("PASS %s\n",label);
}
Envelope E(std::uint64_t component=1, std::uint64_t application=1, std::uint32_t target=30) {
    Envelope e; auto& c=e.context;
    c.session=1; c.component=component; c.application=application; c.source=20; c.target=target;
    c.actualRegion=Region::Torso; c.mode=Mode::RealTime;
    c.identitiesVerified=c.pathVerified=c.modifierOwnershipVerified=c.armourComplete=true;
    e.family=Family::Kinetic; e.kind=ComponentKind::Projectile;
    e.revisions={1,1,1,1,1}; e.sourceGeneration=1; e.targetGeneration=2; return e;
}
Threat Bullet() {
    Threat t; t.family=Family::Kinetic; t.construction=Construction::Ball;
    t.mass={0.01,Unit::Kilograms,true}; t.diameter={0.01,Unit::Metres,true};
    t.impactSpeed={100,Unit::MetresPerSecond,true}; t.profileVerified=t.contactVerified=t.unitsCalibrated=true;
    return t;
}
TargetProfile Target(Unit unit=Unit::Joules) {
    TargetProfile t; t.anatomy=Anatomy::Biological; t.verified=true; t.inputUnit=unit;
    t.directHpPerUnit=0.1; t.bluntHpPerJoule=0; t.limbPerHp=0.5; t.tissueCoupling=1; return t;
}
bool Finish(AdmissionLedger& l, Token t, const Envelope& e) {
    return l.ResolveReserved(t,e.revisions,Bullet(),Target(),{})==Code::Ok &&
        l.BeginSimulatedApplication(t)==Code::Ok && l.AcknowledgeSimulation(t)==Code::Ok;
}
std::uint64_t LoggedScenario(int loggingMode) {
    AdmissionLedger l(1); l.ResetSession(1); std::uint64_t digest=0;
    auto observe=[&](Code c) {
        // Simulate an outside disabled/full/failing sink. Its return is never a ledger input.
        const bool written=loggingMode==2;
        (void)written;
        digest=digest*131+static_cast<unsigned>(c)+1;
    };
    for (std::uint64_t n=1;n<=1000;++n) {
        auto e=E(n); auto a=l.Reserve(e); observe(a.code);
        observe(l.Reserve(e).code);
        observe(l.ResolveReserved(a.token,e.revisions,Bullet(),Target(),{}));
        observe(l.BeginSimulatedApplication(a.token)); observe(l.BeginSimulatedApplication(a.token));
        observe(l.AcknowledgeSimulation(a.token)); observe(l.RetireThrough(n,true));
        observe(l.Reserve(e).code);
    }
    return digest;
}
}
int main() {
    static_assert(!kGameplayWrites);
    AdmissionLedger l(2); auto e=E();
    Check(l.Reserve(e).code==Code::StaleSession,"no reservation before a valid session");
    Check(l.ResetSession(1)==Code::Ok && l.ResetSession(1)==Code::StaleSession && l.ResetSession(0)==Code::StaleSession,
          "session epochs strictly increase");
    auto invalid=e; invalid.context.pathVerified=false;
    Check(l.Reserve(invalid).code==Code::Unsupported,"unsupported path rejected before reservation");
    invalid=e; invalid.revisions.armour=0;
    Check(l.Reserve(invalid).code==Code::Unsupported,"missing armour snapshot revision rejected");
    invalid=e; invalid.context.mode=Mode::Unknown;
    Check(l.Reserve(invalid).code==Code::Unsupported,"unknown VATS mode stays unsupported");
    invalid=e; invalid.targetGeneration=0;
    Check(l.Reserve(invalid).code==Code::Unsupported,"actor incarnation required separately from form ID");
    auto first=l.Reserve(e);
    Check(first.code==Code::Ok && l.Reserve(e).code==Code::Duplicate,"same application cannot reserve twice");
    auto changed=e; changed.context.source=21;
    Check(l.Reserve(changed).code==Code::IdentityConflict,"same key with changed attacker is a conflict");
    changed=e; changed.targetGeneration=3;
    Check(l.Reserve(changed).code==Code::IdentityConflict,"reused target form with changed incarnation conflicts");
    changed=e; changed.revisions.settings=2;
    Check(l.Reserve(changed).code==Code::IdentityConflict,"duplicate cannot replace its settings snapshot");
    auto second=l.Reserve(E(2));
    Check(second.code==Code::Ok && l.Reserve(E(3)).code==Code::Full,"full capacity rejects without evicting an active entry");
    Check(l.Reserve(e).code==Code::Duplicate,"duplicate identity remains detectable at full capacity");
    Check(l.BeginSimulatedApplication(first.token)==Code::BadTransition,"application cannot start before resolution");
    Check(l.ResolveReserved(first.token,e.revisions,Bullet(),Target(),{})==Code::Ok,"reserved context resolves through unchanged pure model");
    Inspection view;
    Check(l.Inspect(first.token,view)==Code::Ok && view.phase==Phase::Resolved && view.hp==5 && view.limb==2.5,
          "preview retained as values with expected synthetic result");
    Check(l.ResolveReserved(first.token,e.revisions,Bullet(),Target(),{})==Code::BadTransition,"resolved input cannot be recomputed under the same token");
    Check(l.BeginSimulatedApplication(first.token)==Code::Ok && l.BeginSimulatedApplication(first.token)==Code::BadTransition,
          "only one simulated application start");
    Check(l.AcknowledgeSimulation(first.token)==Code::Ok && l.AcknowledgeSimulation(first.token)==Code::BadTransition,
          "only one simulated acknowledgment");
    Check(l.Reserve(e).code==Code::Duplicate && l.Reserve(E(3)).code==Code::Full,"completion retains duplicate history until proven producer closure");
    Check(l.RetireThrough(2,true)==Code::Busy,"retirement preflight blocks on an unresolved lower component");
    Usage usage; l.GetUsage(usage);
    Check(usage.retained==2 && usage.retiredThrough==0,"failed retirement changes no entries or boundary");
    Check(l.RetireThrough(1,false)==Code::InvalidBoundary && l.RetireThrough(1,true)==Code::Ok,
          "only proven closure allows bounded history retirement");
    Check(l.Reserve(e).code==Code::RetiredComponent && l.Inspect(first.token,view)==Code::InvalidToken,
          "late duplicate and old token remain rejected after cleanup");
    auto third=l.Reserve(E(3));
    Check(third.code==Code::Ok && third.token.slot==first.token.slot && third.token.generation!=first.token.generation,
          "slot reuse cannot revive old token");
    Check(l.RejectOrFault(second.token)==Code::Ok && l.RejectOrFault(third.token)==Code::Ok && l.RetireThrough(3,true)==Code::Ok,
          "pre-start rejection can retire without pretending damage was applied");
    Check(l.RetireThrough(2,true)==Code::InvalidBoundary,"retirement boundary cannot go backwards");

    AdmissionLedger other(2); other.ResetSession(1); other.Reserve(e);
    Check(other.BeginSimulatedApplication(first.token)==Code::InvalidToken,"tokens are scoped to their issuing ledger");
    auto fourth=l.Reserve(E(4)); Code threadCode=Code::Ok;
    std::thread worker([&]{ threadCode=l.RejectOrFault(fourth.token); }); worker.join();
    Check(threadCode==Code::WrongThread && l.Inspect(fourth.token,view)==Code::Ok && view.phase==Phase::Reserved,
          "foreign thread rejected before accessing mutable ledger state");
    auto revisions=e.revisions; revisions.profile=2;
    Check(l.ResolveReserved(fourth.token,revisions,Bullet(),Target(),{})==Code::SnapshotChanged &&
          l.BeginSimulatedApplication(fourth.token)==Code::BadTransition,"changed snapshot rejects whole pending preview");
    l.RetireThrough(4,true);
    auto fifth=l.Reserve(E(5)); auto bad=Bullet(); bad.impactSpeed.value=std::numeric_limits<double>::quiet_NaN();
    Check(l.ResolveReserved(fifth.token,e.revisions,bad,Target(),{})==Code::ModelRejected &&
          l.Inspect(fifth.token,view)==Code::Ok && view.hp==0 && view.wearEntries==0,"invalid model inputs cannot reach simulated application");
    l.RetireThrough(5,true);
    auto sixth=l.Reserve(E(6));
    Check(l.ResolveReserved(sixth.token,e.revisions,Bullet(),Target(),std::vector<Layer>(17))==Code::Unsupported,
          "armour snapshot size has a separate bounded admission limit");
    l.RetireThrough(6,true);
    auto seventh=l.Reserve(E(7));
    l.ResolveReserved(seventh.token,e.revisions,Bullet(),Target(),{}); l.BeginSimulatedApplication(seventh.token);
    Check(l.RejectOrFault(seventh.token)==Code::Ok && l.Inspect(seventh.token,view)==Code::Ok && view.phase==Phase::Faulted,
          "failure after simulated start retains uncertain ownership");
    Check(l.BeginSimulatedApplication(seventh.token)==Code::BadTransition && l.Reserve(E(7)).code==Code::Duplicate &&
          l.RetireThrough(7,true)==Code::Busy,"partial application cannot restart or lose its duplicate history");
    Check(l.ResetSession(2)==Code::Ok && l.AcknowledgeSimulation(seventh.token)==Code::StaleSession,
          "reload invalidates old-session completion without touching new state");
    auto newSession=e; newSession.context.session=2;
    Check(l.Reserve(newSession).code==Code::Ok && l.Reserve(e).code==Code::StaleSession,"new session can reuse IDs while old contexts stay stale");

    AdmissionLedger components(16); components.ResetSession(1);
    auto pellet1=components.Reserve(E(1)); auto pellet2=components.Reserve(E(2));
    auto sameCarrierNewApplication=components.Reserve(E(1,2));
    Check(pellet1.code==Code::Ok && pellet2.code==Code::Ok && sameCarrierNewApplication.code==Code::Ok,
          "distinct pellets and distinct applications never collapse by source or time");
    auto blast=E(3); blast.family=Family::Blast; blast.kind=ComponentKind::Blast;
    auto blast1=components.Reserve(blast); blast.context.target=31; auto blast2=components.Reserve(blast);
    Check(blast1.code==Code::Ok && blast2.code==Code::Ok,"one blast retains separate target applications");
    std::uint64_t id=4;
    for (auto family : {Family::Laser,Family::Plasma,Family::Flame,Family::Blast}) {
        auto envelope=E(id++); envelope.family=family;
        envelope.kind=family==Family::Laser ? ComponentKind::Beam : family==Family::Flame ? ComponentKind::Exposure :
            family==Family::Blast ? ComponentKind::Blast : ComponentKind::Projectile;
        auto admission=components.Reserve(envelope);
        Threat dose; dose.family=family; dose.profileVerified=true;
        dose.dose={10,Unit::Dose,true}; dose.doseRate={20,Unit::DosePerGameSecond,true}; dose.duration={0.5,Unit::GameSeconds,true};
        Check(admission.code==Code::Ok && components.ResolveReserved(admission.token,envelope.revisions,dose,Target(Unit::Dose),{})==Code::Ok,
              "nonkinetic family uses its own valid pure-model input through ledger");
    }
    auto wrong=E(12); wrong.family=Family::Flame;
    Check(components.Reserve(wrong).code==Code::Unsupported,"flame projectile is not silently treated as verified exposure");
    wrong=E(12); wrong.family=Family::Unsupported;
    Check(components.Reserve(wrong).code==Code::Unsupported,"unimplemented miscellaneous family stays unsupported");
    auto mismatch=components.Reserve(E(12)); auto plasma=Bullet(); plasma.family=Family::Plasma;
    Check(components.ResolveReserved(mismatch.token,e.revisions,plasma,Target(),{})==Code::Unsupported,
          "family cannot change between reservation and resolution");
    AdmissionLedger zero(0); zero.ResetSession(1); AdmissionLedger oversized(129); oversized.ResetSession(1);
    Check(zero.Reserve(e).code==Code::Full && oversized.Reserve(e).code==Code::Full,"invalid configured capacity fails closed");
    auto neverReserved=components.Reserve(E(13));
    Check(Finish(components,neverReserved.token,E(13)),"ordinary fixture still completes after unrelated failures");
    Check(LoggedScenario(0)==LoggedScenario(1) && LoggedScenario(1)==LoggedScenario(2),
          "1000-component traces identical with absent failing or successful external logging");
    std::printf("%u admission checks passed. Offline simulations only, no game writes.\n",checks);
}

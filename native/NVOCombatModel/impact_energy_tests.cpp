#include "ImpactEnergy.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
using namespace nvo::energy;
namespace {
unsigned checks{};
void Check(bool ok, const char* label) {
    ++checks;
    if (!ok) { std::fprintf(stderr, "FAIL %s\n", label); std::exit(1); }
}
void Rejected(const Input& i, Reason reason, const char* label) {
    const auto r = Evaluate(i);
    Check(!r.estimate && r.reason == reason && !r.damageAuthority, label);
}
Input Valid() {
    Input i{};
    i.keys = {"FalloutNV.esm:0E3778", "FalloutNV.esm:08ED03", "FalloutNV.esm:08F20F"};
    i.contact = {1, 1, 10, 2, 0xff000001, 0x14, 0x123, 0xe3778, 0x8ed03, 0xb000806};
    i.velocity = i.contact;
    i.profileMappingVerified = i.completeSnapshot = i.movementApplied = i.baselineVerified = i.candidateAvailable = true;
    i.producer = Producer::OwnedSegmentEstimate;
    i.speedUnit = SpeedUnit::MetresPerSimulationSecond; i.clock = Clock::ParentBulletUpdateDelta;
    i.speed = 400; i.dt = .016; i.contactTime = .008; i.unitsPerMetre = 70;
    i.fraction = .5; i.tolerance = .05; i.offChord = i.modelGap = i.endpointError = i.accountingError = .001;
    return i;
}
}
int main() {
    const auto good = Valid(); auto i = good;
    auto r = Evaluate(i);
    Check(r.estimate && std::abs(r.estimate->massKg - .00745187465) < 1e-15, "115 grain conversion");
    Check(r.estimate && std::abs(r.estimate->conditionalJoules - 596.149972) < 1e-8 && !r.damageAuthority, "9mm conditional energy");
    i.keys = {"FalloutNV.esm:004333", "FalloutNV.esm:06B53C", "FalloutNV.esm:08F20A"};
    i.contact.weapon = i.velocity.weapon = 0x4333; i.contact.ammo = i.velocity.ammo = 0x6b53c; i.speed = 800;
    r = Evaluate(i);
    Check(r.estimate && std::abs(r.estimate->massKg - .00952543977) < 1e-15, "147 grain conversion");
    Check(r.estimate && std::abs(r.estimate->conditionalJoules - 3048.1407264) < 1e-8, "308 conditional energy");
    i = good; i.speed = 0; r = Evaluate(i);
    Check(r.estimate && r.estimate->conditionalJoules == 0, "explicit zero differs from absent");
    i.candidateAvailable = false; Rejected(i, Reason::Snapshot, "logged zero sentinel is unavailable");
    for (auto key : {"FalloutNV.esm:13E442", "FalloutNV.esm:13E443", "Other.esm:08ED03", ""}) {
        i = good; i.keys.ammo = key; Rejected(i, Reason::UnsupportedProfile, "no AP HP or foreign inheritance");
    }
    i = good; i.keys.weapon = "FalloutNV.esm:08F217"; Rejected(i, Reason::UnsupportedProfile, "no broad ammo-only match");
    i = good; i.keys.sourceProjectile = "FalloutNV.esm:08F20A"; Rejected(i, Reason::UnsupportedProfile, "wrong original projectile");
    i = good; i.profileMappingVerified = false; Rejected(i, Reason::UnsupportedProfile, "unresolved canonical mapping");
    for (auto member : {&Identity::capture, &Identity::session, &Identity::lifetime}) {
        i = good; ++(i.velocity.*member); Rejected(i, Reason::Identity, "no cross capture/session/lifetime reuse");
    }
    for (auto member : {&Identity::step, &Identity::projectile, &Identity::source, &Identity::target,
            &Identity::weapon, &Identity::ammo, &Identity::base}) {
        i = good; ++(i.velocity.*member); Rejected(i, Reason::Identity, "exact scalar join");
        i = good; i.contact.*member = i.velocity.*member = 0; Rejected(i, Reason::Identity, "incomplete identity");
    }
    for (auto p : {Producer::Unknown, Producer::EngineBaseline, Producer::BeforeMovement}) {
        i = good; i.producer = p; Rejected(i, Reason::Producer, "no muzzle fallback for early contact");
    }
    i = good; i.movementApplied = false; Rejected(i, Reason::Producer, "unowned segment");
    i = good; i.baselineVerified = false; Rejected(i, Reason::Producer, "unverified baseline");
    i = good; i.completeSnapshot = false; Rejected(i, Reason::Snapshot, "missing sample");
    i = good; i.multipleContacts = true; Rejected(i, Reason::Snapshot, "ambiguous multiple contacts");
    for (auto member : {&Input::offChord, &Input::modelGap, &Input::endpointError, &Input::accountingError}) {
        i = good; i.*member = .051; Rejected(i, Reason::Geometry, "do not widen contact tolerance");
        i.*member = unknown; Rejected(i, Reason::Geometry, "nonfinite geometry");
    }
    i = good; i.fraction = 1.01; Rejected(i, Reason::Geometry, "outside segment");
    i = good; i.unitsPerMetre = 100; Rejected(i, Reason::Units, "changed world scale");
    i = good; i.speedUnit = SpeedUnit::EngineUnitsPerSecond; Rejected(i, Reason::Units, "do not treat engine units as metres");
    i = good; i.clock = Clock::Unknown; Rejected(i, Reason::Time, "unknown clock");
    i = good; i.contactTime = .017; Rejected(i, Reason::Time, "time after step");
    i = good; i.contactTime = -1; Rejected(i, Reason::Time, "negative time");
    for (double dt : {0., .251, unknown}) { i = good; i.dt = dt; Rejected(i, Reason::Time, "invalid delta"); }
    for (double speed : {-1., unknown, std::numeric_limits<double>::infinity()}) {
        i = good; i.speed = speed; Rejected(i, Reason::Speed, "invalid speed");
    }
    i = good; i.speed = 1e300; Rejected(i, Reason::Arithmetic, "energy overflow");
    i = good; i.speed = 1e-300; Rejected(i, Reason::Arithmetic, "positive energy underflow");
    i = good; i.speed *= 2; r = Evaluate(i);
    Check(r.estimate && std::abs(r.estimate->conditionalJoules / Evaluate(good).estimate->conditionalJoules - 4) < 1e-14, "speed squared sensitivity");
    Check(!kDamageAuthority && !Result::damageAuthority, "authority cannot be enabled by inputs");
    std::printf("{\"checks_passed\":%u,\"game_loaded\":false,\"damage_authority\":false}\n", checks);
}

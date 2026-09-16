#include "ImpactEnergy.hpp"
#include <cmath>

namespace nvo::energy {
namespace {
// Generated from hash-verified BallistX donor rows, not installed configuration.
#include "ImpactEnergyProfiles.inl"
bool Positive(double v) noexcept { return std::isfinite(v) && v > 0; }
bool Nonnegative(double v) noexcept { return std::isfinite(v) && v >= 0; }
bool Complete(const Identity& i) noexcept {
    return i.capture && i.session && i.lifetime && i.step && i.projectile && i.source
        && i.target && i.weapon && i.ammo && i.base;
}
Result Reject(Reason r) noexcept { return {r, std::nullopt}; }
}
const Profile* FindProfile(const FormKeys& k) noexcept {
    for (const auto& p : kProfiles)
        if (k.weapon == p.keys.weapon && k.ammo == p.keys.ammo && k.sourceProjectile == p.keys.sourceProjectile) return &p;
    return nullptr;
}
bool SameIdentity(const Identity& a, const Identity& b) noexcept {
    return a.capture == b.capture && a.session == b.session && a.lifetime == b.lifetime
        && a.step == b.step && a.projectile == b.projectile && a.source == b.source
        && a.target == b.target && a.weapon == b.weapon && a.ammo == b.ammo && a.base == b.base;
}
Result Evaluate(const Input& i) noexcept {
    const auto* p = FindProfile(i.keys);
    if (!p || !i.profileMappingVerified) return Reject(Reason::UnsupportedProfile);
    if (i.producer != Producer::OwnedSegmentEstimate || !i.movementApplied || !i.baselineVerified)
        return Reject(Reason::Producer);
    if (!Complete(i.contact) || !SameIdentity(i.contact, i.velocity)) return Reject(Reason::Identity);
    if (!i.completeSnapshot || i.multipleContacts || !i.candidateAvailable) return Reject(Reason::Snapshot);
    if (!Positive(i.tolerance) || !Nonnegative(i.fraction) || i.fraction > 1
        || !Nonnegative(i.offChord) || i.offChord > i.tolerance
        || !Nonnegative(i.modelGap) || i.modelGap > i.tolerance
        || !Nonnegative(i.endpointError) || i.endpointError > i.tolerance
        || !Nonnegative(i.accountingError) || i.accountingError > i.tolerance) return Reject(Reason::Geometry);
    // The current donor convention is explicit, not a calibration certificate.
    if (i.speedUnit != SpeedUnit::MetresPerSimulationSecond || i.unitsPerMetre != 70.0)
        return Reject(Reason::Units);
    if (i.clock != Clock::ParentBulletUpdateDelta || !Positive(i.dt) || i.dt > 0.25
        || !Nonnegative(i.contactTime) || i.contactTime > i.dt) return Reject(Reason::Time);
    if (!Nonnegative(i.speed)) return Reject(Reason::Speed);
    const double mass = p->massGrains * kKilogramsPerGrain;
    const double diameter = p->diameterInches * kMetresPerInch;
    const double energy = 0.5 * mass * i.speed * i.speed;
    if (!Positive(mass) || !Positive(diameter) || !Nonnegative(energy)
        || (i.speed > 0 && energy == 0)) return Reject(Reason::Arithmetic);
    return {Reason::None, Estimate{mass, diameter, energy}};
}
const char* ReasonName(Reason r) noexcept {
    switch (r) {
    case Reason::None: return "conditional_estimate_only";
    case Reason::UnsupportedProfile: return "unsupported_profile";
    case Reason::Identity: return "identity_mismatch_or_missing";
    case Reason::Producer: return "unsupported_contact_producer";
    case Reason::Snapshot: return "candidate_or_snapshot_unavailable";
    case Reason::Geometry: return "geometry_unverified";
    case Reason::Units: return "unit_convention_mismatch";
    case Reason::Time: return "time_context_invalid";
    case Reason::Speed: return "speed_invalid";
    case Reason::Arithmetic: return "arithmetic_invalid";
    }
    return "unknown_reason";
}
}

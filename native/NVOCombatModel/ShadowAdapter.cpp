#include "ShadowAdapter.hpp"
#include <cmath>

namespace nvo::shadow {
namespace {
using namespace nvo::model;

bool KnownRegion(Region r) noexcept { return Cover(r) != 0; }
bool FiniteNonnegative(double value) noexcept { return std::isfinite(value) && value >= 0; }
bool ExactMeasurement(const Measurement& value, Unit unit, bool positive) noexcept {
    return value.verified && value.unit == unit && FiniteNonnegative(value.value)
        && (!positive || value.value > 0);
}
Result Reject(Status status, Reason reason, Region region = Region::Unknown,
    nvo::model::Reason modelReason = nvo::model::Reason::None) noexcept {
    Result result;
    result.status = status;
    result.reason = reason;
    result.resolvedRegion = region;
    result.modelReason = modelReason;
    return result;
}
}

Result Evaluate(const Input& input) {
    const auto& identity = input.identity;
    if (!identity.identitiesVerified || !identity.session || !identity.source || !identity.target
        || !identity.carrier || !identity.weapon || !identity.ammo || !identity.profile)
        return Reject(Status::WaitingForEvidence, Reason::Identity);
    if (!identity.component || !identity.application)
        return Reject(Status::WaitingForEvidence, Reason::Component);
    if (!identity.pathVerified)
        return Reject(Status::WaitingForEvidence, Reason::Path);

    if (!input.mode.verified || (input.mode.value != Mode::RealTime && input.mode.value != Mode::Vats))
        return Reject(Status::WaitingForEvidence, Reason::Mode);

    const auto& region = input.region;
    if (!region.hitDataVerified || !region.collisionVerified
        || !KnownRegion(region.hitData) || !KnownRegion(region.collision))
        return Reject(Status::WaitingForEvidence, Reason::RegionUnavailable);
    if (region.hitData != region.collision)
        return Reject(Status::WaitingForEvidence, Reason::RegionConflict);
    const Region actual = region.hitData;

    if (!input.modifierOwnershipVerified)
        return Reject(Status::WaitingForEvidence, Reason::ModifierOwnership, actual);

    const auto& armour = input.armour;
    if (!armour.enumerationComplete || !armour.regionCoverageComplete
        || armour.order != LayerOrder::OutermostToInnermost || !armour.impactSnapshotVerified)
        return Reject(Status::WaitingForEvidence, Reason::ArmourSnapshot, actual);
    if (armour.layers.empty() && !armour.bareRegionVerified)
        return Reject(Status::WaitingForEvidence, Reason::ArmourSnapshot, actual);
    if (!armour.layers.empty() && armour.bareRegionVerified)
        return Reject(Status::InvalidInput, Reason::ArmourContradiction, actual);

    if (input.family != Family::Kinetic)
        return Reject(Status::Unsupported, Reason::Family, actual);
    const auto& profile = input.kinetic;
    if (!profile.exactMapping || !profile.identity || profile.identity != identity.profile
        || profile.construction < Construction::Ball
        || profile.construction >= Construction::Unknown
        || !ExactMeasurement(profile.mass, Unit::Kilograms, true)
        || !ExactMeasurement(profile.diameter, Unit::Metres, true))
        return Reject(Status::Unsupported, Reason::ThreatProfile, actual);

    const auto& speed = input.speed;
    if (speed.shape == Shape::Missing || speed.shape == Shape::Ambiguous)
        return Reject(Status::WaitingForEvidence, Reason::SpeedUnavailable, actual);
    if (speed.shape == Shape::Interval) {
        if (!ExactMeasurement(speed.low, Unit::MetresPerSecond, false)
            || !ExactMeasurement(speed.high, Unit::MetresPerSecond, false)
            || speed.low.value > speed.high.value)
            return Reject(Status::InvalidInput, Reason::SpeedInterval, actual);
        // Interval evidence is represented honestly but revision 4A does not
        // reinterpret the scalar resolver or choose a midpoint/end point.
        return Reject(Status::WaitingForEvidence, Reason::SpeedInterval, actual);
    }
    if (speed.shape != Shape::Exact
        || !ExactMeasurement(speed.exact, Unit::MetresPerSecond, false))
        return Reject(Status::InvalidInput, Reason::SpeedUnavailable, actual);
    if (!speed.contactVerified || !speed.producerVerified)
        return Reject(Status::WaitingForEvidence, Reason::SpeedProducer, actual);
    if (!speed.unitsCalibrated)
        return Reject(Status::WaitingForEvidence, Reason::SpeedUnits, actual);
    if (!input.target.verified)
        return Reject(Status::Unsupported, Reason::TargetProfile, actual);

    Context context;
    context.session = identity.session;
    context.component = identity.component;
    context.application = identity.application;
    context.source = identity.source;
    context.target = identity.target;
    context.actualRegion = actual;
    context.mode = input.mode.value;
    context.identitiesVerified = true;
    context.pathVerified = true;
    context.modifierOwnershipVerified = true;
    context.armourComplete = true;

    Threat threat;
    threat.family = Family::Kinetic;
    threat.construction = profile.construction;
    threat.mass = profile.mass;
    threat.diameter = profile.diameter;
    threat.impactSpeed = speed.exact;
    threat.profileVerified = true;
    threat.contactVerified = true;
    threat.unitsCalibrated = true;
    threat.woundPayload = profile.woundPayload;

    const Preview preview = Resolve(context, threat, input.target, armour.layers);
    Result result;
    result.resolvedRegion = actual;
    result.preview = preview;
    result.modelReason = preview.reason;
    if (preview.status == nvo::model::Status::PreviewOnly) {
        result.status = Status::PreviewOnly;
        result.reason = Reason::None;
    } else if (preview.status == nvo::model::Status::Unsupported) {
        result.status = Status::WaitingForEvidence;
        result.reason = preview.reason == nvo::model::Reason::Family
            ? Reason::Family : preview.reason == nvo::model::Reason::Profile
            ? Reason::TargetProfile : Reason::ArmourSnapshot;
    } else {
        result.status = Status::InvalidInput;
        result.reason = Reason::Resolver;
    }
    return result;
}

const char* StatusName(Status status) noexcept {
    switch (status) {
    case Status::PreviewOnly: return "preview_only";
    case Status::WaitingForEvidence: return "waiting_for_evidence";
    case Status::Unsupported: return "unsupported";
    case Status::InvalidInput: return "invalid_input";
    }
    return "invalid_status";
}

const char* ReasonName(Reason reason) noexcept {
    switch (reason) {
    case Reason::None: return "none";
    case Reason::Identity: return "identity";
    case Reason::Component: return "component";
    case Reason::Path: return "path";
    case Reason::Mode: return "mode";
    case Reason::RegionUnavailable: return "region_unavailable";
    case Reason::RegionConflict: return "region_conflict";
    case Reason::ModifierOwnership: return "modifier_ownership";
    case Reason::ArmourSnapshot: return "armour_snapshot";
    case Reason::ArmourContradiction: return "armour_contradiction";
    case Reason::Family: return "family";
    case Reason::ThreatProfile: return "threat_profile";
    case Reason::SpeedUnavailable: return "speed_unavailable";
    case Reason::SpeedInterval: return "speed_interval";
    case Reason::SpeedProducer: return "speed_producer";
    case Reason::SpeedUnits: return "speed_units";
    case Reason::TargetProfile: return "target_profile";
    case Reason::Resolver: return "resolver";
    }
    return "invalid_reason";
}
}

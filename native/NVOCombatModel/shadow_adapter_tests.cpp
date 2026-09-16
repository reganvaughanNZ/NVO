#include "ShadowAdapter.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <string_view>

using namespace nvo;
namespace {
unsigned checks{};
void Check(bool pass, const char* name) {
    if (!pass) { std::printf("FAIL %s\n", name); std::exit(1); }
    ++checks;
    std::printf("PASS %s\n", name);
}
bool Near(double a, double b) { return std::abs(a - b) <= 1e-9 * (1 + std::abs(b)); }
model::Measurement M(double value, model::Unit unit) { return {value, unit, true}; }

model::TargetProfile Biological() {
    model::TargetProfile target;
    target.anatomy = model::Anatomy::Biological;
    target.verified = true;
    target.inputUnit = model::Unit::Joules;
    target.directHpPerUnit = 0.1;
    target.bluntHpPerJoule = 0.01;
    target.limbPerHp = 0.5;
    target.tissueCoupling = 1.0;
    return target;
}

model::Layer TorsoLayer(std::uint64_t instance = 100) {
    model::Layer layer;
    layer.instance = instance;
    layer.coverage = model::Cover(model::Region::Torso);
    layer.condition = 1.0;
    layer.profileVerified = true;
    auto& response = layer.response[static_cast<unsigned>(model::Family::Kinetic)];
    response.supported = true;
    response.unit = model::Unit::Joules;
    response.resistanceJ = {{500.0, 700.0, 300.0, 400.0}};
    response.bluntFraction = 0.1;
    response.wearPerAbsorbedUnit = 0.0001;
    return layer;
}

shadow::Input Ready() {
    shadow::Input input;
    input.identity = {1, 2, 3, 4, 0x14, 0x15, 0x16, 0x17, 0x18, true, true};
    input.region = {model::Region::Torso, model::Region::Torso, true, true};
    input.mode = {model::Mode::RealTime, true};
    input.modifierOwnershipVerified = true;
    input.family = model::Family::Kinetic;
    input.kinetic.identity = 4;
    input.kinetic.construction = model::Construction::Ball;
    input.kinetic.mass = M(0.01, model::Unit::Kilograms);
    input.kinetic.diameter = M(0.009, model::Unit::Metres);
    input.kinetic.exactMapping = true;
    input.speed.shape = shadow::Shape::Exact;
    input.speed.exact = M(400.0, model::Unit::MetresPerSecond);
    input.speed.contactVerified = true;
    input.speed.producerVerified = true;
    input.speed.unitsCalibrated = true;
    input.armour.enumerationComplete = true;
    input.armour.regionCoverageComplete = true;
    input.armour.order = shadow::LayerOrder::OutermostToInnermost;
    input.armour.impactSnapshotVerified = true;
    input.armour.bareRegionVerified = true;
    input.target = Biological();
    return input;
}

bool EmptyPreview(const shadow::Result& result) {
    return result.preview.status != model::Status::PreviewOnly
        && result.preview.directHp == 0 && result.preview.limb == 0
        && result.preview.wear.empty();
}
}

int main() {
    static_assert(!shadow::kGameplayWrites);
    static_assert(!shadow::kRuntimeIntegrated);
    static_assert(!shadow::Result::gameplayWrites);
    static_assert(!model::kGameplayWrites);

    const auto ready = Ready();
    const auto bare = shadow::Evaluate(ready);
    Check(bare.status == shadow::Status::PreviewOnly && bare.reason == shadow::Reason::None,
        "complete exact evidence produces preview only");
    Check(bare.resolvedRegion == model::Region::Torso && Near(bare.preview.incident, 800.0)
        && Near(bare.preview.directHp, 80.0), "adapter preserves agreed region and pure resolver output");

    auto armoured = ready;
    armoured.armour.bareRegionVerified = false;
    armoured.armour.layers.push_back(TorsoLayer());
    const auto covered = shadow::Evaluate(armoured);
    Check(covered.status == shadow::Status::PreviewOnly && Near(covered.preview.residual, 300.0),
        "complete instance layer reaches pure preview");
    Check(covered.preview.wear.size() == 1 && covered.preview.wear[0].instance == 100,
        "instance identity remains in preview wear field");

    auto head = armoured;
    head.region.hitData = head.region.collision = model::Region::Head;
    const auto uncoveredHead = shadow::Evaluate(head);
    Check(uncoveredHead.status == shadow::Status::PreviewOnly
        && Near(uncoveredHead.preview.directHp, bare.preview.directHp),
        "body layer does not silently become helmet coverage");

    auto vats = ready;
    vats.mode.value = model::Mode::Vats;
    Check(Near(shadow::Evaluate(vats).preview.directHp, bare.preview.directHp),
        "verified VATS uses the same pure armour rule");

    for (unsigned field = 0; field < 8; ++field) {
        auto input = ready;
        if (field == 0) input.identity.session = 0;
        if (field == 1) input.identity.source = 0;
        if (field == 2) input.identity.target = 0;
        if (field == 3) input.identity.carrier = 0;
        if (field == 4) input.identity.weapon = 0;
        if (field == 5) input.identity.ammo = 0;
        if (field == 6) input.identity.profile = 0;
        if (field == 7) input.identity.identitiesVerified = false;
        const auto result = shadow::Evaluate(input);
        Check(result.status == shadow::Status::WaitingForEvidence
            && result.reason == shadow::Reason::Identity && EmptyPreview(result),
            "missing identity cannot become a preview");
    }
    auto input = ready;
    input.identity.component = 0;
    Check(shadow::Evaluate(input).reason == shadow::Reason::Component,
        "missing component identity is explicit");
    input = ready;
    input.identity.application = 0;
    Check(shadow::Evaluate(input).reason == shadow::Reason::Component,
        "missing application identity is explicit");
    input = ready;
    input.identity.pathVerified = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::Path,
        "unverified engine path cannot preview");

    input = ready;
    input.mode.verified = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::Mode,
        "unknown real-time or VATS mode cannot preview");
    input = ready;
    input.region.collisionVerified = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::RegionUnavailable,
        "one region producer is insufficient");
    input = ready;
    input.region.collision = model::Region::LeftArm;
    const auto conflict = shadow::Evaluate(input);
    Check(conflict.status == shadow::Status::WaitingForEvidence
        && conflict.reason == shadow::Reason::RegionConflict && EmptyPreview(conflict),
        "region disagreement remains disagreement");
    input = ready;
    input.region.hitData = input.region.collision = model::Region::Unknown;
    Check(shadow::Evaluate(input).reason == shadow::Reason::RegionUnavailable,
        "unknown region is not torso");
    input = ready;
    input.modifierOwnershipVerified = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ModifierOwnership,
        "unowned difficulty critical or VATS scaling blocks preview");

    input = ready;
    input.armour.enumerationComplete = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ArmourSnapshot,
        "incomplete equipped-item enumeration is not bare skin");
    input = ready;
    input.armour.regionCoverageComplete = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ArmourSnapshot,
        "unproven region coverage is not bare skin");
    input = ready;
    input.armour.order = shadow::LayerOrder::Unknown;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ArmourSnapshot,
        "unverified layer order blocks preview");
    input = ready;
    input.armour.impactSnapshotVerified = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ArmourSnapshot,
        "armour list not coherently captured at impact blocks preview");
    input = ready;
    input.armour.bareRegionVerified = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ArmourSnapshot,
        "empty layer list requires verified bare region");
    input = armoured;
    input.armour.bareRegionVerified = true;
    const auto contradiction = shadow::Evaluate(input);
    Check(contradiction.status == shadow::Status::InvalidInput
        && contradiction.reason == shadow::Reason::ArmourContradiction,
        "bare and armoured claims cannot coexist");

    input = ready;
    input.family = model::Family::Laser;
    Check(shadow::Evaluate(input).status == shadow::Status::Unsupported
        && shadow::Evaluate(input).reason == shadow::Reason::Family,
        "kinetic adapter does not invent laser slug physics");
    input = ready;
    input.kinetic.exactMapping = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ThreatProfile,
        "unmapped weapon and ammunition stay unsupported");
    input = ready;
    input.kinetic.identity = 5;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ThreatProfile,
        "profile identity must match the hit snapshot");
    input = ready;
    input.kinetic.construction = model::Construction::Unknown;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ThreatProfile,
        "unknown ammunition construction stays unsupported");
    input = ready;
    input.kinetic.mass.unit = model::Unit::Joules;
    Check(shadow::Evaluate(input).reason == shadow::Reason::ThreatProfile,
        "mixed cartridge units are rejected before the resolver");

    input = ready;
    input.speed.shape = shadow::Shape::Missing;
    Check(shadow::Evaluate(input).reason == shadow::Reason::SpeedUnavailable,
        "missing speed remains unavailable");
    input = ready;
    input.speed.shape = shadow::Shape::Ambiguous;
    Check(shadow::Evaluate(input).reason == shadow::Reason::SpeedUnavailable,
        "ambiguous speed remains unavailable");
    input = ready;
    input.speed.shape = shadow::Shape::Interval;
    input.speed.low = M(350.0, model::Unit::MetresPerSecond);
    input.speed.high = M(360.0, model::Unit::MetresPerSecond);
    const auto interval = shadow::Evaluate(input);
    Check(interval.status == shadow::Status::WaitingForEvidence
        && interval.reason == shadow::Reason::SpeedInterval && EmptyPreview(interval),
        "valid speed interval is represented without midpoint promotion");
    input.speed.low.value = 370.0;
    Check(shadow::Evaluate(input).status == shadow::Status::InvalidInput,
        "reversed speed interval is invalid");
    input = ready;
    input.speed.exact.verified = false;
    Check(shadow::Evaluate(input).status == shadow::Status::InvalidInput
        && shadow::Evaluate(input).reason == shadow::Reason::SpeedUnavailable,
        "unverified scalar speed is not exact");
    input = ready;
    input.speed.contactVerified = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::SpeedProducer,
        "unverified contact producer blocks preview");
    input = ready;
    input.speed.producerVerified = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::SpeedProducer,
        "unverified speed producer blocks preview");
    input = ready;
    input.speed.unitsCalibrated = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::SpeedUnits,
        "authored unit convention is not silently called calibrated");

    input = ready;
    input.target.verified = false;
    Check(shadow::Evaluate(input).status == shadow::Status::Unsupported
        && shadow::Evaluate(input).reason == shadow::Reason::TargetProfile,
        "missing target anatomy profile stays unsupported");
    input = armoured;
    input.armour.layers[0].profileVerified = false;
    const auto unknownLayer = shadow::Evaluate(input);
    Check(unknownLayer.status == shadow::Status::WaitingForEvidence
        && unknownLayer.reason == shadow::Reason::ArmourSnapshot
        && unknownLayer.modelReason == model::Reason::Layer,
        "unknown worn armour cannot become bare skin");
    input = armoured;
    input.armour.layers.push_back(input.armour.layers[0]);
    const auto duplicate = shadow::Evaluate(input);
    Check(duplicate.status == shadow::Status::InvalidInput
        && duplicate.modelReason == model::Reason::Layer,
        "duplicate armour instance cannot absorb twice");
    input = armoured;
    input.armour.layers[0].condition = 1.1;
    Check(shadow::Evaluate(input).status == shadow::Status::WaitingForEvidence,
        "invalid live armour condition produces no preview");

    input = ready;
    input.speed.shape = shadow::Shape::Interval;
    input.speed.low = M(354.396070, model::Unit::MetresPerSecond);
    input.speed.high = M(359.517095, model::Unit::MetresPerSecond);
    input.speed.unitsCalibrated = false;
    Check(shadow::Evaluate(input).reason == shadow::Reason::SpeedInterval,
        "current 3U1 owned-step range stays diagnostic only");

    bool deterministic = true;
    for (unsigned i = 0; i < 10000; ++i) {
        const auto result = shadow::Evaluate(armoured);
        deterministic &= result.status == shadow::Status::PreviewOnly
            && Near(result.preview.directHp, covered.preview.directHp);
    }
    Check(deterministic, "10000 shadow previews are deterministic and budget independent");
    Check(std::string_view(shadow::StatusName(shadow::Status::PreviewOnly)) == "preview_only"
        && std::string_view(shadow::ReasonName(shadow::Reason::RegionConflict)) == "region_conflict",
        "diagnostic status names are stable");

    std::printf("RESULT checks=%u failures=0 gameplay_writes=0 runtime_integrated=0 synthetic_profiles=1\n", checks);
    return 0;
}

#include "MaterialPreview.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <initializer_list>
#include <limits>

// All coefficients, identities and region mappings below are synthetic. These
// checks establish the offline contract, not game mappings or measured physics.
namespace {
namespace m = nvo::model;
namespace r = nvo::responses;
namespace s = nvo::shadow;
namespace p = nvo::materials;
namespace b = nvo::binding;
unsigned checks{};
void Check(bool pass, const char* name) {
    ++checks;
    if (!pass) { std::printf("FAIL %s\n", name); std::exit(1); }
}
bool Near(double a, double b) { return std::abs(a - b) <= 1e-9 * (1 + std::abs(b)); }
m::Measurement M(double value, m::Unit unit) { return {value, unit, true}; }
struct Fixture { r::Catalogue catalogue; p::NumericProfiles numeric; p::Input input; };

b::Evidence SyntheticBinding(const p::Input& in) {
    // Fixture generation only: this constructs invented matching scopes for each
    // numerical case. Runtime/producer evidence must be captured independently;
    // copying the consumer's identity is never proof of contact or snapshot scope.
    b::Evidence evidence;
    evidence.expected = {71, in.identity.session, 73, 74, 75, in.identity.component,
        in.identity.application, in.identity.profile, in.identity.source, in.identity.target,
        in.identity.carrier, in.identity.weapon, in.identity.ammo, in.region.hitData, in.mode.value};
    evidence.contact = evidence.snapshot = evidence.expected;
    evidence.contactProducer = b::ContactProducer::VerifiedExactContact;
    evidence.snapshotProducer = b::SnapshotProducer::VerifiedAtImpact;
    evidence.exactCopyScopeVerified = evidence.contactPositionAssociated = true;
    return evidence;
}

Fixture Ready() {
    Fixture f;
    const auto provenance = r::Provenance::SyntheticFixture;
    for (const auto* name : {"plate", "hide", "chassis"}) {
        const std::string profile = std::string("synthetic.") + name;
        f.catalogue.definitions.push_back({profile + ".ballistic", r::Domain::Surface,
            r::Family::Ballistic, r::ConditionLaw::AuthoredCurve, provenance, r::TissueKind::Unresolved});
        r::SurfaceProfile surface;
        surface.id = profile;
        surface.kind = profile == "synthetic.plate" ? r::SurfaceKind::WornItem
            : profile == "synthetic.hide" ? r::SurfaceKind::NaturalProtection : r::SurfaceKind::MechanicalStructure;
        surface.construction = std::string("synthetic.") + name + ".construction";
        surface.responses[0] = profile + ".ballistic";
        f.catalogue.surfaces.push_back(surface);
        p::SurfaceRule rule;
        rule.definition = surface.responses[0]; rule.provenance = provenance;
        rule.condition = r::ConditionLaw::AuthoredCurve;
        rule.curve = {{0, 0}, {0.5, 0.25}, {1, 1}};
        rule.stoppingJ = {{400, 800, 200, 100}};
        rule.transmittedFraction = 0.25; rule.lossPerStoppedJ = 0.001;
        f.numeric.surfaces.push_back(rule);
    }
    f.numeric.surfaces[1].stoppingJ = {{200, 100, 300, 40}};
    f.numeric.surfaces[1].transmittedFraction = 0.5;
    f.numeric.surfaces[2].stoppingJ = {{300, 200, 400, 60}};
    f.numeric.surfaces[2].transmittedFraction = 0.2;
    for (const auto kind : {r::TissueKind::Biological, r::TissueKind::Mechanical}) {
        const std::string id = kind == r::TissueKind::Biological ? "synthetic.bio.ballistic" : "synthetic.mech.ballistic";
        f.catalogue.definitions.push_back({id, r::Domain::Tissue, r::Family::Ballistic,
            r::ConditionLaw::NotApplicable, provenance, kind});
        p::TissueRule tissue;
        tissue.definition = id; tissue.provenance = provenance; tissue.tissue = kind;
        tissue.coupling = kind == r::TissueKind::Biological ? 0.8 : 1;
        tissue.directHpPerJ = kind == r::TissueKind::Biological ? 0.1 : 0.2;
        tissue.transmittedHpPerJ = kind == r::TissueKind::Biological ? 0.02 : 0.03;
        tissue.regionalLossPerHp = 0.3;
        f.numeric.tissues.push_back(tissue);
    }
    r::RegionProfile bio;
    bio.engineRegion = 42; bio.location = "thorax"; bio.tissue = r::TissueKind::Biological;
    bio.naturalSetKnown = true; bio.naturalSurfaces = {"synthetic.hide"};
    bio.responses[0] = "synthetic.bio.ballistic";
    auto mechanical = bio;
    mechanical.engineRegion = 9; mechanical.location = "sensor"; mechanical.tissue = r::TissueKind::Mechanical;
    mechanical.naturalSurfaces = {"synthetic.chassis"}; mechanical.responses[0] = "synthetic.mech.ballistic";
    auto bare = bio;
    bare.engineRegion = 0; bare.location = "bare.region"; bare.naturalSurfaces.clear();
    f.catalogue.targets = {{"synthetic.wearer", r::EquipmentPolicy::WornAllowed, {bio}},
        {"synthetic.robot", r::EquipmentPolicy::NoWornEquipment, {mechanical}},
        {"synthetic.bare", r::EquipmentPolicy::WornAllowed, {bare}}};
    auto& in = f.input;
    in.identity = {1, 2, 3, 4, 0x14, 0x15, 0x16, 0x17, 0x18, true, true};
    in.mode = {m::Mode::RealTime, true}; in.region = {42, 42, true, true};
    in.modifierOwnershipVerified = true; in.targetBindingVerified = true;
    in.targetProfile = "synthetic.wearer"; in.family = r::Family::Ballistic; in.delivery = r::Delivery::Projectile;
    in.kinetic.identity = 4; in.kinetic.construction = m::Construction::Ball;
    in.kinetic.mass = M(0.01, m::Unit::Kilograms); in.kinetic.diameter = M(0.009, m::Unit::Metres);
    in.kinetic.exactMapping = true; in.kinetic.woundPayload = true;
    in.speed.shape = s::Shape::Exact; in.speed.exact = M(400, m::Unit::MetresPerSecond);
    in.speed.contactVerified = in.speed.producerVerified = in.speed.unitsCalibrated = true;
    in.snapshot.wornComplete = in.snapshot.naturalComplete = in.snapshot.coverageComplete = in.snapshot.atImpactVerified = true;
    in.snapshot.order = s::LayerOrder::OutermostToInnermost;
    in.snapshot.surfaces = {{100, "synthetic.plate", r::SurfaceKind::WornItem, p::Contact::Hit, 0.5, true, true},
        {200, "synthetic.hide", r::SurfaceKind::NaturalProtection, p::Contact::Hit, 1, true, true}};
    in.binding = SyntheticBinding(in);
    return f;
}
p::Result Evaluate(const Fixture& f) {
    // Preserve the original numerical cases when their region/mode/component
    // changes. Binding rejection tests below call p::Evaluate directly instead.
    auto input = f.input;
    input.binding = SyntheticBinding(input);
    return p::Evaluate(f.catalogue, f.numeric, input);
}
bool EmptyNumeric(const p::Result& x) {
    return x.energy.layers.empty() && x.surfaces.empty() && x.energy.incidentJ == 0
        && x.energy.residualJ == 0 && x.energy.stoppedJ == 0 && x.energy.transmittedJ == 0
        && x.energy.retainedJ == 0 && x.biologicalHp == 0 && x.mechanicalHp == 0
        && x.biologicalRegionalLoss == 0 && x.mechanicalRegionalLoss == 0
        && !x.protectionPenetrated && !x.biologicalWoundEligible && !x.payloadEligible;
}
bool SameScope(const b::Stamp& a, const b::Stamp& z) {
    return a.generation == z.generation && a.session == z.session && a.transaction == z.transaction
        && a.copyOrdinal == z.copyOrdinal && a.lifetime == z.lifetime && a.component == z.component
        && a.application == z.application && a.profile == z.profile && a.source == z.source
        && a.target == z.target && a.carrier == z.carrier && a.weapon == z.weapon && a.ammo == z.ammo
        && a.region == z.region && a.mode == z.mode;
}
bool EmptyHeld(const p::Result& x) {
    return EmptyNumeric(x) && SameScope(x.impactScope, {}) && x.identity.session == 0
        && x.identity.component == 0 && x.identity.application == 0 && x.identity.profile == 0
        && x.identity.source == 0 && x.identity.target == 0 && x.identity.carrier == 0
        && x.identity.weapon == 0 && x.identity.ammo == 0
        && !x.identity.identitiesVerified && !x.identity.pathVerified && x.engineRegion == -1
        && x.mode == m::Mode::Unknown && x.definitions.surfaces.empty()
        && x.definitions.target.empty() && x.definitions.location.empty()
        && x.definitions.tissueResponse.empty();
}
bool BindingRejected(const p::Result& x, b::Reason reason) {
    return x.status == p::Status::WaitingForEvidence && x.reason == p::Reason::ImpactBinding
        && x.bindingReason == reason && EmptyHeld(x);
}
bool Held(const Fixture& f) { const auto x = Evaluate(f); return x.status != p::Status::PreviewOnly && EmptyNumeric(x); }
bool RejectsAll(std::initializer_list<std::function<void(Fixture&)>> edits) {
    for (const auto& edit : edits) { auto f = Ready(); edit(f); if (!Held(f)) return false; }
    return true;
}
Fixture Bare() {
    auto f = Ready(); f.input.targetProfile = "synthetic.bare"; f.input.region = {0, 0, true, true};
    f.input.snapshot.surfaces.clear(); f.input.snapshot.bareVerified = true; return f;
}
}

int main() {
    static_assert(sizeof(void*) == 4, "Use the x86 standalone runner");
    static_assert(!p::kGameplayWrites && !p::kRuntimeIntegrated && !m::kGameplayWrites);
    static_assert(p::kContractVersion == 2 && !b::kGameplayWrites && !b::kRuntimeIntegrated);
    const auto ready = Ready();
    const auto base = Evaluate(ready);
    Check(r::Validate(ready.catalogue).valid, "synthetic authored catalogue is independently valid");
    Check(base.status == p::Status::PreviewOnly && base.reason == p::Reason::None, "complete ballistic preview");
    Check(Near(base.energy.incidentJ, 800) && Near(base.energy.residualJ, 500)
        && Near(base.energy.stoppedJ, 300) && Near(base.energy.transmittedJ, 125)
        && Near(base.energy.retainedJ, 175), "manually calculated energy budget");
    Check(base.energy.layers.size() == 2 && base.energy.layers[0].key == 100
        && Near(base.energy.layers[0].incomingJ, 800) && Near(base.energy.layers[0].stoppedJ, 100)
        && Near(base.energy.layers[0].outgoingJ, 700) && Near(base.energy.layers[0].transmittedJ, 25)
        && base.energy.layers[1].key == 200 && Near(base.energy.layers[1].incomingJ, 700)
        && Near(base.energy.layers[1].stoppedJ, 200) && Near(base.energy.layers[1].outgoingJ, 500),
        "ordered layer budgets retain instance keys");
    Check(Near(base.biologicalHp, 42.5) && Near(base.biologicalRegionalLoss, 12.75)
        && base.mechanicalHp == 0 && base.mechanicalRegionalLoss == 0
        && base.protectionPenetrated && base.biologicalWoundEligible && base.payloadEligible,
        "biological output and payload use residual and transmitted channels");
    Check(base.surfaces.size() == 2 && Near(base.surfaces[0].wornConditionLoss, 0.1)
        && base.surfaces[0].naturalStructureLoss == 0 && base.surfaces[0].mechanicalStructureLoss == 0
        && Near(base.surfaces[1].naturalStructureLoss, 0.2) && base.surfaces[1].wornConditionLoss == 0
        && base.surfaces[1].mechanicalStructureLoss == 0, "worn and natural loss have distinct owners");
    Check(base.engineRegion == 42 && base.identity.application == 3 && base.identity.component == 2
        && base.surfaces[1].target == 0x15 && base.surfaces[1].engineRegion == 42
        && base.surfaces[1].profile == "synthetic.hide"
        && base.surfaces[1].definition == "synthetic.hide.ballistic"
        && base.surfaces[1].provenance == r::Provenance::SyntheticFixture,
        "nonhumanoid region identity and provenance survive unchanged");
    auto f = ready;
    auto anotherPlate = f.input.snapshot.surfaces[0]; anotherPlate.key = 101;
    f.input.snapshot.surfaces.insert(f.input.snapshot.surfaces.begin() + 1, anotherPlate);
    auto x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && x.energy.layers.size() == 3 && x.definitions.surfaces.size() == 2
        && Near(x.energy.residualJ, 400) && Near(x.biologicalHp, 35),
        "shared worn definition preserves two actual item instances");
    f = ready; f.input.snapshot.surfaces.erase(f.input.snapshot.surfaces.begin()); x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && Near(x.energy.residualJ, 600) && Near(x.biologicalHp, 50),
        "natural protection is neither missing armour nor bare skin");
    f = ready; f.input.targetProfile = "synthetic.robot"; f.input.region = {9, 9, true, true};
    f.input.snapshot.surfaces = {{300, "synthetic.chassis", r::SurfaceKind::MechanicalStructure, p::Contact::Hit, 1, true, true}};
    x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && Near(x.mechanicalHp, 101.8) && Near(x.mechanicalRegionalLoss, 30.54)
        && x.biologicalHp == 0 && x.biologicalRegionalLoss == 0 && !x.biologicalWoundEligible && !x.payloadEligible
        && x.surfaces.size() == 1 && Near(x.surfaces[0].mechanicalStructureLoss, 0.3)
        && x.surfaces[0].wornConditionLoss == 0 && x.surfaces[0].naturalStructureLoss == 0,
        "mechanical tissue and chassis never become biological damage or worn loss");
    const auto bare = Evaluate(Bare());
    Check(bare.status == p::Status::PreviewOnly && Near(bare.biologicalHp, 64) && !bare.protectionPenetrated
        && bare.biologicalWoundEligible && bare.surfaces.empty(), "verified bare region permits tissue energy without armour penetration");
    f = ready; f.input.kinetic.diameter.value *= 2; x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && Near(x.biologicalHp, base.biologicalHp), "diameter remains metadata not invented geometry physics");
    f = ready; f.input.speed.exact.value = 0; x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && x.energy.incidentJ == 0 && x.biologicalHp == 0
        && !x.protectionPenetrated && !x.biologicalWoundEligible && !x.payloadEligible,
        "known zero contact speed is valid and produces no wound");
    f = ready; f.input.mode.value = m::Mode::Vats; x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && x.mode == m::Mode::Vats && Near(x.biologicalHp, base.biologicalHp),
        "verified VATS and real time share numerical rules");
    f = ready; f.input.speed.exact.value = 200; // 200 J: ordering changes the transmitted subset.
    const auto forward = Evaluate(f); std::reverse(f.input.snapshot.surfaces.begin(), f.input.snapshot.surfaces.end());
    const auto backward = Evaluate(f);
    Check(forward.status == p::Status::PreviewOnly && backward.status == p::Status::PreviewOnly
        && Near(forward.energy.transmittedJ, 75) && Near(backward.energy.transmittedJ, 100)
        && Near(forward.biologicalHp, 1.5) && Near(backward.biologicalHp, 2)
        && !forward.protectionPenetrated && !forward.biologicalWoundEligible && !forward.payloadEligible,
        "verified layer order matters and stopped projectiles cannot deliver penetrating payloads");
    f = ready; f.input.snapshot.surfaces[0].contact = p::Contact::Miss;
    f.input.snapshot.surfaces[0].condition = m::unknown; f.input.snapshot.surfaces[0].conditionVerified = false;
    f.numeric.surfaces.erase(f.numeric.surfaces.begin()); x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && x.energy.layers.size() == 1 && x.surfaces.size() == 1
        && x.surfaces[0].key == 200 && Near(x.energy.residualJ, 600),
        "verified missed surface needs no unused condition or numbers and consumes neither");
    f = ready; for (auto& surface : f.input.snapshot.surfaces) surface.contact = p::Contact::Miss;
    f.input.snapshot.bareVerified = true; x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && Near(x.biologicalHp, 64) && x.surfaces.empty()
        && !x.protectionPenetrated, "all misses require explicit bare contact and produce no surface loss");
    f = ready; f.catalogue.definitions[0].condition = r::ConditionLaw::ExplicitlyIndependent;
    f.numeric.surfaces[0].condition = r::ConditionLaw::ExplicitlyIndependent; f.numeric.surfaces[0].curve.clear();
    f.input.snapshot.surfaces[0].condition = 0; x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && Near(x.energy.layers[0].stoppedJ, 400)
        && x.surfaces[0].wornConditionLoss == 0 && Near(x.energy.residualJ, 200),
        "explicit condition independence retains actual zero condition for loss cap");
    f = ready; f.input.snapshot.surfaces[0].condition = 0.75; x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && Near(x.energy.layers[0].stoppedJ, 250),
        "piecewise curve interpolates authored knots");
    f = ready; f.input.snapshot.surfaces[0].condition = 0;
    f.numeric.surfaces[1].stoppingJ = {{0, 0, 0, 0}}; x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && Near(x.energy.residualJ, 800) && Near(x.biologicalHp, 64)
        && x.energy.stoppedJ == 0 && x.surfaces[0].wornConditionLoss == 0 && x.surfaces[1].naturalStructureLoss == 0,
        "authored zero condition scale and explicit zero resistance are known zero rather than missing");
    bool constructions = true;
    const double expectedResidual[] = {500, 500, 450, 735};
    for (unsigned i = 0; i < 4; ++i) {
        f = ready; f.input.kinetic.construction = static_cast<m::Construction>(i); x = Evaluate(f);
        constructions = constructions && x.status == p::Status::PreviewOnly && Near(x.energy.residualJ, expectedResidual[i]);
    }
    Check(constructions, "all four projectile constructions select their explicit stopping columns");
    f = Bare(); f.input.delivery = r::Delivery::Pellet; f.input.kinetic.construction = m::Construction::Pellet;
    f.input.kinetic.mass.value = 0.002; const auto pellet = Evaluate(f);
    f.input.identity.component = 20; f.input.identity.application = 30; const auto secondPellet = Evaluate(f);
    Check(pellet.status == p::Status::PreviewOnly && Near(pellet.energy.incidentJ, 160)
        && Near(pellet.energy.incidentJ * 5, bare.energy.incidentJ) && Near(pellet.biologicalHp, 12.8)
        && secondPellet.identity.component == 20 && Near(secondPellet.energy.incidentJ, 160),
        "independent pellet mass carries its own share rather than shell-total energy");
    f = ready; f.input.delivery = r::Delivery::Fragment;
    Check(Evaluate(f).status == p::Status::PreviewOnly, "explicit fragment component shares ballistic contract");

    // The linear specialization must retain the established 4A result.
    f = ready; f.catalogue.targets[0].regions[0].naturalSurfaces.clear(); f.input.snapshot.surfaces.resize(1);
    f.numeric.surfaces[0].curve = {{0, 0}, {1, 1}};
    s::Input legacy;
    legacy.identity = f.input.identity; legacy.region = {m::Region::Torso, m::Region::Torso, true, true};
    legacy.mode = f.input.mode; legacy.modifierOwnershipVerified = true; legacy.family = m::Family::Kinetic;
    legacy.kinetic = f.input.kinetic; legacy.speed = f.input.speed;
    legacy.armour.enumerationComplete = legacy.armour.regionCoverageComplete = legacy.armour.impactSnapshotVerified = true;
    legacy.armour.order = s::LayerOrder::OutermostToInnermost;
    m::Layer oldLayer;
    oldLayer.instance = 100; oldLayer.coverage = m::Cover(m::Region::Torso); oldLayer.condition = 0.5; oldLayer.profileVerified = true;
    auto& oldRule = oldLayer.response[0]; oldRule.supported = true; oldRule.unit = m::Unit::Joules;
    oldRule.resistanceJ = f.numeric.surfaces[0].stoppingJ; oldRule.bluntFraction = 0.25; oldRule.wearPerAbsorbedUnit = 0.001;
    legacy.armour.layers = {oldLayer}; legacy.target = {m::Anatomy::Biological, true, m::Unit::Joules, 0.1, 0.02, 0.3, 0.8};
    const auto old = s::Evaluate(legacy); x = Evaluate(f);
    Check(old.status == s::Status::PreviewOnly && x.status == p::Status::PreviewOnly
        && Near(x.energy.residualJ, old.preview.residual) && Near(x.energy.transmittedJ, old.preview.bluntJoules)
        && Near(x.biologicalHp, old.preview.directHp) && Near(x.biologicalRegionalLoss, old.preview.limb)
        && x.surfaces.size() == 1 && old.preview.wear.size() == 1
        && Near(x.surfaces[0].wornConditionLoss, old.preview.wear[0].loss), "linear specialization agrees with existing shadow preview");
    f = ready; const auto first = Evaluate(f); const auto repeated = Evaluate(f);
    Check(Near(first.biologicalHp, repeated.biologicalHp) && f.input.snapshot.surfaces[0].condition == 0.5
        && f.input.identity.application == 3 && f.numeric.surfaces[0].curve[1].scale == 0.25
        && f.catalogue.targets[0].regions[0].naturalSurfaces[0] == "synthetic.hide",
        "preview repeat is deterministic and does not mutate input condition or authoring");

    Check(RejectsAll({[](Fixture& v) { v.input.identity.session = 0; }, [](Fixture& v) { v.input.identity.source = 0; },
        [](Fixture& v) { v.input.identity.target = 0; }, [](Fixture& v) { v.input.identity.carrier = 0; },
        [](Fixture& v) { v.input.identity.weapon = 0; }, [](Fixture& v) { v.input.identity.ammo = 0; },
        [](Fixture& v) { v.input.identity.profile = 0; }}), "every attribution identity is required");
    Check(RejectsAll({[](Fixture& v) { v.input.identity.identitiesVerified = false; }}), "unverified identities hold");
    Check(RejectsAll({[](Fixture& v) { v.input.identity.pathVerified = false; }}), "unverified path holds");
    Check(RejectsAll({[](Fixture& v) { v.input.identity.component = 0; }, [](Fixture& v) { v.input.identity.application = 0; }}),
        "component and application identities are required");
    Check(RejectsAll({[](Fixture& v) { v.input.mode.verified = false; }, [](Fixture& v) { v.input.mode.value = m::Mode::Unknown; }}),
        "mode requires explicit supported evidence");
    Check(RejectsAll({[](Fixture& v) { v.input.kinetic.identity = 99; }, [](Fixture& v) { v.input.kinetic.exactMapping = false; },
        [](Fixture& v) { v.input.kinetic.construction = m::Construction::Unknown; }}), "threat identity construction and mapping cannot default");
    Check(RejectsAll({[](Fixture& v) { v.input.kinetic.mass.value = 0; }, [](Fixture& v) { v.input.kinetic.mass.unit = m::Unit::Joules; },
        [](Fixture& v) { v.input.kinetic.diameter.verified = false; }, [](Fixture& v) { v.input.kinetic.diameter.value = -1; }}),
        "mass and diameter require positive verified matching units");
    Check(RejectsAll({[](Fixture& v) { v.input.speed.shape = s::Shape::Missing; }}), "missing speed holds");
    Check(RejectsAll({[](Fixture& v) { v.input.speed.shape = s::Shape::Ambiguous; }}), "ambiguous speed holds");
    Check(RejectsAll({[](Fixture& v) { v.input.speed.shape = s::Shape::Interval; v.input.speed.low = M(390, m::Unit::MetresPerSecond);
        v.input.speed.high = M(410, m::Unit::MetresPerSecond); }}), "valid speed interval never becomes midpoint energy");
    Check(RejectsAll({[](Fixture& v) { v.input.speed.exact.verified = false; }, [](Fixture& v) { v.input.speed.exact.unit = m::Unit::Joules; },
        [](Fixture& v) { v.input.speed.exact.value = -1; }}), "exact speed measurement requires known units and nonnegative value");
    Check(RejectsAll({[](Fixture& v) { v.input.speed.contactVerified = false; }, [](Fixture& v) { v.input.speed.producerVerified = false; }}),
        "contact and producer authority are required");
    Check(RejectsAll({[](Fixture& v) { v.input.speed.unitsCalibrated = false; }}), "uncalibrated speed holds");
    Check(RejectsAll({[](Fixture& v) { v.input.region.hitDataVerified = false; }, [](Fixture& v) { v.input.region.collisionVerified = false; }}),
        "both actual region producers must be verified");
    Check(RejectsAll({[](Fixture& v) { v.input.region.hitData = v.input.region.collision = -1; },
        [](Fixture& v) { v.input.region.hitData = v.input.region.collision = 256; }}), "engine region bounds cannot be coerced into humanoid enum");
    Check(RejectsAll({[](Fixture& v) { v.input.region.collision = 0; }}), "region disagreement holds rather than selecting aim region");
    Check(RejectsAll({[](Fixture& v) { v.input.region.hitData = v.input.region.collision = 41; },
        [](Fixture& v) { v.input.targetProfile = "unknown.target"; }}), "unmapped target or region holds");
    Check(RejectsAll({[](Fixture& v) { v.input.targetBindingVerified = false; }}), "target profile needs verified actual target binding");
    Check(RejectsAll({[](Fixture& v) { v.input.modifierOwnershipVerified = false; }}), "modifier ownership remains a gate");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.wornComplete = false; }}), "incomplete worn set holds");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.naturalComplete = false; }}), "incomplete natural set holds");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.coverageComplete = false; }}), "incomplete contact coverage holds");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.atImpactVerified = false; }}), "stable state without at-impact evidence holds");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.order = s::LayerOrder::Unknown; }}), "inventory traversal does not supply layer order");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.surfaces[1].key = 100; },
        [](Fixture& v) { v.input.snapshot.surfaces[0].key = 0; }}), "surface keys are nonzero and globally unique");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.surfaces[0].bindingVerified = false; }}), "surface instance binding must be verified");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.surfaces[0].conditionVerified = false; }}), "condition measurement must be verified");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.surfaces[0].condition = -0.1; },
        [](Fixture& v) { v.input.snapshot.surfaces[0].condition = 1.1; },
        [](Fixture& v) { v.input.snapshot.surfaces[0].condition = m::unknown; }}), "condition cannot be clamped or inferred from invalid data");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.surfaces[0].contact = p::Contact::Unknown; }}), "unknown actual surface contact holds");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.surfaces[0].kind = r::SurfaceKind::NaturalProtection; }}),
        "surface kind cannot redirect item loss to natural owner");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.surfaces[0].profile = "unknown.surface"; }}), "unknown equipped profile holds");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.surfaces.pop_back(); }}), "missing mapped natural surface holds");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.surfaces.push_back({300, "synthetic.chassis", r::SurfaceKind::MechanicalStructure,
        p::Contact::Hit, 1, true, true}); }}), "unmapped additional natural surface holds");
    Check(RejectsAll({[](Fixture& v) { auto copy = v.input.snapshot.surfaces[1]; copy.key = 201; v.input.snapshot.surfaces.push_back(copy); }}),
        "duplicate mapped natural surface cannot become an extra layer");
    Check(RejectsAll({[](Fixture& v) { v.catalogue.targets[0].equipment = r::EquipmentPolicy::NoWornEquipment; }}),
        "no-worn target policy rejects contradictory actual equipment");
    Check(RejectsAll({[](Fixture& v) { for (auto& surface : v.input.snapshot.surfaces) surface.contact = p::Contact::Miss; }}),
        "no contacted surface without bare evidence holds");
    Check(RejectsAll({[](Fixture& v) { v.input.snapshot.bareVerified = true; }}), "bare evidence contradicting contacted protection rejects");
    Check(RejectsAll({[](Fixture& v) { v.numeric.surfaces.erase(v.numeric.surfaces.begin()); }}), "missing surface numbers remain unresolved");
    Check(RejectsAll({[](Fixture& v) { v.numeric.tissues.erase(v.numeric.tissues.begin()); }}), "missing tissue numbers remain unresolved");
    Check(RejectsAll({[](Fixture& v) { v.numeric.surfaces.push_back(v.numeric.surfaces[0]); }}), "duplicate numerical surface identity rejects");
    Check(RejectsAll({[](Fixture& v) { v.numeric.tissues.push_back(v.numeric.tissues[0]); }}), "duplicate numerical tissue identity rejects");
    Check(RejectsAll({[](Fixture& v) { v.numeric.surfaces[0].provenance = r::Provenance::ReviewedGameplay; },
        [](Fixture& v) { v.numeric.tissues[0].provenance = r::Provenance::ReviewedGameplay; }}), "numbers cannot promote symbolic provenance");
    Check(RejectsAll({[](Fixture& v) { v.numeric.surfaces[0].condition = r::ConditionLaw::ExplicitlyIndependent; v.numeric.surfaces[0].curve.clear(); }}),
        "numerical and symbolic condition policies must agree");
    Check(RejectsAll({[](Fixture& v) { v.numeric.tissues[0].tissue = r::TissueKind::Mechanical; }}), "numerical tissue kind must match selected definition");
    Check(RejectsAll({[](Fixture& v) { v.numeric.surfaces[0].definition = "synthetic.bio.ballistic"; },
        [](Fixture& v) { v.numeric.tissues[0].definition = "synthetic.plate.ballistic"; }}), "surface and tissue numerical domains cannot cross");
    Check(RejectsAll({[](Fixture& v) { v.catalogue.definitions[0].family = r::Family::Laser; }}), "definition family mismatch rejects whole preview");
    Check(RejectsAll({[](Fixture& v) { v.numeric.surfaces[0].stoppingJ[0] = m::unknown; },
        [](Fixture& v) { v.numeric.tissues[0].coupling = m::unknown; },
        [](Fixture& v) { v.input.speed.exact.value = std::numeric_limits<double>::infinity(); }}), "nonfinite evidence or coefficients return no partial numbers");
    Check(RejectsAll({[](Fixture& v) { v.numeric.surfaces[0].curve = {{0, 0}}; },
        [](Fixture& v) { v.numeric.surfaces[0].curve = {{0.1, 0}, {1, 1}}; },
        [](Fixture& v) { v.numeric.surfaces[0].curve = {{0, 0}, {0.9, 1}}; },
        [](Fixture& v) { v.numeric.surfaces[0].curve = {{0, 0}, {0.5, 0.7}, {0.5, 0.8}, {1, 1}}; },
        [](Fixture& v) { v.numeric.surfaces[0].curve = {{0, 0.5}, {0.5, 0.4}, {1, 1}}; },
        [](Fixture& v) { v.numeric.surfaces[0].curve = {{0, 0}, {1, 0.9}}; },
        [](Fixture& v) { v.numeric.surfaces[0].curve = {{0, -0.1}, {1, 1}}; },
        [](Fixture& v) { v.numeric.surfaces[0].curve = {{0, 0}, {0.5, 1.1}, {1, 1}}; },
        [](Fixture& v) { v.numeric.surfaces[0].curve = {{0, 0}, {0.5, m::unknown}, {1, 1}}; },
        [](Fixture& v) { v.numeric.surfaces[0].curve.resize(9); }}), "authored curve must satisfy span ordering scale and count contract");
    Check(RejectsAll({[](Fixture& v) { v.catalogue.definitions[0].condition = r::ConditionLaw::ExplicitlyIndependent;
        v.numeric.surfaces[0].condition = r::ConditionLaw::ExplicitlyIndependent; }}), "independent law rejects hidden curve");
    Check(RejectsAll({[](Fixture& v) { v.numeric.surfaces[0].stoppingJ[0] = -1; },
        [](Fixture& v) { v.numeric.surfaces[0].transmittedFraction = 1.1; },
        [](Fixture& v) { v.numeric.surfaces[0].lossPerStoppedJ = -1; },
        [](Fixture& v) { v.numeric.tissues[0].coupling = 1.1; },
        [](Fixture& v) { v.numeric.tissues[0].directHpPerJ = -1; },
        [](Fixture& v) { v.numeric.tissues[0].transmittedHpPerJ = -1; },
        [](Fixture& v) { v.numeric.tissues[0].regionalLossPerHp = -1; }}), "numerical coefficients obey energy fraction and nonnegative rules");
    bool unsupported = true;
    for (unsigned i = 1; i < r::kFamilyCount; ++i) {
        f = ready; f.input.family = static_cast<r::Family>(i); x = Evaluate(f);
        unsupported = unsupported && x.status == p::Status::Unsupported && x.reason == p::Reason::Family && EmptyNumeric(x);
    }
    Check(unsupported, "all ten other families remain explicit unsupported numerical paths");
    Check(RejectsAll({[](Fixture& v) { v.input.delivery = r::Delivery::Melee; },
        [](Fixture& v) { v.input.delivery = r::Delivery::Unknown; }}), "delivery cannot bypass family contract");
    Check(RejectsAll({[](Fixture& v) { v.input.kinetic.mass.value = std::numeric_limits<double>::max(); },
        [](Fixture& v) { v.numeric.tissues[0].directHpPerJ = std::numeric_limits<double>::max(); }}),
        "energy or output overflow discards whole numerical result");
    const auto invalidKernel = m::ResolveKineticLayers(800, {{1, 100, 1, 0.5, 0.001}, {2, m::unknown, 1, 0.5, 0.001}});
    Check(invalidKernel.status != m::Status::PreviewOnly && invalidKernel.layers.empty() && invalidKernel.incidentJ == 0,
        "shared kernel rejects invalid later layer without leaking earlier result");
    f = ready; f.input.region = {255, 255, true, true}; f.catalogue.targets[0].regions[0].engineRegion = 255; x = Evaluate(f);
    Check(x.status == p::Status::PreviewOnly && x.engineRegion == 255 && Near(x.biologicalHp, 42.5),
        "maximum authored engine region remains literal and supported");

    // End-to-end binding checks deliberately bypass the numerical fixture helper
    // and call the production entry point with independently corrupted evidence.
    // These synthetic inputs cannot certify either reserved producer at runtime.
    f = ready; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(x.status == p::Status::PreviewOnly && SameScope(x.impactScope, f.input.binding.expected)
        && x.surfaces.size() == 2 && x.surfaces[0].key == 100 && x.surfaces[1].key == 200
        && Near(x.biologicalHp, 42.5), "successful offline result preserves the complete instance capture scope");
    f = ready; f.input.binding = {}; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ExpectedScopeMissing),
        "legacy verification booleans without binding evidence return no result");
    f = ready; f.input.binding.expected = {}; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ExpectedScopeMissing), "missing consumer scope empties material result");
    f = ready; f.input.binding.contact = {}; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ContactScopeMissing), "missing contact scope empties material result");
    f = ready; f.input.binding.snapshot = {}; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::SnapshotScopeMissing), "missing snapshot scope empties material result");
    f = ready; ++f.input.binding.contact.generation; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ContactScopeMismatch), "stale contact generation empties material result");
    f = ready; ++f.input.binding.snapshot.generation; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::SnapshotScopeMismatch), "stale snapshot generation empties material result");
    f = ready; ++f.input.identity.application; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ExpectedIdentityMismatch), "current application cannot reuse a prior binding");
    f = ready; ++f.input.binding.contact.copyOrdinal; ++f.input.binding.snapshot.copyOrdinal;
    x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ContactScopeMismatch),
        "same target and agreeing producer stamps from a different copy remain held");
    f = ready; ++f.input.binding.contact.application; ++f.input.binding.snapshot.application;
    x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ContactScopeMismatch),
        "same target and agreeing producer stamps from a different application remain held");
    f = ready; ++f.input.binding.expected.transaction; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ContactScopeMismatch), "new transaction cannot consume old producer stamps");
    f = ready; f.input.binding.exactCopyScopeVerified = false; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::CopyScopeUnverified), "matching keys without copy proof remain held");
    f = ready; f.input.binding.contactPositionAssociated = false; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ContactPositionUnverified), "matching keys without contact association remain held");
    for (const auto producer : {b::ContactProducer::Unknown, b::ContactProducer::OwnedStepInterval,
         b::ContactProducer::EngineSegmentMean, b::ContactProducer::PointModelEstimate,
         b::ContactProducer::MuzzleEstimate, static_cast<b::ContactProducer>(255)}) {
        f = ready; f.input.binding.contactProducer = producer;
        x = p::Evaluate(f.catalogue, f.numeric, f.input);
        const auto name = "exact speed and legacy flags cannot promote contact producer "
            + std::to_string(static_cast<unsigned>(producer));
        Check(f.input.speed.shape == s::Shape::Exact && f.input.speed.contactVerified
            && f.input.speed.producerVerified && f.input.speed.unitsCalibrated
            && BindingRejected(x, b::Reason::ContactProducerUnqualified), name.c_str());
    }
    for (const auto producer : {b::SnapshotProducer::Unknown, b::SnapshotProducer::StableCopyInput,
         static_cast<b::SnapshotProducer>(255)}) {
        f = ready; f.input.binding.snapshotProducer = producer;
        x = p::Evaluate(f.catalogue, f.numeric, f.input);
        const auto name = "legacy at-impact flag cannot promote snapshot producer "
            + std::to_string(static_cast<unsigned>(producer));
        Check(f.input.snapshot.atImpactVerified && BindingRejected(x, b::Reason::SnapshotProducerUnqualified), name.c_str());
    }
    for (const double upper : {401.0, 400.0}) {
        f = ready; f.input.speed.shape = s::Shape::Interval;
        f.input.speed.low = M(400, m::Unit::MetresPerSecond);
        f.input.speed.high = M(upper, m::Unit::MetresPerSecond);
        x = p::Evaluate(f.catalogue, f.numeric, f.input);
        Check(x.status == p::Status::WaitingForEvidence && x.reason == p::Reason::Evidence
            && x.evidenceReason == s::Reason::SpeedInterval && EmptyHeld(x),
            upper == 400 ? "matching scopes do not promote zero-width interval to exact speed"
                : "matching scopes do not promote interval to exact speed");
        ++f.input.binding.snapshot.copyOrdinal;
        x = p::Evaluate(f.catalogue, f.numeric, f.input);
        Check(BindingRejected(x, b::Reason::SnapshotScopeMismatch),
            upper == 400 ? "zero-width interval cannot bypass mismatched snapshot binding"
                : "interval cannot bypass mismatched snapshot binding");
    }
    f = ready; ++f.input.binding.contact.region; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::ContactScopeMismatch), "actual-region agreement cannot repair a mismatched contact stamp");
    f = ready; ++f.input.binding.snapshot.lifetime; x = p::Evaluate(f.catalogue, f.numeric, f.input);
    Check(BindingRejected(x, b::Reason::SnapshotScopeMismatch), "stable surface data from another lifetime cannot be consumed");
    std::printf("SAMPLE synthetic baseline: incident=%.3f J residual=%.3f J stopped=%.3f J transmitted=%.3f J retained=%.3f J biological_hp=%.3f regional_loss=%.3f worn_loss=%.3f natural_loss=%.3f\n",
        base.energy.incidentJ, base.energy.residualJ, base.energy.stoppedJ, base.energy.transmittedJ,
        base.energy.retainedJ, base.biologicalHp, base.biologicalRegionalLoss,
        base.surfaces[0].wornConditionLoss, base.surfaces[1].naturalStructureLoss);
    std::printf("PASS material preview checks: %u\n", checks);
    return 0;
}

#include "ResponseDefinitions.hpp"
#include <cstdlib>
#include <iostream>
#include <utility>
using namespace nvo::responses;
namespace {
int checks = 0;
void Expect(bool result, const char* name) {
    ++checks;
    if (!result) { std::cerr << "FAIL " << name << '\n'; std::exit(1); }
}
constexpr unsigned Index(Family f) { return static_cast<unsigned>(f); }
Catalogue Fixture() {
    Catalogue c;
    SurfaceProfile worn, hide, chassis;
    worn.id = "synthetic.plate"; worn.kind = SurfaceKind::WornItem; worn.construction = "plate_and_backing";
    hide.id = "synthetic.hide"; hide.kind = SurfaceKind::NaturalProtection; hide.construction = "hide";
    chassis.id = "synthetic.chassis"; chassis.kind = SurfaceKind::MechanicalStructure; chassis.construction = "chassis";
    RegionProfile bio, mech;
    bio.engineRegion = 42; bio.location = "thorax"; bio.tissue = TissueKind::Biological; bio.naturalSetKnown = true;
    mech.engineRegion = 9; mech.location = "sensor"; mech.tissue = TissueKind::Mechanical; mech.naturalSetKnown = true;
    bio.naturalSurfaces = {hide.id}; mech.naturalSurfaces = {chassis.id};
    for (unsigned i = 0; i < kFamilyCount; ++i) {
        const auto family = static_cast<Family>(i);
        const std::string name = Describe(family)->name;
        for (auto* s : {&worn, &hide, &chassis}) {
            const auto id = s->id + "." + name;
            c.definitions.push_back({id, Domain::Surface, family, ConditionLaw::AuthoredCurve,
                                     Provenance::SyntheticFixture, TissueKind::Unresolved});
            s->responses[i] = id;
        }
        bio.responses[i] = "synthetic.bio." + name;
        mech.responses[i] = "synthetic.mech." + name;
        c.definitions.push_back({bio.responses[i], Domain::Tissue, family, ConditionLaw::NotApplicable,
                                 Provenance::SyntheticFixture, TissueKind::Biological});
        c.definitions.push_back({mech.responses[i], Domain::Tissue, family, ConditionLaw::NotApplicable,
                                 Provenance::SyntheticFixture, TissueKind::Mechanical});
    }
    c.surfaces = {worn, hide, chassis};
    c.targets = {{"synthetic.animal", EquipmentPolicy::NoWornEquipment, {bio}},
                 {"synthetic.robot", EquipmentPolicy::NoWornEquipment, {mech}},
                 {"synthetic.wearer", EquipmentPolicy::WornAllowed, {bio}}};
    return c;
}
Query Base() { return {Family::Ballistic, Delivery::Projectile, "synthetic.animal", 42, true, {}}; }
bool Empty(const Plan& p) {
    return p.target.empty() && p.location.empty() && p.tissue == TissueKind::Unresolved
        && p.tissueResponse.empty() && p.tissueProvenance == Provenance::Unresolved && p.surfaces.empty();
}
void Held(const Catalogue& c, const Query& q, Status status, Reason reason, const char* name) {
    const auto p = Select(c, q);
    Expect(p.status == status && p.reason == reason && Empty(p), name);
}
} // namespace
int main() {
    static_assert(!kRuntimeIntegrated && !kGameplayWrites);
    static_assert(sizeof(void*) == 4, "Use the x86 standalone runner");
    const auto base = Fixture();
    Expect(Validate(base).valid, "all-family synthetic catalogue");
    Expect(Validate({}).valid, "empty authoring catalogue is not runtime support");
    // Independent contract fixture: columns are projectile/pellet/fragment/melee/
    // thrown/explosion/pulse/continuous. Changes require review of RESPONSE-DESIGN.
    constexpr bool accepted[kFamilyCount][8] = {
        {true, true, true, false, false, false, false, false}, // ballistic
        {true, false, false, true, true, false, false, false}, // piercing
        {true, false, false, true, true, false, false, false}, // cutting
        {true, false, false, true, true, false, false, false}, // blunt
        {false, false, false, false, false, true, false, false}, // blast
        {true, false, false, false, false, false, true, true}, // laser
        {true, false, false, false, false, false, true, true}, // plasma
        {false, false, false, false, false, false, false, true}, // flame
        {false, false, false, false, false, true, true, true}, // external heat
        {true, false, false, true, false, false, true, true}, // electrical
        {true, false, false, false, false, true, true, true} // emp
    };
    static_assert(static_cast<unsigned>(Delivery::Count) == 8);
    for (unsigned i = 0; i < kFamilyCount; ++i) {
        const auto family = static_cast<Family>(i);
        Expect(Describe(family) != nullptr, "family described");
        for (unsigned j = 0; j < static_cast<unsigned>(Delivery::Count); ++j) {
            auto q = Base(); q.family = family; q.delivery = static_cast<Delivery>(j);
            const auto p = Select(base, q);
            if (accepted[i][j]) {
                Expect(p.status == Status::DefinitionsOnly && p.tissue == TissueKind::Biological
                    && p.surfaces.size() == 1 && p.surfaces[0].kind == SurfaceKind::NaturalProtection,
                    "allowed delivery selects definitions, not bare or damage");
                Expect(Timing(family, q.delivery) != TimeBasis::Unresolved, "allowed timing");
            } else {
                Expect(p.status == Status::Unsupported && p.reason == Reason::Delivery && Empty(p), "unsupported delivery");
                Expect(Timing(family, q.delivery) == TimeBasis::Unresolved, "unsupported timing");
            }
        }
    }
    Expect(!Describe(Family::Count) && !Describe(Family::Unknown), "invalid family bounds");
    Expect(!Allows(Family::Ballistic, Delivery::Unknown), "invalid delivery no shift overflow");
    Expect(Allows(Family::Ballistic, Delivery::Pellet) && Allows(Family::Ballistic, Delivery::Fragment), "pellet and fragment components");
    Expect(!Allows(Family::Ballistic, Delivery::Thrown) && Allows(Family::Piercing, Delivery::Thrown)
        && Allows(Family::Cutting, Delivery::Thrown) && Allows(Family::Blunt, Delivery::Thrown), "thrown is not bullet");
    Expect(Timing(Family::Laser, Delivery::Continuous) == TimeBasis::ExposureInterval
        && Timing(Family::Electrical, Delivery::Continuous) == TimeBasis::ExposureInterval, "continuous overrides impulse timing");
    Expect(Timing(Family::Electrical, Delivery::Projectile) == TimeBasis::Contact
        && Timing(Family::Laser, Delivery::Pulse) == TimeBasis::Pulse, "delivery owns time basis");
    Expect(Describe(Family::EMP)->quantity != Describe(Family::Electrical)->quantity, "EMP separate quantity");
    Expect(Describe(Family::Blast)->quantity != Describe(Family::ExternalHeat)->quantity, "blast separate heat");
    auto q = Base(); q.target = "synthetic.robot"; q.engineRegion = 9; q.family = Family::EMP; q.delivery = Delivery::Pulse;
    auto p = Select(base, q);
    Expect(p.status == Status::DefinitionsOnly && p.tissue == TissueKind::Mechanical
        && p.surfaces.size() == 1 && p.surfaces[0].kind == SurfaceKind::MechanicalStructure, "robot has chassis not inventory wear");
    q = Base(); q.target = "synthetic.wearer"; q.wornProfiles = {"synthetic.plate"};
    p = Select(base, q);
    Expect(p.status == Status::DefinitionsOnly && p.surfaces.size() == 2, "worn and natural remain distinct");
    auto c = base; c.targets[2].regions[0].naturalSurfaces.clear();
    p = Select(c, q);
    Expect(p.status == Status::DefinitionsOnly && p.surfaces.size() == 1, "explicitly absent natural protection");
    c.targets[2].regions[0].naturalSetKnown = false;
    Held(c, q, Status::WaitingForDefinition, Reason::NaturalSetUnknown, "unknown natural set is not bare");
    c = base; c.targets[2].regions.push_back(c.targets[1].regions[0]);
    q.engineRegion = 9;
    Expect(Select(c, q).tissue == TissueKind::Mechanical, "mixed target uses region-specific tissue");
    c = base; c.definitions[1].provenance = Provenance::ProvisionalGameplay;
    Expect(Select(c, Base()).surfaces[0].provenance == Provenance::ProvisionalGameplay, "provisional label preserved");
    q = Base(); q.family = Family::Unknown;
    Held(base, q, Status::Unsupported, Reason::Family, "unknown query family");
    q = Base(); q.delivery = Delivery::Unknown;
    Held(base, q, Status::Unsupported, Reason::Delivery, "unknown query delivery");
    c = base; c.targets[0].regions[0].tissue = TissueKind::Unresolved;
    Held(c, Base(), Status::WaitingForDefinition, Reason::Tissue, "unknown tissue");
    c = base; c.targets[0].equipment = EquipmentPolicy::Unresolved;
    Held(c, Base(), Status::WaitingForDefinition, Reason::EquipmentPolicy, "unknown equipment policy");
    q = Base(); q.wornSetKnown = false;
    Held(base, q, Status::WaitingForDefinition, Reason::EquipmentUnknown, "unknown worn set");
    q = Base(); q.target = "unknown";
    Held(base, q, Status::WaitingForDefinition, Reason::TargetMissing, "unknown species no generic human fallback");
    q = Base(); q.engineRegion = 0;
    Held(base, q, Status::WaitingForDefinition, Reason::RegionMissing, "no humanoid region substitution");
    q = Base(); q.wornProfiles = {"synthetic.plate"};
    Held(base, q, Status::InvalidDefinition, Reason::WornSurface, "no-worn target contradicts gear");
    q.target = "synthetic.wearer"; q.wornProfiles = {"unknown"};
    Held(base, q, Status::WaitingForDefinition, Reason::MissingReference, "unclassified gear does not disappear");
    q.wornProfiles = {"synthetic.plate", "synthetic.plate"};
    Held(base, q, Status::InvalidDefinition, Reason::Duplicate, "definition list cannot invent duplicate layers");
    q.wornProfiles = {"synthetic.hide"};
    Held(base, q, Status::WaitingForDefinition, Reason::WornSurface, "hide not inventory");
    q.wornProfiles.assign(33, "synthetic.plate");
    Held(base, q, Status::InvalidDefinition, Reason::Bounds, "worn bound");
    c = base; c.surfaces[1].responses[0].clear();
    Expect(Validate(c).valid, "incomplete matrix legal to author");
    Held(c, Base(), Status::WaitingForDefinition, Reason::ResponseMissing, "missing resistance not immunity or zero");
    c = base; c.targets[0].regions[0].responses[0].clear();
    Held(c, Base(), Status::WaitingForDefinition, Reason::ResponseMissing, "missing tissue susceptibility");
    c = base; c.definitions[1].condition = ConditionLaw::Unresolved;
    Held(c, Base(), Status::WaitingForDefinition, Reason::Condition, "missing condition rule");
    c = base; c.definitions[1].condition = ConditionLaw::ExplicitlyIndependent;
    Expect(Select(c, Base()).status == Status::DefinitionsOnly, "explicit independence is authored");
    c = base; c.surfaces[1].responses[0] = c.surfaces[1].responses[Index(Family::Laser)];
    Held(c, Base(), Status::InvalidDefinition, Reason::BindingMismatch, "no cross-family resistance");
    c = base; c.surfaces[1].responses[0] = c.targets[0].regions[0].responses[0];
    Held(c, Base(), Status::InvalidDefinition, Reason::BindingMismatch, "tissue recipe not material");
    c = base; c.targets[1].regions[0].responses[0] = c.targets[0].regions[0].responses[0];
    Held(c, Base(), Status::InvalidDefinition, Reason::Tissue, "biological recipe cannot substitute for machine");
    c = base; c.targets[0].regions[0].naturalSurfaces = {"synthetic.plate"};
    Held(c, Base(), Status::InvalidDefinition, Reason::NaturalSurface, "worn plate cannot be natural silently");
    c = base; c.targets[0].regions[0].naturalSurfaces.push_back("synthetic.hide");
    Held(c, Base(), Status::InvalidDefinition, Reason::Duplicate, "duplicate natural surface");
    c = base; c.targets[0].regions.push_back(c.targets[0].regions[0]);
    Held(c, Base(), Status::InvalidDefinition, Reason::Duplicate, "duplicate region");
    c = base; c.definitions.push_back(c.definitions[0]);
    Held(c, Base(), Status::InvalidDefinition, Reason::Duplicate, "duplicate definition");
    c = base; c.surfaces.push_back(c.surfaces[0]);
    Held(c, Base(), Status::InvalidDefinition, Reason::Duplicate, "duplicate surface");
    c = base; c.targets.push_back(c.targets[0]);
    Held(c, Base(), Status::InvalidDefinition, Reason::Duplicate, "duplicate target");
    c = base; c.definitions[0].id = "BAD ID";
    Held(c, Base(), Status::InvalidDefinition, Reason::Identifier, "strict identifiers");
    c = base; c.definitions[0].id.assign(64, 'a');
    Held(c, Base(), Status::InvalidDefinition, Reason::Identifier, "bounded identifier");
    c = base; c.surfaces[0].responses[0] = "missing.recipe";
    Held(c, Base(), Status::InvalidDefinition, Reason::MissingReference, "typo is not incomplete authoring");
    c = base; c.definitions[0].family = Family::Unknown;
    Held(c, Base(), Status::InvalidDefinition, Reason::Family, "unknown definition family");
    c = base; c.definitions[0].domain = Domain::Unresolved;
    Held(c, Base(), Status::InvalidDefinition, Reason::Domain, "unknown definition domain");
    c = base; c.definitions[0].provenance = Provenance::Unresolved;
    Held(c, Base(), Status::InvalidDefinition, Reason::Provenance, "unlabelled provenance");
    c = base; c.definitions[0].condition = ConditionLaw::NotApplicable;
    Held(c, Base(), Status::InvalidDefinition, Reason::Condition, "surface must address condition");
    c = base; c.definitions[3].condition = ConditionLaw::AuthoredCurve;
    Held(c, Base(), Status::InvalidDefinition, Reason::Condition, "tissue not item-condition wear");
    c = base; c.definitions[3].tissue = TissueKind::Unresolved;
    Held(c, Base(), Status::InvalidDefinition, Reason::Tissue, "tissue definition requires kind");
    c = base; c.surfaces[0].kind = SurfaceKind::Unresolved;
    Held(c, Base(), Status::InvalidDefinition, Reason::SurfaceKind, "unknown surface kind");
    c = base; c.targets[0].regions[0].engineRegion = -1;
    Held(c, Base(), Status::InvalidDefinition, Reason::Region, "negative region");
    c = base; c.targets[0].regions[0].engineRegion = 256;
    Held(c, Base(), Status::InvalidDefinition, Reason::Region, "bounded region");
    c = base; c.definitions.resize(513);
    Held(c, Base(), Status::InvalidDefinition, Reason::Bounds, "bounded catalogue");
    // Failure after a successful first surface must not leak a partial plan.
    c = base; c.surfaces[1].responses[0].clear();
    q = Base(); q.target = "synthetic.wearer"; q.wornProfiles = {"synthetic.plate"};
    Held(c, q, Status::WaitingForDefinition, Reason::ResponseMissing, "partial plan discarded");
    for (unsigned i = 0; i < 10000; ++i) {
        const auto repeat = Select(base, Base());
        if (repeat.status != Status::DefinitionsOnly || repeat.surfaces.size() != 1) return 2;
    }
    std::cout << "PASS " << checks << " checks; 10000 deterministic selections; synthetic definitions only; gameplay authority 0\n";
}

#include "ResponseDefinitions.hpp"
#include <algorithm>

namespace nvo::responses {
namespace {
constexpr std::uint32_t Bit(Delivery d) { return 1u << static_cast<unsigned>(d); }
constexpr auto projectile = Bit(Delivery::Projectile);
constexpr auto melee = Bit(Delivery::Melee);
constexpr auto thrown = Bit(Delivery::Thrown);
constexpr auto explosion = Bit(Delivery::Explosion);
constexpr auto pulse = Bit(Delivery::Pulse);
constexpr auto continuous = Bit(Delivery::Continuous);
constexpr std::array<FamilyContract, kFamilyCount> contracts{{
    {"ballistic", Quantity::ContactJoules,
     projectile | Bit(Delivery::Pellet) | Bit(Delivery::Fragment),
     "Per-projectile mass, construction, geometry and authoritative contact speed; no shell-total duplication"},
    {"piercing", Quantity::PiercingExposure, melee | thrown | projectile,
     "Authored tip geometry, contact and calibrated piercing measure; bullet thresholds cannot substitute"},
    {"cutting", Quantity::CuttingExposure, melee | thrown | projectile,
     "Authored edge/contact geometry and calibrated cutting measure"},
    {"blunt", Quantity::BluntExposure, melee | thrown | projectile,
     "Authored contact area, transmission and calibrated blunt measure; weapon damage is not energy"},
    {"blast", Quantity::BlastExposure, explosion,
     "Unique blast component, exposure/occlusion and ownership of distance falloff"},
    {"laser", Quantity::LaserExposure, projectile | pulse | continuous,
     "Explicit laser exposure and delivery timing; game damage is not joules"},
    {"plasma", Quantity::PlasmaExposure, projectile | pulse | continuous,
     "Explicit plasma exposure and delivery timing; not an inherited laser coefficient"},
    {"flame", Quantity::ThermalExposure, continuous,
     "Attributed exposure interval and rate; partitioning and burn ownership required"},
    {"external_heat", Quantity::ThermalExposure, explosion | pulse | continuous,
     "Separately identified external heat exposure; not the blast or fragment budget"},
    {"electrical", Quantity::ElectricalExposure, projectile | melee | pulse | continuous,
     "Explicit electrical exposure, contact path and electrical response; visuals do not classify"},
    {"emp", Quantity::EMPExposure, projectile | explosion | pulse | continuous,
     "Explicit EMP component and electronic susceptibility; no inferred biological wound"}
}};
bool Id(const std::string& s) {
    if (s.empty() || s.size() > 63) return false;
    return std::all_of(s.begin(), s.end(), [](unsigned char c) {
        return (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '.' || c == '-';
    });
}
template<class T> const T* Find(const std::vector<T>& list, const std::string& id) {
    const auto it = std::find_if(list.begin(), list.end(), [&](const T& x) { return x.id == id; });
    return it == list.end() ? nullptr : &*it;
}
template<class T> Check Identifiers(const std::vector<T>& list) {
    for (std::size_t i = 0; i < list.size(); ++i) {
        if (!Id(list[i].id)) return {false, Reason::Identifier};
        for (std::size_t j = 0; j < i; ++j)
            if (list[j].id == list[i].id) return {false, Reason::Duplicate};
    }
    return {true, Reason::None};
}
Check CheckBindings(const Catalogue& c, const Bindings& bindings, Domain domain) {
    for (std::size_t i = 0; i < kFamilyCount; ++i) {
        if (bindings[i].empty()) continue; // legal incomplete authoring, held by Select
        if (!Id(bindings[i])) return {false, Reason::Identifier};
        const auto* d = Find(c.definitions, bindings[i]);
        if (!d) return {false, Reason::MissingReference};
        if (d->domain != domain || static_cast<unsigned>(d->family) != i)
            return {false, Reason::BindingMismatch};
    }
    return {true, Reason::None};
}
Plan Fail(Status status, Reason reason) {
    Plan p;
    p.status = status;
    p.reason = reason;
    return p; // never return a partial definition plan
}
} // namespace

const FamilyContract* Describe(Family family) {
    const auto i = static_cast<unsigned>(family);
    return i < contracts.size() ? &contracts[i] : nullptr;
}
bool Allows(Family family, Delivery delivery) {
    const auto* d = Describe(family);
    return d && static_cast<unsigned>(delivery) < static_cast<unsigned>(Delivery::Count)
        && (d->deliveries & Bit(delivery)) != 0;
}
TimeBasis Timing(Family family, Delivery delivery) {
    if (!Allows(family, delivery)) return TimeBasis::Unresolved;
    if (delivery == Delivery::Continuous) return TimeBasis::ExposureInterval;
    if (delivery == Delivery::Pulse || delivery == Delivery::Explosion) return TimeBasis::Pulse;
    return TimeBasis::Contact;
}
Check Validate(const Catalogue& c) {
    if (c.definitions.size() > 512 || c.surfaces.size() > 128 || c.targets.size() > 128)
        return {false, Reason::Bounds};
    for (const auto check : {Identifiers(c.definitions), Identifiers(c.surfaces), Identifiers(c.targets)})
        if (!check.valid) return check;
    for (const auto& d : c.definitions) {
        if (!Describe(d.family)) return {false, Reason::Family};
        if (d.domain != Domain::Surface && d.domain != Domain::Tissue) return {false, Reason::Domain};
        if (d.provenance != Provenance::SyntheticFixture && d.provenance != Provenance::ProvisionalGameplay
            && d.provenance != Provenance::ReviewedGameplay) return {false, Reason::Provenance};
        if (d.domain == Domain::Tissue) {
            if (d.condition != ConditionLaw::NotApplicable) return {false, Reason::Condition};
            if (d.tissue != TissueKind::Biological && d.tissue != TissueKind::Mechanical)
                return {false, Reason::Tissue};
        } else if (d.condition != ConditionLaw::Unresolved && d.condition != ConditionLaw::AuthoredCurve
                   && d.condition != ConditionLaw::ExplicitlyIndependent) return {false, Reason::Condition};
        if (d.domain == Domain::Surface && d.tissue != TissueKind::Unresolved) return {false, Reason::Tissue};
    }
    for (const auto& s : c.surfaces) {
        if (s.kind != SurfaceKind::WornItem && s.kind != SurfaceKind::NaturalProtection
            && s.kind != SurfaceKind::MechanicalStructure) return {false, Reason::SurfaceKind};
        if (!Id(s.construction)) return {false, Reason::Identifier};
        const auto check = CheckBindings(c, s.responses, Domain::Surface);
        if (!check.valid) return check;
    }
    for (const auto& t : c.targets) {
        if (t.equipment != EquipmentPolicy::Unresolved && t.equipment != EquipmentPolicy::WornAllowed
            && t.equipment != EquipmentPolicy::NoWornEquipment) return {false, Reason::EquipmentPolicy};
        if (t.regions.size() > 64) return {false, Reason::Bounds};
        for (std::size_t i = 0; i < t.regions.size(); ++i) {
            const auto& r = t.regions[i];
            if (r.engineRegion < 0 || r.engineRegion > 255) return {false, Reason::Region};
            if (!Id(r.location)) return {false, Reason::Identifier};
            if (r.tissue != TissueKind::Biological && r.tissue != TissueKind::Mechanical
                && r.tissue != TissueKind::Unresolved) return {false, Reason::Tissue};
            for (std::size_t j = 0; j < i; ++j)
                if (t.regions[j].engineRegion == r.engineRegion || t.regions[j].location == r.location)
                    return {false, Reason::Duplicate};
            if (r.naturalSurfaces.size() > 32) return {false, Reason::Bounds};
            for (std::size_t j = 0; j < r.naturalSurfaces.size(); ++j) {
                const auto* s = Find(c.surfaces, r.naturalSurfaces[j]);
                if (!s) return {false, Reason::MissingReference};
                if (s->kind == SurfaceKind::WornItem) return {false, Reason::NaturalSurface};
                for (std::size_t k = 0; k < j; ++k)
                    if (r.naturalSurfaces[k] == r.naturalSurfaces[j]) return {false, Reason::Duplicate};
            }
            const auto check = CheckBindings(c, r.responses, Domain::Tissue);
            if (!check.valid) return check;
            for (const auto& id : r.responses) {
                const auto* d = Find(c.definitions, id);
                if (d && r.tissue != TissueKind::Unresolved && d->tissue != r.tissue)
                    return {false, Reason::Tissue};
            }
        }
    }
    return {true, Reason::None};
}
Plan Select(const Catalogue& c, const Query& q) {
    const auto check = Validate(c);
    if (!check.valid) return Fail(Status::InvalidDefinition, check.reason);
    if (!Describe(q.family)) return Fail(Status::Unsupported, Reason::Family);
    if (!Allows(q.family, q.delivery)) return Fail(Status::Unsupported, Reason::Delivery);
    if (q.wornProfiles.size() > 32) return Fail(Status::InvalidDefinition, Reason::Bounds);
    for (std::size_t i = 0; i < q.wornProfiles.size(); ++i) {
        if (!Id(q.wornProfiles[i])) return Fail(Status::InvalidDefinition, Reason::Identifier);
        for (std::size_t j = 0; j < i; ++j)
            if (q.wornProfiles[i] == q.wornProfiles[j]) return Fail(Status::InvalidDefinition, Reason::Duplicate);
    }
    const auto* target = Find(c.targets, q.target);
    if (!target) return Fail(Status::WaitingForDefinition, Reason::TargetMissing);
    const auto region = std::find_if(target->regions.begin(), target->regions.end(),
        [&](const RegionProfile& r) { return r.engineRegion == q.engineRegion; });
    if (region == target->regions.end()) return Fail(Status::WaitingForDefinition, Reason::RegionMissing);
    if (region->tissue == TissueKind::Unresolved) return Fail(Status::WaitingForDefinition, Reason::Tissue);
    if (!region->naturalSetKnown) return Fail(Status::WaitingForDefinition, Reason::NaturalSetUnknown);
    if (target->equipment == EquipmentPolicy::Unresolved)
        return Fail(Status::WaitingForDefinition, Reason::EquipmentPolicy);
    if (!q.wornSetKnown) return Fail(Status::WaitingForDefinition, Reason::EquipmentUnknown);
    if (target->equipment == EquipmentPolicy::NoWornEquipment && !q.wornProfiles.empty())
        return Fail(Status::InvalidDefinition, Reason::WornSurface);
    const auto f = static_cast<unsigned>(q.family);
    const auto* tissue = Find(c.definitions, region->responses[f]);
    if (!tissue) return Fail(Status::WaitingForDefinition, Reason::ResponseMissing);
    Plan plan;
    plan.status = Status::DefinitionsOnly;
    plan.target = target->id;
    plan.location = region->location;
    plan.tissue = region->tissue;
    plan.tissueResponse = tissue->id;
    plan.tissueProvenance = tissue->provenance;
    auto append = [&](const std::string& id, bool worn) -> Reason {
        const auto* s = Find(c.surfaces, id);
        if (!s) return Reason::MissingReference;
        if (worn && s->kind != SurfaceKind::WornItem) return Reason::WornSurface;
        const auto* d = Find(c.definitions, s->responses[f]);
        if (!d) return Reason::ResponseMissing;
        if (d->condition == ConditionLaw::Unresolved) return Reason::Condition;
        plan.surfaces.push_back({s->id, s->kind, d->id, d->condition, d->provenance});
        return Reason::None;
    };
    for (const auto& id : q.wornProfiles) {
        const auto reason = append(id, true);
        if (reason != Reason::None) return Fail(Status::WaitingForDefinition, reason);
    }
    for (const auto& id : region->naturalSurfaces) {
        const auto reason = append(id, false);
        if (reason != Reason::None) return Fail(Status::WaitingForDefinition, reason);
    }
    return plan;
}
} // namespace nvo::responses

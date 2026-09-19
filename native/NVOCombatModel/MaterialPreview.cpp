#include "MaterialPreview.hpp"
#include <algorithm>
#include <cmath>

namespace nvo::materials {
namespace {
bool Nonnegative(double x) { return std::isfinite(x) && x >= 0; }
bool Fraction(double x) { return Nonnegative(x) && x <= 1; }
template<class T> const T* FindId(const std::vector<T>& rows, const std::string& id) {
    const auto p = std::find_if(rows.begin(), rows.end(), [&](const T& row) { return row.id == id; });
    return p == rows.end() ? nullptr : &*p;
}
template<class T> const T* FindRule(const std::vector<T>& rows, const std::string& id) {
    const auto p = std::find_if(rows.begin(), rows.end(), [&](const T& row) { return row.definition == id; });
    return p == rows.end() ? nullptr : &*p;
}
Result Fail(Status status, Reason reason) {
    Result r; r.status = status; r.reason = reason; return r;
}
Result EvidenceFailure(const shadow::EvidenceCheck& check) {
    const auto status = check.status == shadow::Status::InvalidInput ? Status::InvalidInput
        : check.status == shadow::Status::Unsupported ? Status::Unsupported : Status::WaitingForEvidence;
    auto r = Fail(status, Reason::Evidence); r.evidenceReason = check.reason; return r;
}
bool ValidCurve(const SurfaceRule& s) {
    if (s.condition == responses::ConditionLaw::ExplicitlyIndependent) return s.curve.empty();
    if (s.condition != responses::ConditionLaw::AuthoredCurve || s.curve.size() < 2 || s.curve.size() > 8)
        return false;
    if (s.curve.front().condition != 0 || s.curve.back().condition != 1 || s.curve.back().scale != 1)
        return false;
    for (std::size_t i = 0; i < s.curve.size(); ++i) {
        const auto& p = s.curve[i];
        if (!Fraction(p.condition) || !Fraction(p.scale)) return false;
        if (i && (p.condition <= s.curve[i - 1].condition || p.scale < s.curve[i - 1].scale)) return false;
    }
    return true;
}
bool ValidNumbers(const responses::Catalogue& c, const NumericProfiles& n) {
    if (n.surfaces.size() > 512 || n.tissues.size() > 512) return false;
    for (std::size_t i = 0; i < n.surfaces.size(); ++i) {
        const auto& s = n.surfaces[i];
        const auto* d = FindId(c.definitions, s.definition);
        if (!d || d->domain != responses::Domain::Surface || d->family != responses::Family::Ballistic
            || d->provenance != s.provenance || d->condition != s.condition || !ValidCurve(s)
            || !Fraction(s.transmittedFraction) || !Nonnegative(s.lossPerStoppedJ)) return false;
        for (double capacity : s.stoppingJ) if (!Nonnegative(capacity)) return false;
        for (std::size_t j = 0; j < i; ++j) if (n.surfaces[j].definition == s.definition) return false;
    }
    for (std::size_t i = 0; i < n.tissues.size(); ++i) {
        const auto& t = n.tissues[i];
        const auto* d = FindId(c.definitions, t.definition);
        if (!d || d->domain != responses::Domain::Tissue || d->family != responses::Family::Ballistic
            || d->provenance != t.provenance || d->tissue != t.tissue
            || !Fraction(t.coupling) || !Nonnegative(t.directHpPerJ)
            || !Nonnegative(t.transmittedHpPerJ) || !Nonnegative(t.regionalLossPerHp)) return false;
        for (std::size_t j = 0; j < i; ++j) if (n.tissues[j].definition == t.definition) return false;
    }
    return true;
}
double Scale(const SurfaceRule& s, double condition) {
    if (s.condition == responses::ConditionLaw::ExplicitlyIndependent) return 1;
    for (std::size_t i = 1; i < s.curve.size(); ++i) {
        const auto& hi = s.curve[i];
        const auto& lo = s.curve[i - 1];
        if (condition <= hi.condition) {
            const double t = (condition - lo.condition) / (hi.condition - lo.condition);
            return lo.scale + t * (hi.scale - lo.scale);
        }
    }
    return model::unknown; // callers reject; never guess a fallback capacity
}
} // namespace

Result Evaluate(const responses::Catalogue& catalogue, const NumericProfiles& numbers, const Input& in) {
    // Deliberate explicit mapping. No cast into the legacy five-family arrays.
    if (in.family != responses::Family::Ballistic) return Fail(Status::Unsupported, Reason::Family);
    if (!responses::Allows(in.family, in.delivery)) return Fail(Status::Unsupported, Reason::Delivery);
    const auto identityCheck = shadow::CheckIdentityAndMode(in.identity, in.mode);
    if (!identityCheck.ready) return EvidenceFailure(identityCheck);
    if (!in.region.hitDataVerified || !in.region.collisionVerified || in.region.hitData < 0
        || in.region.hitData > 255 || in.region.collision < 0 || in.region.collision > 255
        || in.region.hitData != in.region.collision) return Fail(Status::WaitingForEvidence, Reason::Region);
    if (!in.modifierOwnershipVerified) return Fail(Status::WaitingForEvidence, Reason::ModifierOwnership);
    if (!in.targetBindingVerified) return Fail(Status::WaitingForEvidence, Reason::TargetBinding);
    const auto bindingCheck = binding::Validate(in.identity, in.mode, in.region.hitData, in.binding);
    if (!bindingCheck.ready) {
        auto r = Fail(Status::WaitingForEvidence, Reason::ImpactBinding);
        r.bindingReason = bindingCheck.reason; return r;
    }
    const auto& snapshot = in.snapshot;
    if (!snapshot.wornComplete || !snapshot.naturalComplete || !snapshot.coverageComplete
        || !snapshot.atImpactVerified || snapshot.order != shadow::LayerOrder::OutermostToInnermost)
        return Fail(Status::WaitingForEvidence, Reason::Snapshot);
    if (snapshot.surfaces.size() > 64) return Fail(Status::InvalidInput, Reason::Snapshot);
    const auto kineticCheck = shadow::CheckKineticInputs(in.identity, in.kinetic, in.speed);
    if (!kineticCheck.ready) return EvidenceFailure(kineticCheck);
    // Projectile velocity is authoritative only if all shared producer/contact/
    // unit gates passed above. No interval endpoint or muzzle-speed substitution.
    const double incident = 0.5 * in.kinetic.mass.value * in.speed.exact.value * in.speed.exact.value;
    if (!Nonnegative(incident)) return Fail(Status::InvalidInput, Reason::Arithmetic);

    responses::Query query;
    query.family = responses::Family::Ballistic; query.delivery = in.delivery;
    query.target = in.targetProfile; query.engineRegion = in.region.hitData;
    query.wornSetKnown = snapshot.wornComplete;
    std::size_t contacts = 0;
    for (std::size_t i = 0; i < snapshot.surfaces.size(); ++i) {
        const auto& s = snapshot.surfaces[i];
        if (!s.key) return Fail(Status::InvalidInput, Reason::SurfaceIdentity);
        for (std::size_t j = 0; j < i; ++j)
            if (snapshot.surfaces[j].key == s.key) return Fail(Status::InvalidInput, Reason::SurfaceIdentity);
        if (!s.bindingVerified) return Fail(Status::WaitingForEvidence, Reason::SurfaceBinding);
        if (s.kind != responses::SurfaceKind::WornItem && s.kind != responses::SurfaceKind::NaturalProtection
            && s.kind != responses::SurfaceKind::MechanicalStructure)
            return Fail(Status::InvalidInput, Reason::SurfaceBinding);
        if (s.contact != Contact::Hit && s.contact != Contact::Miss)
            return Fail(Status::WaitingForEvidence, Reason::Contact);
        if (s.contact == Contact::Hit) {
            ++contacts;
            if (!s.conditionVerified) return Fail(Status::WaitingForEvidence, Reason::Condition);
            if (!Fraction(s.condition)) return Fail(Status::InvalidInput, Reason::Condition);
        }
        if (s.kind == responses::SurfaceKind::WornItem
            && std::find(query.wornProfiles.begin(), query.wornProfiles.end(), s.profile) == query.wornProfiles.end())
            query.wornProfiles.push_back(s.profile); // deduplicate definitions, never instances
    }
    if ((contacts == 0) != snapshot.bareVerified) return Fail(Status::WaitingForEvidence, Reason::Snapshot);

    const auto plan = responses::Select(catalogue, query);
    if (plan.status != responses::Status::DefinitionsOnly) {
        auto r = Fail(plan.status == responses::Status::InvalidDefinition ? Status::InvalidInput
            : plan.status == responses::Status::Unsupported ? Status::Unsupported : Status::WaitingForEvidence,
            Reason::Definitions);
        r.definitionReason = plan.reason; return r;
    }
    // The complete mapped natural set must be present, including independently
    // verified misses. Worn instances may share a definition; natural bindings
    // name one region-specific surface each in this revision.
    for (const auto& expected : plan.surfaces) {
        std::size_t count = 0;
        for (const auto& s : snapshot.surfaces) if (s.profile == expected.profile && s.kind == expected.kind) ++count;
        if (count == 0 || (expected.kind != responses::SurfaceKind::WornItem && count != 1))
            return Fail(Status::WaitingForEvidence, Reason::SurfaceSet);
    }
    for (const auto& s : snapshot.surfaces) {
        const auto p = std::find_if(plan.surfaces.begin(), plan.surfaces.end(),
            [&](const responses::SurfaceBinding& b) { return b.profile == s.profile && b.kind == s.kind; });
        if (p == plan.surfaces.end()) return Fail(Status::WaitingForEvidence, Reason::SurfaceSet);
    }
    if (!ValidNumbers(catalogue, numbers)) return Fail(Status::InvalidInput, Reason::NumericProfiles);
    const auto* target = FindRule(numbers.tissues, plan.tissueResponse);
    if (!target) return Fail(Status::WaitingForEvidence, Reason::NumericBinding);

    std::vector<model::KineticLayer> layers;
    std::vector<SurfaceChange> changes;
    for (const auto& s : snapshot.surfaces) {
        if (s.contact == Contact::Miss) continue;
        const auto binding = std::find_if(plan.surfaces.begin(), plan.surfaces.end(),
            [&](const responses::SurfaceBinding& b) { return b.profile == s.profile; });
        const auto* rule = FindRule(numbers.surfaces, binding->response);
        if (!rule) return Fail(Status::WaitingForEvidence, Reason::NumericBinding);
        const double scale = Scale(*rule, s.condition);
        if (!Fraction(scale)) return Fail(Status::InvalidInput, Reason::Arithmetic);
        const double capacity = rule->stoppingJ[static_cast<unsigned>(in.kinetic.construction)] * scale;
        if (!Nonnegative(capacity)) return Fail(Status::InvalidInput, Reason::Arithmetic);
        layers.push_back({s.key, capacity, s.condition, rule->transmittedFraction, rule->lossPerStoppedJ});
        SurfaceChange change;
        change.key = s.key; change.kind = s.kind; change.target = in.identity.target;
        change.engineRegion = in.region.hitData; change.profile = s.profile;
        change.definition = rule->definition; change.provenance = rule->provenance;
        changes.push_back(change);
    }
    const auto budget = model::ResolveKineticLayers(incident, layers);
    if (budget.status != model::Status::PreviewOnly) {
        auto r = Fail(Status::InvalidInput, Reason::Arithmetic); r.modelReason = budget.reason; return r;
    }
    const double hp = budget.residualJ * target->coupling * target->directHpPerJ
                      + budget.transmittedJ * target->transmittedHpPerJ;
    const double regional = hp * target->regionalLossPerHp;
    if (!Nonnegative(hp) || !Nonnegative(regional)) return Fail(Status::InvalidInput, Reason::Arithmetic);
    for (std::size_t i = 0; i < changes.size(); ++i) {
        const double loss = budget.layers[i].conditionLoss;
        auto& change = changes[i];
        if (change.kind == responses::SurfaceKind::WornItem) change.wornConditionLoss = loss;
        else if (change.kind == responses::SurfaceKind::NaturalProtection) change.naturalStructureLoss = loss;
        else change.mechanicalStructureLoss = loss;
    }
    Result r;
    r.status = Status::PreviewOnly; r.reason = Reason::None;
    r.identity = in.identity; r.mode = in.mode.value; r.engineRegion = in.region.hitData;
    r.impactScope = in.binding.expected;
    r.definitions = plan; r.energy = budget; r.surfaces = changes;
    r.protectionPenetrated = !layers.empty() && budget.residualJ > 0;
    if (plan.tissue == responses::TissueKind::Biological) {
        r.biologicalHp = hp; r.biologicalRegionalLoss = regional;
        r.biologicalWoundEligible = budget.residualJ > 0 && target->coupling > 0;
        r.payloadEligible = in.kinetic.woundPayload && r.biologicalWoundEligible;
    } else {
        r.mechanicalHp = hp; r.mechanicalRegionalLoss = regional;
    }
    return r;
}
} // namespace nvo::materials

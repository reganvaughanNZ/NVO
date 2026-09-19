#include "ArmourModel.hpp"
#include <algorithm>
#include <cmath>

namespace nvo::model {
namespace {
bool Nonnegative(double x) { return std::isfinite(x) && x >= 0; }
bool Fraction(double x) { return Nonnegative(x) && x <= 1; }
bool Measure(const Measurement& m, Unit u, bool positive = false) {
    return m.verified && m.unit == u && Nonnegative(m.value) && (!positive || m.value > 0);
}
Preview Reject(Status s, Reason r) { Preview p; p.status = s; p.reason = r; return p; }
}
KineticBudget ResolveKineticLayers(double incidentJ, const std::vector<KineticLayer>& layers) {
    auto reject = [](Reason reason) { KineticBudget b; b.reason = reason; return b; };
    if (!Nonnegative(incidentJ)) return reject(Reason::Arithmetic);
    if (layers.size() > 64) return reject(Reason::Layer);
    for (std::size_t i = 0; i < layers.size(); ++i) {
        const auto& l = layers[i];
        if (!l.key || !Nonnegative(l.stoppingJ) || !Fraction(l.condition)
            || !Fraction(l.transmittedFraction) || !Nonnegative(l.lossPerStoppedJ))
            return reject(Reason::Layer);
        for (std::size_t j = 0; j < i; ++j)
            if (layers[j].key == l.key) return reject(Reason::Layer);
    }
    KineticBudget b;
    b.incidentJ = incidentJ; b.residualJ = incidentJ;
    for (const auto& l : layers) {
        const double stopped = std::min(b.residualJ, l.stoppingJ);
        const double transmitted = stopped * l.transmittedFraction;
        const double loss = stopped * l.lossPerStoppedJ;
        if (!Nonnegative(loss)) return reject(Reason::Arithmetic);
        b.layers.push_back({l.key, b.residualJ, stopped, b.residualJ - stopped,
                           transmitted, stopped - transmitted, std::min(l.condition, loss)});
        b.residualJ -= stopped;
        b.stoppedJ += stopped;
        b.transmittedJ += transmitted;
        b.retainedJ += stopped - transmitted;
    }
    if (!Nonnegative(b.residualJ) || !Nonnegative(b.stoppedJ) || !Nonnegative(b.transmittedJ)
        || !Nonnegative(b.retainedJ) || b.residualJ > incidentJ || b.transmittedJ > b.stoppedJ)
        return reject(Reason::Arithmetic);
    b.status = Status::PreviewOnly; b.reason = Reason::None;
    return b;
}
Preview Resolve(const Context& c, const Threat& t, const TargetProfile& a, const std::vector<Layer>& layers) {
    if (!c.session || !c.component || !c.application || !c.source || !c.target ||
        !c.identitiesVerified || !c.pathVerified || !c.modifierOwnershipVerified || !c.armourComplete ||
        (c.mode != Mode::RealTime && c.mode != Mode::Vats))
        return Reject(Status::Unsupported, Reason::Context);
    if (!Cover(c.actualRegion)) return Reject(Status::Unsupported, Reason::Region);
    if (t.family < Family::Kinetic || t.family >= Family::Unsupported || !t.profileVerified)
        return Reject(Status::Unsupported, Reason::Family);
    const bool kinetic = t.family == Family::Kinetic;
    if (t.woundPayload && !kinetic) return Reject(Status::Unsupported, Reason::Profile);
    const Unit unit = kinetic ? Unit::Joules : Unit::Dose;
    if (!a.verified || (a.anatomy != Anatomy::Biological && a.anatomy != Anatomy::Mechanical) ||
        a.inputUnit != unit || !Fraction(a.tissueCoupling) || !Nonnegative(a.directHpPerUnit) ||
        !Nonnegative(a.bluntHpPerJoule) || !Nonnegative(a.limbPerHp))
        return Reject(Status::InvalidInput, Reason::Profile);
    double incident{};
    if (kinetic) {
        if (!t.contactVerified || !t.unitsCalibrated) return Reject(Status::Unsupported, Reason::Measurement);
        if (t.construction < Construction::Ball || t.construction >= Construction::Unknown ||
            !Measure(t.mass, Unit::Kilograms, true) || !Measure(t.diameter, Unit::Metres, true) ||
            !Measure(t.impactSpeed, Unit::MetresPerSecond))
            return Reject(Status::InvalidInput, Reason::Measurement);
        incident = 0.5 * t.mass.value * t.impactSpeed.value * t.impactSpeed.value;
    } else if (t.family == Family::Flame) {
        if (!Measure(t.doseRate, Unit::DosePerGameSecond) || !Measure(t.duration, Unit::GameSeconds))
            return Reject(Status::InvalidInput, Reason::Measurement);
        incident = t.doseRate.value * t.duration.value;
    } else {
        if (!Measure(t.dose, Unit::Dose)) return Reject(Status::InvalidInput, Reason::Measurement);
        incident = t.dose.value;
    }
    if (!Nonnegative(incident)) return Reject(Status::InvalidInput, Reason::Arithmetic);
    // Validate the entire input before calculating: no partial preview escapes.
    // An adapter must supply only its complete, ordered relevant armour snapshot.
    for (std::size_t i = 0; i < layers.size(); ++i) {
        const auto& l = layers[i];
        if (!l.instance || !l.coverage || (l.coverage & ~63u) || !Fraction(l.condition) || !l.profileVerified)
            return Reject(Status::Unsupported, Reason::Layer);
        for (std::size_t j = 0; j < i; ++j)
            if (layers[j].instance == l.instance) return Reject(Status::InvalidInput, Reason::Layer);
        if (!(l.coverage & Cover(c.actualRegion))) continue;
        const auto& r = l.response[static_cast<unsigned>(t.family)];
        if (!r.supported || r.unit != unit) return Reject(Status::Unsupported, Reason::Layer);
        if (!Nonnegative(r.wearPerAbsorbedUnit)) return Reject(Status::InvalidInput, Reason::Layer);
        if (kinetic) {
            if (!Fraction(r.bluntFraction) || !Nonnegative(r.resistanceJ[static_cast<unsigned>(t.construction)]))
                return Reject(Status::InvalidInput, Reason::Layer);
        } else if (!Fraction(r.shieldFraction)) return Reject(Status::InvalidInput, Reason::Layer);
    }
    Preview p;
    p.unit = unit; p.incident = incident; p.residual = incident;
    if (kinetic) {
        std::vector<KineticLayer> contacts;
        for (const auto& l : layers) {
            if (!(l.coverage & Cover(c.actualRegion))) continue;
            const auto& r = l.response[static_cast<unsigned>(Family::Kinetic)];
            contacts.push_back({l.instance, r.resistanceJ[static_cast<unsigned>(t.construction)] * l.condition,
                                l.condition, r.bluntFraction, r.wearPerAbsorbedUnit});
        }
        const auto budget = ResolveKineticLayers(incident, contacts);
        if (budget.status != Status::PreviewOnly) return Reject(budget.status, budget.reason);
        p.residual = budget.residualJ; p.absorbed = budget.stoppedJ; p.bluntJoules = budget.transmittedJ;
        for (const auto& row : budget.layers) p.wear.push_back({row.key, row.conditionLoss});
    } else for (const auto& l : layers) {
        if (!(l.coverage & Cover(c.actualRegion))) continue;
        const auto& r = l.response[static_cast<unsigned>(t.family)];
        const double absorbed = p.residual * (r.shieldFraction * l.condition);
        p.residual -= absorbed;
        p.absorbed += absorbed;
        const double wear = absorbed * r.wearPerAbsorbedUnit;
        if (!Nonnegative(wear)) return Reject(Status::InvalidInput, Reason::Arithmetic);
        p.wear.push_back({l.instance, std::min(l.condition, wear)});
    }
    p.directHp = p.residual * a.tissueCoupling * a.directHpPerUnit + p.bluntJoules * a.bluntHpPerJoule;
    p.limb = p.directHp * a.limbPerHp;
    if (!Nonnegative(p.directHp) || !Nonnegative(p.limb) || !Nonnegative(p.residual) ||
        !Nonnegative(p.absorbed) || !Nonnegative(p.bluntJoules) || p.residual > incident || p.bluntJoules > p.absorbed)
        return Reject(Status::InvalidInput, Reason::Arithmetic);
    p.armourPenetrated = kinetic && p.residual > 0;
    p.biologicalWoundEligible = p.armourPenetrated && a.anatomy == Anatomy::Biological && a.tissueCoupling > 0;
    p.woundPayloadEligible = t.woundPayload && p.biologicalWoundEligible;
    p.mechanicalDamage = a.anatomy == Anatomy::Mechanical && p.directHp > 0;
    p.status = Status::PreviewOnly; p.reason = Reason::None;
    return p;
}
}

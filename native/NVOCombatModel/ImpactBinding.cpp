#include "ImpactBinding.hpp"

namespace nvo::binding {
namespace {
bool Complete(const Stamp& s) noexcept {
    return s.generation && s.session && s.transaction && s.copyOrdinal && s.lifetime
        && s.component && s.application && s.profile && s.source && s.target
        && s.carrier && s.weapon && s.ammo && s.region >= 0 && s.region <= 255
        && (s.mode == model::Mode::RealTime || s.mode == model::Mode::Vats);
}
bool Same(const Stamp& a, const Stamp& b) noexcept {
    // Field comparison intentionally avoids padding-dependent memcmp.
    return a.generation == b.generation && a.session == b.session
        && a.transaction == b.transaction && a.copyOrdinal == b.copyOrdinal
        && a.lifetime == b.lifetime && a.component == b.component
        && a.application == b.application && a.profile == b.profile
        && a.source == b.source && a.target == b.target && a.carrier == b.carrier
        && a.weapon == b.weapon && a.ammo == b.ammo && a.region == b.region && a.mode == b.mode;
}
} // namespace
Check Validate(const shadow::IdentityEvidence& id, const shadow::ModeEvidence& mode,
               int region, const Evidence& e) noexcept {
    const auto& s = e.expected;
    if (!Complete(s)) return {false, Reason::ExpectedScopeMissing};
    if (s.session != id.session || s.component != id.component || s.application != id.application
        || s.profile != id.profile || s.source != id.source || s.target != id.target
        || s.carrier != id.carrier || s.weapon != id.weapon || s.ammo != id.ammo
        || s.region != region || s.mode != mode.value)
        return {false, Reason::ExpectedIdentityMismatch};
    if (!Complete(e.contact)) return {false, Reason::ContactScopeMissing};
    if (!Same(s, e.contact)) return {false, Reason::ContactScopeMismatch};
    if (!Complete(e.snapshot)) return {false, Reason::SnapshotScopeMissing};
    if (!Same(s, e.snapshot)) return {false, Reason::SnapshotScopeMismatch};
    if (!e.exactCopyScopeVerified) return {false, Reason::CopyScopeUnverified};
    if (!e.contactPositionAssociated) return {false, Reason::ContactPositionUnverified};
    if (e.contactProducer != ContactProducer::VerifiedExactContact)
        return {false, Reason::ContactProducerUnqualified};
    if (e.snapshotProducer != SnapshotProducer::VerifiedAtImpact)
        return {false, Reason::SnapshotProducerUnqualified};
    return {true, Reason::None};
}
const char* ReasonName(Reason reason) noexcept {
    switch (reason) {
    case Reason::None: return "none";
    case Reason::ExpectedScopeMissing: return "expected_scope_missing";
    case Reason::ExpectedIdentityMismatch: return "expected_identity_mismatch";
    case Reason::ContactScopeMissing: return "contact_scope_missing";
    case Reason::ContactScopeMismatch: return "contact_scope_mismatch";
    case Reason::SnapshotScopeMissing: return "snapshot_scope_missing";
    case Reason::SnapshotScopeMismatch: return "snapshot_scope_mismatch";
    case Reason::CopyScopeUnverified: return "copy_scope_unverified";
    case Reason::ContactPositionUnverified: return "contact_position_unverified";
    case Reason::ContactProducerUnqualified: return "contact_producer_unqualified";
    case Reason::SnapshotProducerUnqualified: return "snapshot_producer_unqualified";
    }
    return "invalid_binding_reason";
}
} // namespace nvo::binding

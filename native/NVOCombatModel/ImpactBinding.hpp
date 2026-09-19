#pragma once
#include "ShadowAdapter.hpp"

// Offline provenance contract. No engine reader, live provider or permission to
// apply damage. Matching keys do not establish committed engine loss.
namespace nvo::binding {
inline constexpr bool kRuntimeIntegrated = false;
inline constexpr bool kGameplayWrites = false;
struct Stamp {
    std::uint64_t generation{}, session{}, transaction{}, copyOrdinal{}, lifetime{};
    std::uint64_t component{}, application{}, profile{};
    std::uint32_t source{}, target{}, carrier{}, weapon{}, ammo{};
    int region{-1};
    model::Mode mode{model::Mode::Unknown};
};
enum class ContactProducer {
    Unknown, OwnedStepInterval, EngineSegmentMean, PointModelEstimate, MuzzleEstimate,
    VerifiedExactContact // reserved contract: NO current runtime provider qualifies
};
enum class SnapshotProducer {
    Unknown, StableCopyInput,
    VerifiedAtImpact // reserved contract: stable double reads alone do not qualify
};
struct Evidence {
    // Expected comes from the consumer's current call, never a reused cached
    // observation. Producer stamps must be captured independently with payloads.
    Stamp expected, contact, snapshot;
    ContactProducer contactProducer{ContactProducer::Unknown};
    SnapshotProducer snapshotProducer{SnapshotProducer::Unknown};
    bool exactCopyScopeVerified{};
    bool contactPositionAssociated{}; // hit-to-contact, not collision-to-reread
};
enum class Reason {
    None, ExpectedScopeMissing, ExpectedIdentityMismatch, ContactScopeMissing,
    ContactScopeMismatch, SnapshotScopeMissing, SnapshotScopeMismatch,
    CopyScopeUnverified, ContactPositionUnverified, ContactProducerUnqualified,
    SnapshotProducerUnqualified
};
struct Check { bool ready{}; Reason reason{Reason::ExpectedScopeMissing}; };
// These gates supplement, never replace, the existing identity/path/mode,
// actual-region, exact-speed/unit, snapshot and profile checks.
Check Validate(const shadow::IdentityEvidence&, const shadow::ModeEvidence&,
               int actualRegion, const Evidence&) noexcept;
const char* ReasonName(Reason) noexcept;
} // namespace nvo::binding

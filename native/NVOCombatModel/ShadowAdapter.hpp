#pragma once
#include "ArmourModel.hpp"

// Packet 4A: pure, read-only evidence adapter for armour shadow previews.
// It has no engine/NVSE headers, hooks, logging, mutation or application API.
namespace nvo::shadow {
inline constexpr bool kGameplayWrites = false;
inline constexpr bool kRuntimeIntegrated = false;
inline constexpr unsigned kContractVersion = 1;

enum class Status { PreviewOnly, WaitingForEvidence, Unsupported, InvalidInput };
enum class Reason {
    None,
    Identity,
    Component,
    Path,
    Mode,
    RegionUnavailable,
    RegionConflict,
    ModifierOwnership,
    ArmourSnapshot,
    ArmourContradiction,
    Family,
    ThreatProfile,
    SpeedUnavailable,
    SpeedInterval,
    SpeedProducer,
    SpeedUnits,
    TargetProfile,
    Resolver
};
enum class Shape { Missing, Exact, Interval, Ambiguous };
enum class LayerOrder { Unknown, OutermostToInnermost };

struct IdentityEvidence {
    std::uint64_t session{}, component{}, application{}, profile{};
    std::uint32_t source{}, target{}, carrier{}, weapon{}, ammo{};
    bool identitiesVerified{}, pathVerified{};
};

struct RegionEvidence {
    nvo::model::Region hitData{nvo::model::Region::Unknown};
    nvo::model::Region collision{nvo::model::Region::Unknown};
    bool hitDataVerified{}, collisionVerified{};
};

struct ModeEvidence {
    nvo::model::Mode value{nvo::model::Mode::Unknown};
    bool verified{};
};

struct SpeedEvidence {
    Shape shape{Shape::Missing};
    nvo::model::Measurement exact, low, high;
    bool contactVerified{}, producerVerified{}, unitsCalibrated{};
};

struct KineticProfile {
    std::uint64_t identity{};
    nvo::model::Construction construction{nvo::model::Construction::Unknown};
    nvo::model::Measurement mass, diameter;
    bool exactMapping{}, woundPayload{};
};

struct ArmourEvidence {
    // All evidence flags are required. Empty layers mean bare only when verified.
    bool enumerationComplete{}, regionCoverageComplete{};
    LayerOrder order{LayerOrder::Unknown};
    bool impactSnapshotVerified{}, bareRegionVerified{};
    std::vector<nvo::model::Layer> layers;
};

struct Input {
    IdentityEvidence identity;
    RegionEvidence region;
    ModeEvidence mode;
    bool modifierOwnershipVerified{};
    nvo::model::Family family{nvo::model::Family::Unsupported};
    KineticProfile kinetic;
    SpeedEvidence speed;
    ArmourEvidence armour;
    nvo::model::TargetProfile target;
};

struct Result {
    Status status{Status::WaitingForEvidence};
    Reason reason{Reason::Identity};
    nvo::model::Reason modelReason{nvo::model::Reason::None};
    nvo::model::Region resolvedRegion{nvo::model::Region::Unknown};
    nvo::model::Preview preview;
    static constexpr bool gameplayWrites = false;
};

Result Evaluate(const Input&);
const char* StatusName(Status) noexcept;
const char* ReasonName(Reason) noexcept;
}

#pragma once
#include "ResponseDefinitions.hpp"
#include "ShadowAdapter.hpp"
#include "ImpactBinding.hpp"

// Packet 4G. Original offline model bridge. No engine functions or apply API.
namespace nvo::materials {
inline constexpr bool kGameplayWrites = false;
inline constexpr bool kRuntimeIntegrated = false;
inline constexpr unsigned kContractVersion = 2;
struct CurvePoint { double condition{model::unknown}, scale{model::unknown}; };
struct SurfaceRule {
    std::string definition;
    responses::Provenance provenance{responses::Provenance::Unresolved};
    responses::ConditionLaw condition{responses::ConditionLaw::Unresolved};
    // AuthoredCurve requires 2..8 ordered points spanning [0,1], nondecreasing
    // scale in [0,1], scale(1)=1. Independent requires an empty curve.
    std::vector<CurvePoint> curve;
    std::array<double, 4> stoppingJ{{model::unknown, model::unknown, model::unknown, model::unknown}};
    double transmittedFraction{model::unknown}, lossPerStoppedJ{model::unknown};
};
struct TissueRule {
    std::string definition;
    responses::Provenance provenance{responses::Provenance::Unresolved};
    responses::TissueKind tissue{responses::TissueKind::Unresolved};
    double coupling{model::unknown}, directHpPerJ{model::unknown}, transmittedHpPerJ{model::unknown};
    double regionalLossPerHp{model::unknown};
};
struct NumericProfiles { std::vector<SurfaceRule> surfaces; std::vector<TissueRule> tissues; };
enum class Contact { Unknown, Miss, Hit };
struct SurfaceState {
    std::uint64_t key{}; // instance token within the bound capture only, not a persistent item ID
    std::string profile;
    responses::SurfaceKind kind{responses::SurfaceKind::Unresolved};
    Contact contact{Contact::Unknown};
    double condition{model::unknown};
    bool bindingVerified{}, conditionVerified{};
};
struct Snapshot {
    bool wornComplete{}, naturalComplete{}, coverageComplete{}, atImpactVerified{}, bareVerified{};
    shadow::LayerOrder order{shadow::LayerOrder::Unknown};
    // Complete worn and mapped natural set. Only Hit rows enter arithmetic;
    // their order must be independently verified, not inventory traversal order.
    std::vector<SurfaceState> surfaces;
};
struct RegionEvidence {
    int hitData{-1}, collision{-1}; // actual engine IDs, never cast to model::Region
    bool hitDataVerified{}, collisionVerified{};
};
struct Input {
    shadow::IdentityEvidence identity;
    shadow::ModeEvidence mode;
    RegionEvidence region;
    bool modifierOwnershipVerified{}, targetBindingVerified{};
    std::string targetProfile;
    responses::Family family{responses::Family::Unknown};
    responses::Delivery delivery{responses::Delivery::Unknown};
    shadow::KineticProfile kinetic;
    shadow::SpeedEvidence speed;
    Snapshot snapshot;
    binding::Evidence binding;
};
enum class Status { PreviewOnly, WaitingForEvidence, Unsupported, InvalidInput };
enum class Reason {
    None, Family, Delivery, Evidence, Region, ModifierOwnership, TargetBinding,
    Definitions, Snapshot, SurfaceIdentity, SurfaceBinding, SurfaceSet, Contact,
    Condition, NumericProfiles, NumericBinding, Arithmetic, ImpactBinding
};
struct SurfaceChange {
    std::uint64_t key{};
    responses::SurfaceKind kind{responses::SurfaceKind::Unresolved};
    std::uint32_t target{};
    int engineRegion{-1};
    std::string profile, definition;
    responses::Provenance provenance{responses::Provenance::Unresolved};
    // Exactly one owner channel is populated. Natural/structure loss is NOT
    // worn-item condition, nor extra actor health loss.
    double wornConditionLoss{}, naturalStructureLoss{}, mechanicalStructureLoss{};
};
struct Result {
    Status status{Status::WaitingForEvidence}; Reason reason{Reason::Evidence};
    shadow::Reason evidenceReason{shadow::Reason::None};
    responses::Reason definitionReason{responses::Reason::None};
    model::Reason modelReason{model::Reason::None};
    binding::Reason bindingReason{binding::Reason::None};
    binding::Stamp impactScope; // scopes every returned instance token; not serialization identity
    shadow::IdentityEvidence identity;
    model::Mode mode{model::Mode::Unknown};
    int engineRegion{-1};
    responses::Plan definitions;
    model::KineticBudget energy;
    std::vector<SurfaceChange> surfaces;
    double biologicalHp{}, biologicalRegionalLoss{}, mechanicalHp{}, mechanicalRegionalLoss{};
    bool protectionPenetrated{}, biologicalWoundEligible{}, payloadEligible{};
    // No force/impulse/stagger output. Transmitted J is not an impulse.
};
Result Evaluate(const responses::Catalogue&, const NumericProfiles&, const Input&);
} // namespace nvo::materials

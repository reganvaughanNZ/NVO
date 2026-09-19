#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <vector>

// Packet 4F: offline definition selection, NOT an impact/damage resolver.
// No engine dependencies, numeric damage output, callbacks, or application API.
namespace nvo::responses {
inline constexpr bool kRuntimeIntegrated = false;
inline constexpr bool kGameplayWrites = false;
inline constexpr unsigned kContractVersion = 1;

enum class Family : unsigned {
    Ballistic, Piercing, Cutting, Blunt, Blast, Laser, Plasma, Flame,
    ExternalHeat, Electrical, EMP, Count, Unknown = 255
};
inline constexpr std::size_t kFamilyCount = static_cast<unsigned>(Family::Count);
enum class Delivery : unsigned {
    Projectile, Pellet, Fragment, Melee, Thrown, Explosion, Pulse, Continuous,
    Count, Unknown = 255
};
// Only ContactJoules names a physical energy unit; it proves no measurement.
// All Exposure entries are
// distinct authored quantities with definitions/calibration still required.
enum class Quantity {
    ContactJoules, PiercingExposure, CuttingExposure, BluntExposure,
    BlastExposure, LaserExposure, PlasmaExposure, ThermalExposure,
    ElectricalExposure, EMPExposure
};
enum class TimeBasis { Unresolved, Contact, Pulse, ExposureInterval };
enum class Domain { Unresolved, Surface, Tissue };
enum class SurfaceKind { Unresolved, WornItem, NaturalProtection, MechanicalStructure };
enum class TissueKind { Unresolved, Biological, Mechanical };
enum class EquipmentPolicy { Unresolved, WornAllowed, NoWornEquipment };
enum class ConditionLaw { Unresolved, NotApplicable, AuthoredCurve, ExplicitlyIndependent };
enum class Provenance { Unresolved, SyntheticFixture, ProvisionalGameplay, ReviewedGameplay };

struct FamilyContract {
    const char* name;
    Quantity quantity;
    std::uint32_t deliveries;
    const char* requiredEvidence;
};
const FamilyContract* Describe(Family family);
bool Allows(Family family, Delivery delivery);
TimeBasis Timing(Family family, Delivery delivery);

// IDs reference future response implementations/tuning. No coefficients or
// calculators are implied by a definition, even with ReviewedGameplay provenance.
struct Definition {
    std::string id;
    Domain domain = Domain::Unresolved;
    Family family = Family::Unknown;
    ConditionLaw condition = ConditionLaw::Unresolved;
    Provenance provenance = Provenance::Unresolved;
    TissueKind tissue = TissueKind::Unresolved; // required only for tissue definitions
};
using Bindings = std::array<std::string, kFamilyCount>; // empty = unresolved, NEVER zero
struct SurfaceProfile {
    std::string id;
    SurfaceKind kind = SurfaceKind::Unresolved;
    std::string construction; // e.g. plate + backing; material name alone is insufficient
    Bindings responses;
};
struct RegionProfile {
    int engineRegion = -1; // exact authored mapping, not a forced humanoid enum
    std::string location;
    TissueKind tissue = TissueKind::Unresolved;
    bool naturalSetKnown = false; // empty without this flag is unresolved, not bare
    std::vector<std::string> naturalSurfaces;
    Bindings responses;
};
struct TargetProfile {
    std::string id;
    EquipmentPolicy equipment = EquipmentPolicy::Unresolved;
    std::vector<RegionProfile> regions;
};
struct Catalogue {
    std::vector<Definition> definitions;
    std::vector<SurfaceProfile> surfaces;
    std::vector<TargetProfile> targets;
};
enum class Status { DefinitionsOnly, WaitingForDefinition, Unsupported, InvalidDefinition };
enum class Reason {
    None, Bounds, Identifier, Duplicate, Domain, Family, Condition, Provenance,
    MissingReference, BindingMismatch, SurfaceKind, Region, Tissue,
    EquipmentPolicy, NaturalSurface, Delivery, TargetMissing, RegionMissing,
    EquipmentUnknown, WornSurface, ResponseMissing, NaturalSetUnknown
};
struct Check {
    bool valid = false;
    Reason reason = Reason::None;
};
Check Validate(const Catalogue& catalogue);

// This query has no hit/actor identity or measured contact data. It cannot prove
// actual coverage, layers, snapshot timing, penetration, or a resolved hit.
struct Query {
    Family family = Family::Unknown;
    Delivery delivery = Delivery::Unknown;
    std::string target;
    int engineRegion = -1;
    bool wornSetKnown = false;
    std::vector<std::string> wornProfiles; // unordered unique surface-profile IDs, NOT item instances
};
struct SurfaceBinding {
    std::string profile;
    SurfaceKind kind = SurfaceKind::Unresolved;
    std::string response;
    ConditionLaw condition = ConditionLaw::Unresolved;
    Provenance provenance = Provenance::Unresolved;
};
struct Plan {
    Status status = Status::WaitingForDefinition;
    Reason reason = Reason::None;
    std::string target;
    std::string location;
    TissueKind tissue = TissueKind::Unresolved;
    std::string tissueResponse;
    Provenance tissueProvenance = Provenance::Unresolved;
    std::vector<SurfaceBinding> surfaces; // NOT outer-to-inner layer order
    // Deliberately no HP/limb/wear/stagger numbers or effect-eligibility flags.
};
Plan Select(const Catalogue& catalogue, const Query& query);
} // namespace nvo::responses

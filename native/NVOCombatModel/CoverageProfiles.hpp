#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

// Pure authored coverage classification, not a damage adapter.
namespace nvo::coverage {
inline constexpr bool kGameplayWrites = false;
inline constexpr bool kRuntimeIntegrated = true; // 4D diagnostics only when its DLL is installed.
inline constexpr bool kEngineMemoryAccess = false;
inline constexpr std::size_t kRegions = 6, kMaxItems = 32, kMaxProfiles = 256;
// Semantic regions. Never cast a raw engine region or biped bit into this enum.
enum class Region { Head, Torso, LeftArm, RightArm, LeftLeg, RightLeg };
enum class Extent { None, Partial, Full, Unknown };
enum class Target { EquipmentCharacter, Creature, Unknown };
enum class Status { ClassifiedOnly, WaitingForEvidence, Unsupported, InvalidInput };
enum class Reason {
    None, TargetUnknown, CreatureProfileRequired, SnapshotIncomplete,
    InvalidCatalog, InvalidItem, DuplicateInstance, OriginUnresolved,
    UnknownEquipment, RecordMismatch
};
struct FormKey {
    std::string_view plugin;
    std::uint32_t localId{}; // Owning plugin + local ID, NOT runtime/load-index ID.
};
struct Profile {
    FormKey key;
    std::uint32_t revision{};
    std::uint32_t expectedEquipMask{}; // Drift guard only. Does not generate coverage.
    std::array<Extent, kRegions> regions{};
};
struct Item {
    std::uint64_t instance{}; // Valid only within the supplied snapshot.
    FormKey key;
    bool originResolved{};
    std::uint32_t observedEquipMask{};
    double condition{};
};
struct Input {
    Target target{Target::Unknown};
    bool enumerationComplete{}, stableDoubleRead{};
    std::size_t count{};
    std::array<Item, kMaxItems> items{};
};
struct ClassifiedItem {
    std::uint64_t instance{};
    FormKey key;
    std::uint32_t profileRevision{};
    double condition{};
    std::array<Extent, kRegions> regions{};
};
struct RegionSummary {
    unsigned full{}, partial{}, unknown{};
    // Counts describe authored potential coverage, never material strength,
    // layer order, an exact surface strike, or verified bare anatomy.
};
struct Result {
    Status status{Status::WaitingForEvidence};
    Reason reason{Reason::TargetUnknown};
    std::size_t count{};
    std::array<ClassifiedItem, kMaxItems> items{};
    std::array<RegionSummary, kRegions> regions{};
    static constexpr bool gameplayWrites = false;
    static constexpr bool regionCoverageAuthority = false;
    static constexpr bool impactSnapshotAuthority = false;
    static constexpr bool layerOrderVerified = false;
    static constexpr bool bareRegionVerified = false;
    static constexpr bool armourPreview = false;
};
// Strings and arrays must be valid C++ memory for the duration of this pure call.
// Output string_views borrow catalog keys. No engine memory is accepted or retained.
bool ValidKey(const FormKey&) noexcept;
bool SameKey(const FormKey&, const FormKey&) noexcept;
bool ValidCatalog(const std::vector<Profile>&) noexcept;
class PreparedCatalog {
public:
    // Validate once at session activation; borrowed key strings must outlive use.
    bool Prepare(const Profile*, std::size_t) noexcept;
    void Reset() noexcept { valid_ = false; count_ = 0; }
    bool Valid() const noexcept { return valid_; }
    std::size_t Count() const noexcept { return count_; }
private:
    bool valid_{};
    std::size_t count_{};
    std::array<Profile, kMaxProfiles> profiles_{};
    friend Result Classify(const Input&, const PreparedCatalog&) noexcept;
};
Result Classify(const Input&, const PreparedCatalog&) noexcept;
Result Classify(const Input&, const std::vector<Profile>&) noexcept;
const char* ReasonName(Reason) noexcept;
}

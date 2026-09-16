#pragma once
#include <cstddef>
#include <cstdint>

namespace nvo::armour::reader {

constexpr unsigned kMaxActorExtras = 64;
constexpr unsigned kMaxEntryNodes = 512;
constexpr unsigned kMaxInstanceNodes = 1024;
constexpr unsigned kMaxInstanceExtras = 64;
constexpr unsigned kMaxTotalInstanceExtras = 8192;
constexpr unsigned kMaxEquippedArmour = 32;
constexpr std::uint32_t kKnownBipedMask = 0x000FFFFFu;

// Read must copy exactly size bytes or return false. It must never write to
// source memory or call an engine helper.
struct Memory {
    void* context{};
    bool (*read)(void* context, const void* source, void* destination,
        std::size_t size) noexcept{};
};

enum class Code : std::uint8_t {
    CompleteWithArmour,
    CompleteNoArmourObserved,
    InvalidArgument,
    UnsupportedTarget,
    ReadFailure,
    InvalidPointer,
    MissingContainerChanges,
    DuplicateContainerChanges,
    PresenceMismatch,
    OwnerMismatch,
    NullObjectList,
    CycleOrAlias,
    TraversalLimit,
    DuplicateWorn,
    DuplicateHealth,
    UnsupportedWornForm,
    InvalidArmourRecord,
    InvalidCondition,
    Unstable
};

struct Item {
    std::uint64_t instanceToken{}; // Scalar identity for this call only.
    std::uint32_t formId{};
    std::uint32_t partMask{};
    std::uint32_t baseHealth{};
    float currentHealth{};
    float conditionRatio{};
    float damageThreshold{};
    std::uint16_t armourRating{};
    std::uint32_t bipedFlags{};
    std::uint8_t armourFlags{};
    bool explicitHealth{};
};

struct Snapshot {
    Code code{Code::InvalidArgument};
    std::uint32_t targetId{};
    unsigned entriesVisited{};
    unsigned instancesVisited{};
    unsigned extrasVisited{};
    unsigned itemCount{};
    Item items[kMaxEquippedArmour]{};
    bool enumerationComplete{};
    bool stableDoubleRead{};

    // Step 4B deliberately cannot prove any of these Step 4A gates.
    bool regionCoverageComplete{};
    bool layerOrderVerified{};
    bool impactSnapshotVerified{};
    bool bareRegionVerified{};
};

constexpr bool kGameplayWrites = false;
constexpr bool kSnapshotAuthority = false;
constexpr bool kCallsShadowAdapter = false;

// Two complete, bit-identical traversals are required for success. A stable
// result is still bounded consistency evidence, not atomic impact authority.
Snapshot CaptureStable(const Memory& memory, const void* target,
    std::uint32_t expectedTargetId) noexcept;
const char* Name(Code code) noexcept;
bool Complete(Code code) noexcept;

} // namespace nvo::armour::reader

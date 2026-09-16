#include "ArmourSnapshotReader.hpp"
#include <cmath>
#include <cstring>
#include <limits>

namespace {
using nvo::armour::reader::Code;
using nvo::armour::reader::Item;
using nvo::armour::reader::Memory;
using nvo::armour::reader::Snapshot;
using U8 = std::uint8_t;
using U16 = std::uint16_t;
using U32 = std::uint32_t;
using U64 = std::uint64_t;

constexpr U8 kCharacter = 0x3B;
constexpr U8 kArmour = 0x18;
constexpr U8 kWeapon = 0x28;
constexpr U8 kContainerChanges = 0x15;
constexpr U8 kWorn = 0x16;
constexpr U8 kWornLeft = 0x17;
constexpr U8 kHealth = 0x25;
constexpr std::size_t kReferenceExtraList = 0x44;
constexpr std::size_t kContainerData = 0x0C;
constexpr std::size_t kArmourBaseHealth = 0x6C;
constexpr std::size_t kArmourPartMask = 0x74;
constexpr std::size_t kArmourBipedFlags = 0x78;
constexpr std::size_t kArmourRating = 0x178;
constexpr std::size_t kArmourThreshold = 0x17C;
constexpr std::size_t kArmourFlags = 0x180;

static_assert(sizeof(void*) == 4, "The Fallout New Vegas reader must be built x86.");

struct FormHeader {
    void* vtable;
    U8 type;
    U8 pad05[3];
    U32 flags;
    U32 id;
};
struct ExtraListHeader {
    void* vtable;
    void* head;
    U8 presence[0x13];
    U8 afterPresence;
};
struct ExtraNode {
    void* vtable;
    U8 type;
    U8 pad05[3];
    void* next;
};
struct ContainerView { void* objectList; void* owner; };
struct ListNode { void* data; void* next; };
struct EntryView { void* extendData; std::int32_t countDelta; void* form; };

static_assert(sizeof(FormHeader) == 0x10);
static_assert(sizeof(ExtraListHeader) == 0x1C);
static_assert(sizeof(ExtraNode) == 0x0C);
static_assert(sizeof(ContainerView) == 0x08);
static_assert(sizeof(ListNode) == 0x08);
static_assert(sizeof(EntryView) == 0x0C);

bool IsPointer(const void* value) noexcept
{
    const auto address = reinterpret_cast<std::uintptr_t>(value);
    return address >= 0x10000u && (address & 3u) == 0;
}

const void* At(const void* base, std::size_t offset) noexcept
{
    const auto address = reinterpret_cast<std::uintptr_t>(base);
    if (!address || offset > (std::numeric_limits<std::uintptr_t>::max)() - address)
        return nullptr;
    return reinterpret_cast<const void*>(address + offset);
}

template <class T>
bool Read(const Memory& memory, const void* source, T& value) noexcept
{
    value = {};
    return memory.read && source && memory.read(memory.context, source, &value, sizeof(value));
}

template <class T>
bool ReadAt(const Memory& memory, const void* source, std::size_t offset, T& value) noexcept
{
    const void* address = At(source, offset);
    return address && Read(memory, address, value);
}

bool Present(const ExtraListHeader& list, U8 type) noexcept
{
    return (list.presence[type >> 3] & static_cast<U8>(1u << (type & 7))) != 0;
}

enum class InsertResult : U8 { Inserted, Duplicate, ProbeLimit };

// Fixed storage and a strict probe budget keep corrupted graphs from turning
// synchronous hit observation into an unbounded quadratic scan.
template <unsigned N>
struct PointerSet {
    static_assert(N && (N & (N - 1)) == 0, "Pointer-set size must be a power of two.");
    static constexpr unsigned kProbeLimit = 64;
    static constexpr unsigned kSlotCount = N * 2;
    const void* slots[kSlotCount]{};
    unsigned count{};

    InsertResult Insert(const void* value) noexcept
    {
        U32 hash = static_cast<U32>(reinterpret_cast<std::uintptr_t>(value) >> 2);
        hash ^= hash >> 16;
        hash *= 0x7FEB352Du;
        hash ^= hash >> 15;
        hash *= 0x846CA68Bu;
        hash ^= hash >> 16;
        if (count == N) return InsertResult::ProbeLimit;
        const unsigned start = hash & (kSlotCount - 1);
        const unsigned limit = kSlotCount < kProbeLimit ? kSlotCount : kProbeLimit;
        for (unsigned probe = 0; probe < limit; ++probe) {
            const unsigned index = (start + probe) & (kSlotCount - 1);
            if (slots[index] == value) return InsertResult::Duplicate;
            if (!slots[index]) {
                slots[index] = value;
                ++count;
                return InsertResult::Inserted;
            }
        }
        return InsertResult::ProbeLimit;
    }
};

Snapshot Failure(Code code, U32 target, unsigned entries = 0,
    unsigned instances = 0, unsigned extras = 0) noexcept
{
    Snapshot result{};
    result.code = code;
    result.targetId = target;
    result.entriesVisited = entries;
    result.instancesVisited = instances;
    result.extrasVisited = extras;
    return result;
}

bool SameBytes(const void* left, const void* right, std::size_t size) noexcept
{
    return std::memcmp(left, right, size) == 0;
}

struct InstanceScan {
    Code code{Code::ReadFailure};
    bool ok{};
    bool worn{};
    bool wornLeft{};
    bool explicitHealth{};
    float currentHealth{};
    unsigned extras{};
};

InstanceScan ScanInstance(const Memory& memory, const void* instance,
    PointerSet<nvo::armour::reader::kMaxTotalInstanceExtras>& allExtras,
    unsigned& totalExtras) noexcept
{
    InstanceScan result{};
    if (!IsPointer(instance)) { result.code = Code::InvalidPointer; return result; }
    ExtraListHeader before{};
    if (!Read(memory, instance, before)) return result;
    if (!IsPointer(before.vtable)) { result.code = Code::InvalidPointer; return result; }

    unsigned seenCount{}, wornCount{}, wornLeftCount{}, healthCount{};
    const void* healthNode{};
    const void* node = before.head;
    while (node && seenCount < nvo::armour::reader::kMaxInstanceExtras) {
        if (!IsPointer(node)) { result.code = Code::InvalidPointer; return result; }
        if (totalExtras == nvo::armour::reader::kMaxTotalInstanceExtras) {
            result.code = Code::TraversalLimit; return result;
        }
        const auto inserted = allExtras.Insert(node);
        if (inserted == InsertResult::Duplicate) {
            result.code = Code::CycleOrAlias; return result;
        }
        if (inserted != InsertResult::Inserted) {
            result.code = Code::TraversalLimit; return result;
        }
        ++seenCount;
        ++totalExtras;
        ExtraNode extra{};
        if (!Read(memory, node, extra)) return result;
        if (!IsPointer(extra.vtable)) { result.code = Code::InvalidPointer; return result; }
        if (extra.type == kWorn) ++wornCount;
        else if (extra.type == kWornLeft) ++wornLeftCount;
        else if (extra.type == kHealth) { ++healthCount; healthNode = node; }
        node = extra.next;
    }
    if (node) { result.code = Code::TraversalLimit; return result; }
    if (wornCount > 1) { result.code = Code::DuplicateWorn; return result; }
    if (wornLeftCount > 1) { result.code = Code::DuplicateWorn; return result; }
    if (healthCount > 1) { result.code = Code::DuplicateHealth; return result; }
    if (Present(before, kWorn) != (wornCount == 1)
        || Present(before, kWornLeft) != (wornLeftCount == 1)
        || Present(before, kHealth) != (healthCount == 1)) {
        result.code = Code::PresenceMismatch; return result;
    }
    if (healthNode && !ReadAt(memory, healthNode, 0x0C, result.currentHealth))
        return result;

    ExtraListHeader after{};
    if (!Read(memory, instance, after)) return result;
    if (!SameBytes(&before, &after, sizeof(before))) {
        result.code = Code::Unstable; return result;
    }
    result.code = Code::CompleteNoArmourObserved;
    result.ok = true;
    result.worn = wornCount == 1;
    result.wornLeft = wornLeftCount == 1;
    result.explicitHealth = healthCount == 1;
    result.extras = seenCount;
    return result;
}

bool ReadForm(const Memory& memory, const void* form, FormHeader& result) noexcept
{
    return IsPointer(form) && Read(memory, form, result) && IsPointer(result.vtable)
        && result.id != 0;
}

Snapshot CaptureOnce(const Memory& memory, const void* target, U32 expectedTarget) noexcept
{
    if (!memory.read || !target || !expectedTarget)
        return Failure(Code::InvalidArgument, expectedTarget);
    if (!IsPointer(target)) return Failure(Code::InvalidPointer, expectedTarget);

    FormHeader targetBefore{};
    if (!ReadForm(memory, target, targetBefore))
        return Failure(Code::ReadFailure, expectedTarget);
    if (targetBefore.type != kCharacter || targetBefore.id != expectedTarget)
        return Failure(Code::UnsupportedTarget, expectedTarget);

    ExtraListHeader actorListBefore{};
    if (!ReadAt(memory, target, kReferenceExtraList, actorListBefore))
        return Failure(Code::ReadFailure, expectedTarget);
    if (!IsPointer(actorListBefore.vtable))
        return Failure(Code::InvalidPointer, expectedTarget);

    PointerSet<nvo::armour::reader::kMaxActorExtras> actorExtraSeen{};
    unsigned containerCount{};
    const void* containerNode{};
    const void* extra = actorListBefore.head;
    while (extra && actorExtraSeen.count < nvo::armour::reader::kMaxActorExtras) {
        if (!IsPointer(extra)) return Failure(Code::InvalidPointer, expectedTarget);
        const auto inserted = actorExtraSeen.Insert(extra);
        if (inserted == InsertResult::Duplicate)
            return Failure(Code::CycleOrAlias, expectedTarget);
        if (inserted != InsertResult::Inserted)
            return Failure(Code::TraversalLimit, expectedTarget);
        ExtraNode node{};
        if (!Read(memory, extra, node)) return Failure(Code::ReadFailure, expectedTarget);
        if (!IsPointer(node.vtable)) return Failure(Code::InvalidPointer, expectedTarget);
        if (node.type == kContainerChanges) { ++containerCount; containerNode = extra; }
        extra = node.next;
    }
    if (extra) return Failure(Code::TraversalLimit, expectedTarget);
    const bool containerPresent = Present(actorListBefore, kContainerChanges);
    if (containerPresent != (containerCount != 0))
        return Failure(Code::PresenceMismatch, expectedTarget);
    if (!containerCount) return Failure(Code::MissingContainerChanges, expectedTarget);
    if (containerCount != 1) return Failure(Code::DuplicateContainerChanges, expectedTarget);

    void* containerData{};
    if (!ReadAt(memory, containerNode, kContainerData, containerData))
        return Failure(Code::ReadFailure, expectedTarget);
    if (!IsPointer(containerData)) return Failure(Code::InvalidPointer, expectedTarget);
    ContainerView containerBefore{};
    if (!Read(memory, containerData, containerBefore))
        return Failure(Code::ReadFailure, expectedTarget);
    if (containerBefore.owner != target) return Failure(Code::OwnerMismatch, expectedTarget);
    if (!IsPointer(containerBefore.objectList))
        return Failure(Code::NullObjectList, expectedTarget);

    Snapshot result{};
    result.targetId = expectedTarget;
    PointerSet<nvo::armour::reader::kMaxEntryNodes> entryNodeSeen{};
    PointerSet<nvo::armour::reader::kMaxEntryNodes> entryDataSeen{};
    PointerSet<nvo::armour::reader::kMaxInstanceNodes> instanceNodeSeen{};
    PointerSet<nvo::armour::reader::kMaxInstanceNodes> instanceSeen{};
    PointerSet<nvo::armour::reader::kMaxTotalInstanceExtras> allExtras{};
    unsigned totalExtras{};
    const void* entryNode = containerBefore.objectList;
    while (entryNode && entryNodeSeen.count < nvo::armour::reader::kMaxEntryNodes) {
        if (!IsPointer(entryNode))
            return Failure(Code::InvalidPointer, expectedTarget, result.entriesVisited,
                result.instancesVisited, totalExtras);
        const auto entryNodeInserted = entryNodeSeen.Insert(entryNode);
        if (entryNodeInserted == InsertResult::Duplicate)
            return Failure(Code::CycleOrAlias, expectedTarget, result.entriesVisited,
                result.instancesVisited, totalExtras);
        if (entryNodeInserted != InsertResult::Inserted)
            return Failure(Code::TraversalLimit, expectedTarget, result.entriesVisited,
                result.instancesVisited, totalExtras);
        ListNode list{};
        if (!Read(memory, entryNode, list))
            return Failure(Code::ReadFailure, expectedTarget, result.entriesVisited,
                result.instancesVisited, totalExtras);
        if (list.data) {
            if (!IsPointer(list.data))
                return Failure(Code::InvalidPointer, expectedTarget, result.entriesVisited,
                    result.instancesVisited, totalExtras);
            const auto entryDataInserted = entryDataSeen.Insert(list.data);
            if (entryDataInserted == InsertResult::Duplicate)
                return Failure(Code::CycleOrAlias, expectedTarget, result.entriesVisited,
                    result.instancesVisited, totalExtras);
            if (entryDataInserted != InsertResult::Inserted)
                return Failure(Code::TraversalLimit, expectedTarget, result.entriesVisited,
                    result.instancesVisited, totalExtras);
            EntryView entry{};
            if (!Read(memory, list.data, entry))
                return Failure(Code::ReadFailure, expectedTarget, result.entriesVisited,
                    result.instancesVisited, totalExtras);
            FormHeader form{};
            if (!ReadForm(memory, entry.form, form))
                return Failure(Code::ReadFailure, expectedTarget, result.entriesVisited,
                    result.instancesVisited, totalExtras);
            ++result.entriesVisited;
            if (entry.extendData) {
                if (!IsPointer(entry.extendData))
                    return Failure(Code::InvalidPointer, expectedTarget, result.entriesVisited,
                        result.instancesVisited, totalExtras);
                const void* instanceNode = entry.extendData;
                while (instanceNode
                    && instanceNodeSeen.count < nvo::armour::reader::kMaxInstanceNodes) {
                    if (!IsPointer(instanceNode))
                        return Failure(Code::InvalidPointer, expectedTarget, result.entriesVisited,
                            result.instancesVisited, totalExtras);
                    const auto instanceNodeInserted = instanceNodeSeen.Insert(instanceNode);
                    if (instanceNodeInserted == InsertResult::Duplicate)
                        return Failure(Code::CycleOrAlias, expectedTarget, result.entriesVisited,
                            result.instancesVisited, totalExtras);
                    if (instanceNodeInserted != InsertResult::Inserted)
                        return Failure(Code::TraversalLimit, expectedTarget, result.entriesVisited,
                            result.instancesVisited, totalExtras);
                    ListNode instanceList{};
                    if (!Read(memory, instanceNode, instanceList))
                        return Failure(Code::ReadFailure, expectedTarget, result.entriesVisited,
                            result.instancesVisited, totalExtras);
                    if (instanceList.data) {
                        if (!IsPointer(instanceList.data))
                            return Failure(Code::InvalidPointer, expectedTarget,
                                result.entriesVisited, result.instancesVisited, totalExtras);
                        const auto instanceInserted = instanceSeen.Insert(instanceList.data);
                        if (instanceInserted == InsertResult::Duplicate)
                            return Failure(Code::CycleOrAlias, expectedTarget,
                                result.entriesVisited, result.instancesVisited, totalExtras);
                        if (instanceInserted != InsertResult::Inserted)
                            return Failure(Code::TraversalLimit, expectedTarget,
                                result.entriesVisited, result.instancesVisited, totalExtras);
                        ++result.instancesVisited;
                        const auto scan = ScanInstance(
                            memory, instanceList.data, allExtras, totalExtras);
                        if (!scan.ok)
                            return Failure(scan.code, expectedTarget, result.entriesVisited,
                                result.instancesVisited, totalExtras);
                        if (scan.worn || scan.wornLeft) {
                            if (form.type == kWeapon) {
                                // A verified weapon is equipped but is not armour.
                            } else if (form.type != kArmour || scan.wornLeft) {
                                return Failure(Code::UnsupportedWornForm, expectedTarget,
                                    result.entriesVisited, result.instancesVisited, totalExtras);
                            } else {
                                if (result.itemCount == nvo::armour::reader::kMaxEquippedArmour)
                                    return Failure(Code::TraversalLimit, expectedTarget,
                                        result.entriesVisited, result.instancesVisited, totalExtras);
                                Item item{};
                                item.instanceToken = (static_cast<U64>(expectedTarget) << 32)
                                    | static_cast<U32>(reinterpret_cast<std::uintptr_t>(instanceList.data));
                                item.formId = form.id;
                                if (!ReadAt(memory, entry.form, kArmourBaseHealth, item.baseHealth)
                                    || !ReadAt(memory, entry.form, kArmourPartMask, item.partMask)
                                    || !ReadAt(memory, entry.form, kArmourBipedFlags, item.bipedFlags)
                                    || !ReadAt(memory, entry.form, kArmourRating, item.armourRating)
                                    || !ReadAt(memory, entry.form, kArmourThreshold, item.damageThreshold)
                                    || !ReadAt(memory, entry.form, kArmourFlags, item.armourFlags))
                                    return Failure(Code::ReadFailure, expectedTarget,
                                        result.entriesVisited, result.instancesVisited, totalExtras);
                                if ((item.partMask & ~nvo::armour::reader::kKnownBipedMask) != 0
                                    || !std::isfinite(item.damageThreshold)
                                    || item.damageThreshold < 0.0f || !item.baseHealth)
                                    return Failure(Code::InvalidArmourRecord, expectedTarget,
                                        result.entriesVisited, result.instancesVisited, totalExtras);
                                item.explicitHealth = scan.explicitHealth;
                                item.currentHealth = scan.explicitHealth
                                    ? scan.currentHealth : static_cast<float>(item.baseHealth);
                                const float maximum = static_cast<float>(item.baseHealth);
                                if (!std::isfinite(item.currentHealth) || item.currentHealth < 0.0f
                                    || item.currentHealth > maximum)
                                    return Failure(Code::InvalidCondition, expectedTarget,
                                        result.entriesVisited, result.instancesVisited, totalExtras);
                                item.conditionRatio = item.currentHealth / maximum;
                                if (!std::isfinite(item.conditionRatio))
                                    return Failure(Code::InvalidCondition, expectedTarget,
                                        result.entriesVisited, result.instancesVisited, totalExtras);
                                result.items[result.itemCount++] = item;
                            }
                        }
                    }
                    instanceNode = instanceList.next;
                }
                if (instanceNode)
                    return Failure(Code::TraversalLimit, expectedTarget, result.entriesVisited,
                        result.instancesVisited, totalExtras);
            }
        }
        entryNode = list.next;
    }
    if (entryNode)
        return Failure(Code::TraversalLimit, expectedTarget, result.entriesVisited,
            result.instancesVisited, totalExtras);

    FormHeader targetAfter{};
    ExtraListHeader actorListAfter{};
    void* containerDataAfter{};
    ContainerView containerAfter{};
    if (!ReadForm(memory, target, targetAfter)
        || !ReadAt(memory, target, kReferenceExtraList, actorListAfter)
        || !ReadAt(memory, containerNode, kContainerData, containerDataAfter)
        || !Read(memory, containerData, containerAfter))
        return Failure(Code::ReadFailure, expectedTarget, result.entriesVisited,
            result.instancesVisited, totalExtras);
    if (!SameBytes(&targetBefore, &targetAfter, sizeof(targetBefore))
        || !SameBytes(&actorListBefore, &actorListAfter, sizeof(actorListBefore))
        || containerDataAfter != containerData
        || !SameBytes(&containerBefore, &containerAfter, sizeof(containerBefore)))
        return Failure(Code::Unstable, expectedTarget, result.entriesVisited,
            result.instancesVisited, totalExtras);

    result.extrasVisited = totalExtras;
    result.enumerationComplete = true;
    result.code = result.itemCount ? Code::CompleteWithArmour
                                   : Code::CompleteNoArmourObserved;
    return result;
}

bool SameItem(const Item& a, const Item& b) noexcept
{
    return a.instanceToken == b.instanceToken && a.formId == b.formId
        && a.partMask == b.partMask && a.baseHealth == b.baseHealth
        && SameBytes(&a.currentHealth, &b.currentHealth, sizeof(float))
        && SameBytes(&a.conditionRatio, &b.conditionRatio, sizeof(float))
        && SameBytes(&a.damageThreshold, &b.damageThreshold, sizeof(float))
        && a.armourRating == b.armourRating && a.bipedFlags == b.bipedFlags
        && a.armourFlags == b.armourFlags && a.explicitHealth == b.explicitHealth;
}

bool SameSnapshot(const Snapshot& a, const Snapshot& b) noexcept
{
    if (a.code != b.code || a.targetId != b.targetId
        || a.entriesVisited != b.entriesVisited
        || a.instancesVisited != b.instancesVisited
        || a.extrasVisited != b.extrasVisited || a.itemCount != b.itemCount
        || a.enumerationComplete != b.enumerationComplete) return false;
    for (unsigned i = 0; i < a.itemCount; ++i)
        if (!SameItem(a.items[i], b.items[i])) return false;
    return true;
}
} // namespace

nvo::armour::reader::Snapshot nvo::armour::reader::CaptureStable(
    const Memory& memory, const void* target, U32 expectedTargetId) noexcept
{
    Snapshot first = CaptureOnce(memory, target, expectedTargetId);
    if (!Complete(first.code)) return first;
    const Snapshot second = CaptureOnce(memory, target, expectedTargetId);
    if (!Complete(second.code) || !SameSnapshot(first, second))
        return Failure(Code::Unstable, expectedTargetId, first.entriesVisited,
            first.instancesVisited, first.extrasVisited);
    first.stableDoubleRead = true;
    return first;
}

bool nvo::armour::reader::Complete(Code code) noexcept
{
    return code == Code::CompleteWithArmour || code == Code::CompleteNoArmourObserved;
}

const char* nvo::armour::reader::Name(Code code) noexcept
{
    switch (code) {
    case Code::CompleteWithArmour: return "complete_with_armour";
    case Code::CompleteNoArmourObserved: return "complete_no_armour_observed";
    case Code::InvalidArgument: return "invalid_argument";
    case Code::UnsupportedTarget: return "unsupported_target";
    case Code::ReadFailure: return "guarded_read_failure";
    case Code::InvalidPointer: return "invalid_pointer";
    case Code::MissingContainerChanges: return "container_changes_unavailable";
    case Code::DuplicateContainerChanges: return "duplicate_container_changes";
    case Code::PresenceMismatch: return "presence_chain_mismatch";
    case Code::OwnerMismatch: return "container_owner_mismatch";
    case Code::NullObjectList: return "object_list_unavailable";
    case Code::CycleOrAlias: return "cycle_or_alias";
    case Code::TraversalLimit: return "traversal_limit";
    case Code::DuplicateWorn: return "duplicate_worn_marker";
    case Code::DuplicateHealth: return "duplicate_health_record";
    case Code::UnsupportedWornForm: return "unsupported_worn_form";
    case Code::InvalidArmourRecord: return "invalid_armour_record";
    case Code::InvalidCondition: return "invalid_condition";
    case Code::Unstable: return "unstable_double_read";
    }
    return "unknown";
}

static_assert(!nvo::armour::reader::kGameplayWrites);
static_assert(!nvo::armour::reader::kSnapshotAuthority);
static_assert(!nvo::armour::reader::kCallsShadowAdapter);

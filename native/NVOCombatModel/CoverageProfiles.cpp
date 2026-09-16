#include "CoverageProfiles.hpp"
#include <cmath>

namespace nvo::coverage {
namespace {
char Lower(char c) noexcept { return c >= 'A' && c <= 'Z' ? static_cast<char>(c + ('a' - 'A')) : c; }
bool Equal(std::string_view a, std::string_view b) noexcept {
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) if (Lower(a[i]) != Lower(b[i])) return false;
    return true;
}
bool Mask(std::uint32_t mask) noexcept { return mask != 0 && !(mask & ~0xFFFFFu); }
Result Reject(Status status, Reason reason) noexcept { Result r; r.status = status; r.reason = reason; return r; }
}
bool ValidKey(const FormKey& key) noexcept {
    const auto name = key.plugin;
    if (!key.localId || key.localId > 0xFFFFFFu || name.size() < 5 || name.size() > 128) return false;
    if (name.front() == ' ' || name.back() == ' ' || name.find("..") != name.npos) return false;
    for (const char c : name)
        if (c < 32 || c > 126 || std::string_view("/\\:*?\"<>|").find(c) != std::string_view::npos) return false;
    const auto suffix = name.substr(name.size() - 4);
    return Equal(suffix, ".esm") || Equal(suffix, ".esp");
}
bool SameKey(const FormKey& a, const FormKey& b) noexcept {
    return a.localId == b.localId && Equal(a.plugin, b.plugin);
}
bool PreparedCatalog::Prepare(const Profile* catalog, std::size_t count) noexcept {
    Reset();
    if (!catalog || !count || count > kMaxProfiles) return false;
    for (std::size_t i = 0; i < count; ++i) {
        const auto& p = catalog[i];
        if (!ValidKey(p.key) || !p.revision || !Mask(p.expectedEquipMask)) return false;
        for (const auto extent : p.regions)
            if (extent < Extent::None || extent > Extent::Unknown) return false;
        for (std::size_t j = 0; j < i; ++j) if (SameKey(p.key, catalog[j].key)) return false;
    }
    for (std::size_t i = 0; i < count; ++i) profiles_[i] = catalog[i];
    count_ = count;
    valid_ = true;
    return true;
}
bool ValidCatalog(const std::vector<Profile>& catalog) noexcept {
    PreparedCatalog prepared;
    return prepared.Prepare(catalog.data(), catalog.size());
}
Result Classify(const Input& input, const std::vector<Profile>& catalog) noexcept {
    PreparedCatalog prepared;
    prepared.Prepare(catalog.data(), catalog.size());
    return Classify(input, prepared);
}
Result Classify(const Input& input, const PreparedCatalog& catalog) noexcept {
    if (input.target == Target::Creature)
        return Reject(Status::Unsupported, Reason::CreatureProfileRequired);
    if (input.target != Target::EquipmentCharacter)
        return Reject(Status::WaitingForEvidence, Reason::TargetUnknown);
    if (!input.enumerationComplete || !input.stableDoubleRead)
        return Reject(Status::WaitingForEvidence, Reason::SnapshotIncomplete);
    if (!catalog.valid_) return Reject(Status::InvalidInput, Reason::InvalidCatalog);
    if (input.count > kMaxItems) return Reject(Status::InvalidInput, Reason::InvalidItem);
    Result result;
    for (std::size_t i = 0; i < input.count; ++i) {
        const auto& item = input.items[i];
        if (!item.instance || !Mask(item.observedEquipMask) || !std::isfinite(item.condition)
            || item.condition < 0 || item.condition > 1)
            return Reject(Status::InvalidInput, Reason::InvalidItem);
        for (std::size_t j = 0; j < i; ++j)
            if (item.instance == input.items[j].instance)
                return Reject(Status::InvalidInput, Reason::DuplicateInstance);
        if (!item.originResolved) return Reject(Status::WaitingForEvidence, Reason::OriginUnresolved);
        if (!ValidKey(item.key)) return Reject(Status::InvalidInput, Reason::InvalidItem);
        const Profile* profile{};
        for (std::size_t j=0; j<catalog.count_; ++j)
            if (SameKey(item.key, catalog.profiles_[j].key)) { profile=&catalog.profiles_[j]; break; }
        if (!profile) return Reject(Status::WaitingForEvidence, Reason::UnknownEquipment);
        if (item.observedEquipMask != profile->expectedEquipMask)
            return Reject(Status::WaitingForEvidence, Reason::RecordMismatch);
        auto& mapped = result.items[i];
        mapped = {item.instance, profile->key, profile->revision, item.condition, profile->regions};
        for (std::size_t r = 0; r < kRegions; ++r) {
            auto& summary = result.regions[r];
            switch (mapped.regions[r]) {
            case Extent::Full: ++summary.full; break;
            case Extent::Partial: ++summary.partial; break;
            case Extent::Unknown: ++summary.unknown; break;
            case Extent::None: break;
            }
        }
    }
    result.status = Status::ClassifiedOnly;
    result.reason = Reason::None;
    result.count = input.count;
    return result;
}
const char* ReasonName(Reason reason) noexcept {
    switch (reason) {
    case Reason::None: return "classified_only";
    case Reason::TargetUnknown: return "target_unknown";
    case Reason::CreatureProfileRequired: return "creature_profile_required";
    case Reason::SnapshotIncomplete: return "snapshot_incomplete";
    case Reason::InvalidCatalog: return "invalid_catalog";
    case Reason::InvalidItem: return "invalid_item";
    case Reason::DuplicateInstance: return "duplicate_instance";
    case Reason::OriginUnresolved: return "origin_unresolved";
    case Reason::UnknownEquipment: return "unknown_equipment";
    case Reason::RecordMismatch: return "record_mismatch";
    }
    return "invalid_reason";
}
static_assert(!kGameplayWrites && !kEngineMemoryAccess && !Result::regionCoverageAuthority
    && !Result::layerOrderVerified && !Result::bareRegionVerified && !Result::armourPreview);
}

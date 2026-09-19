#pragma once
#include <cstdint>
#include <limits>

// Native diagnostic copy identity, NOT an ImpactBinding component/application.
// No engine pointers, retained payload, game writes or exact-impact assertions.
namespace nvo::capture {
struct Key {
    std::uint64_t generation{}, transaction{}, copy{};
    unsigned session{};
};
inline bool Complete(const Key& k) noexcept
{ return k.generation && k.transaction && k.copy && k.session; }
inline bool Same(const Key& a, const Key& b) noexcept
{
    return Complete(a) && Complete(b) && a.generation == b.generation
        && a.transaction == b.transaction && a.copy == b.copy && a.session == b.session;
}
// Saturate instead of reusing an identity on wrap. Callers disable/taint capture.
inline bool Advance(std::uint64_t& value) noexcept
{
    if (value == (std::numeric_limits<std::uint64_t>::max)()) return false;
    ++value; return true;
}
enum class ArmourStatus {
    NotObserved, ScopeRejected, Reentrant, BoundaryRejected, UnsupportedTarget,
    LimitReached, ForeignThread, Stale, ReaderRejected, Complete
};
struct ArmourReceipt {
    Key key;
    ArmourStatus status{ArmourStatus::NotObserved};
    std::uint64_t readerEpoch{};
    unsigned sequence{}, items{};
    bool enumerationComplete{}, stableDoubleRead{};
};
// A match means same diagnostic copy only, not atomic impact or protection.
inline bool Joined(const Key& current, bool scopeValid, const ArmourReceipt& r) noexcept
{ return scopeValid && Same(current, r.key); }
inline const char* Name(ArmourStatus s) noexcept
{
    switch (s) {
    case ArmourStatus::NotObserved: return "not_observed";
    case ArmourStatus::ScopeRejected: return "scope_rejected";
    case ArmourStatus::Reentrant: return "reentrant";
    case ArmourStatus::BoundaryRejected: return "boundary_rejected";
    case ArmourStatus::UnsupportedTarget: return "unsupported_target";
    case ArmourStatus::LimitReached: return "diagnostic_limit";
    case ArmourStatus::ForeignThread: return "foreign_thread";
    case ArmourStatus::Stale: return "lifecycle_changed";
    case ArmourStatus::ReaderRejected: return "reader_rejected";
    case ArmourStatus::Complete: return "stable_equipment_copy";
    }
    return "invalid_receipt";
}
}

#pragma once
#include <cstddef>
#include <cstdint>

namespace nvo::attribution {
// These are observed call routes, NOT damage components or applications.
enum class Route : unsigned { Unclassified, HealthHelper, HitCondition };
enum class Witness : unsigned { UnknownCaller, ArgumentMismatch, BytesUnavailable, BytesMismatch, Verified };
struct Site {
    std::uint32_t caller, begin;
    std::size_t size;
    std::uint64_t hash;
    Route route;
};
// Fingerprints of retained, manifest-checked 3K/3L runtime captures. No new
// hook is installed. Verify each matching caller's window before labeling it.
inline constexpr Site kSites[] = {
    {0x0089D82D, 0x0089D80E, 31, 0xBA8F8D907EB3EA79ull, Route::HealthHelper},
    {0x0089BDD8, 0x0089BDAF, 41, 0x0F240085048900B4ull, Route::HitCondition},
    {0x0089BB8E, 0x0089BB65, 41, 0x907658F5F564234Cull, Route::HitCondition},
};
inline std::uint64_t Hash(const unsigned char* data, std::size_t size) noexcept {
    std::uint64_t value = 14695981039346656037ull;
    for (std::size_t i=0; i<size; ++i) { value ^= data[i]; value *= 1099511628211ull; }
    return value;
}
inline const char* Name(Route value) noexcept {
    switch(value) {
    case Route::HealthHelper: return "health_helper_call";
    case Route::HitCondition: return "hitme_condition_call";
    default: return "unclassified_call";
    }
}
inline const char* Name(Witness value) noexcept {
    switch(value) {
    case Witness::Verified: return "verified_window";
    case Witness::ArgumentMismatch: return "argument_mismatch";
    case Witness::BytesUnavailable: return "bytes_unavailable";
    case Witness::BytesMismatch: return "bytes_mismatch";
    default: return "unknown_caller";
    }
}
inline const char* Carrier(bool present, std::uint32_t id, unsigned type) noexcept {
    if (!present) return "absent";
    if (!id) return "unresolved";
    if ((type>=0x3D && type<=0x40) || type==0x69) return "projectile";
    if (type==0x3B || type==0x3C) return "actor";
    // BGSExplosion's base-form type does not prove the live carrier layout.
    return "other";
}
inline bool ExplosionFlag(std::uint32_t flags) noexcept { return (flags & 0x2000u)!=0; }
} // namespace nvo::attribution

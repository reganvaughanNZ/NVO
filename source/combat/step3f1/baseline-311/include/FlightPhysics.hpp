#pragma once
#include <cstdint>

namespace nvo::physics {
// Installs only during xNVSE deferred initialization, before a loaded capture.
void Initialize() noexcept;
void BeginCapture(unsigned session) noexcept;
void Suspend(const char* reason) noexcept;
bool Ready(double units) noexcept;
void Track(void* projectile, unsigned long long serial, std::uint32_t source,
    std::uint32_t weapon, std::uint32_t ammo, std::uint32_t base, unsigned profile,
    unsigned dragModel, double ballisticCoefficient) noexcept;
void Event(void* projectile, unsigned long long serial, bool destroyed) noexcept;
// Normalizes only fully contained, byte-verified hooks owned by this module.
// Used by both physics and timing fingerprints; foreign changes are preserved/rejected.
bool NormalizeOwnedHooks(std::uintptr_t address, unsigned char* bytes, unsigned size) noexcept;
}

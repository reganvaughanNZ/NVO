#pragma once
#include <cstddef>
#include <cstdint>

namespace nvo::hit {
// Interoperability layout, verified against JIP 57.30 GameProcess.h.
// This is the CURRENT CopyHitData argument, never the actor's cached history.
struct Data {
    void* source;
    void* target;
    void* carrier; // May be a projectile, explosion, actor or null.
    std::uint32_t weaponAV;
    std::int32_t region;
    float health, base, fatigue, limb, blockDT, armor, weaponDamage;
    void* weapon;
    float condition;
    float position[3], angle[3];
    void* criticalEffect;
    void* unknown54;
    std::uint32_t flags;
    float multiplier;
    std::int32_t unused60;
};
static_assert(sizeof(Data) == 0x64);
static_assert(offsetof(Data, region) == 0x10);
static_assert(offsetof(Data, health) == 0x14);
static_assert(offsetof(Data, weapon) == 0x30);
static_assert(offsetof(Data, flags) == 0x58);

struct Form { std::uint32_t id{}; unsigned char type{}; };
bool ReadForm(void* form, Form& result) noexcept;
bool ReadBytes(const void* address, void* destination, std::size_t size) noexcept;
bool IsProjectile(unsigned char type) noexcept;
// Returns a verified AMMO ID, or zero/unknown. Never uses currently equipped ammo.
std::uint32_t ProjectileAmmo(void* projectile, unsigned& failures) noexcept;
// True only after the current capture's existing game/JIP ammo guard passed.
bool ProjectileLayoutReady() noexcept;
// Installs once, then verifies ownership on subsequent capture activations.
bool EnsureInstalled() noexcept;
} // namespace nvo::hit

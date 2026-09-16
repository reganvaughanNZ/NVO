#pragma once
#include <cstdint>
#include "NvseBootstrapApi.hpp"
#include "NativeObserver.hpp"

// Called inside NativeObserver's serialized lifecycle/event callbacks. 3B3 also
// delegates private-pilot timing to FlightTiming, which owns one guarded slot.
namespace nvo::flight {
void BeginCapture(unsigned session, bool layoutReady, bool selectorReady) noexcept;
observer::FormResult* SelectProjectile(void* actor, void* projectileBase, void* weapon) noexcept;
// Run the fixed console notice only after the parent observer releases its lock.
void EmitNotice(const nvse::ConsolePrefix* console) noexcept;
void Suspend(const char* reason) noexcept;
void Create(void* projectile, std::uint32_t source, std::uint32_t weapon,
    std::uint32_t ammo, unsigned long long lifetime, bool tracked) noexcept;
void EndSample(void* projectile, unsigned long long lifetime, bool destroyed) noexcept;
} // namespace nvo::flight

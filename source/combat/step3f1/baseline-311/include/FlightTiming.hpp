#pragma once
#include <cstdint>
#include "NvseBootstrapApi.hpp"

namespace nvo::timing {
// Own lock; never acquires the parent observer lock or calls the engine under it.
// Updates may run on another thread. Shared per-lifetime state correlates events;
// TLS is only for synchronous return continuations, never cross-thread markers.
void BeginCapture(unsigned session) noexcept;
void Suspend(const char* reason) noexcept;
void EmitNotice(const nvse::ConsolePrefix* console) noexcept;
void Track(void* projectile, unsigned long long serial, std::uint32_t ref,
    std::uint32_t source, std::uint32_t weapon, std::uint32_t ammo,
    std::uint32_t base, float life, float distance) noexcept;
void Event(void* projectile, unsigned long long serial, bool destroyed) noexcept;
}

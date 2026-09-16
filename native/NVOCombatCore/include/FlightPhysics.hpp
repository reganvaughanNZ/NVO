#pragma once
#include <cstdint>
#include "FlightAdmission.hpp"

namespace nvo::physics {
// Installs only during xNVSE deferred initialization, before a loaded capture.
void Initialize() noexcept;
void BeginCapture(unsigned session) noexcept;
void Suspend(const char* reason) noexcept;
bool Ready(double units) noexcept;
admission::Ticket Reserve(unsigned long long serial, const admission::Profile& profile) noexcept;
bool Attach(admission::Ticket ticket, void* projectile, std::uint32_t ref) noexcept;
bool Commit(admission::Ticket ticket) noexcept;
bool Cancel(admission::Ticket ticket) noexcept;
void Fault(admission::Ticket ticket) noexcept;
void Event(void* projectile, unsigned long long serial, bool destroyed) noexcept;
// Diagnostic input copied at the existing current-hit observer. No pointers
// retained and no candidate or body region is exposed as damage authority.
struct HitQuery {
    unsigned session{}, context{};
    unsigned long long lifetime{};
    std::uint32_t projectile{}, source{}, target{}, weapon{}, ammo{};
    int region{-1};
    std::uint32_t flags{};
    float position[3]{};
};
void ObserveHit(void* projectile,const HitQuery& query) noexcept;
// Normalizes only fully contained, byte-verified hooks owned by this module.
// Used by both physics and timing fingerprints; foreign changes are preserved/rejected.
bool NormalizeOwnedHooks(std::uintptr_t address, unsigned char* bytes, unsigned size) noexcept;
}

#pragma once
#include "CurrentHit.hpp"

namespace nvo::transaction {
// Read-only call scopes, not a damage API. The provider's return is not proof
// of committed health/limb loss. No snapshot pointer escapes its call scope.
void Initialize() noexcept;
void QueueCapture(unsigned session) noexcept;
void Tick() noexcept;
void Suspend(const char* reason) noexcept;
struct CopyScope {
    unsigned long long id{};
    unsigned long long lifetime{};
    unsigned session{};
    std::uint32_t source{}, target{}, carrier{}, weapon{}, ammo{};
    std::int32_t region{};
    std::uint32_t flags{};
    std::uint32_t thread{};
    bool exactInput{}, identityMatch{}, processMatch{}, mainThread{}, tainted{};
    bool valid{};
};
// Returns copied scalar evidence only. No engine pointer escapes this call.
CopyScope CopyInput(const nvo::hit::Data* input, void* process) noexcept;
void HitEvent(void* thisObj, void* params) noexcept;
void HealthEvent(void* thisObj, void* params) noexcept;
struct Scope {
    unsigned long long id{};
    unsigned session{};
    bool matched{};
};
// Copies scalar scope identity without changing event counters or retaining pointers.
Scope MatchScope(void* receiver, void* source) noexcept;
}

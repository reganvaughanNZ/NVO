#pragma once
#include "CurrentHit.hpp"
#include "CopyCapture.hpp"

namespace nvo::transaction {
// Read-only call scopes, not a damage API. The provider's return is not proof
// of committed health/limb loss. No snapshot pointer escapes its call scope.
void Initialize() noexcept;
void QueueCapture(unsigned session) noexcept;
void Tick() noexcept;
void Suspend(const char* reason) noexcept;
struct CopyScope {
    unsigned long long id{};
    unsigned long long generation{}, copyOrdinal{};
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
// Revalidate after the armour reader, outside observer/physics locks. Does not
// increment copy counters, read game pointers, or reuse a previous copy.
bool IsCurrent(const CopyScope& scope) noexcept;
inline nvo::capture::Key CaptureKey(const CopyScope& s) noexcept
{ return {s.generation, s.id, s.copyOrdinal, s.session}; }
void HitEvent(void* thisObj, void* params) noexcept;
void HealthEvent(void* thisObj, void* params) noexcept;
struct Scope {
    unsigned long long id{};
    unsigned session{};
    bool matched{};
    unsigned long long generation{}, lifetime{}, copiesObserved{};
    std::uint32_t carrier{}, weapon{}, ammo{}, flags{};
    unsigned char carrierType{};
    bool carrierPresent{}, criticalEffectPresent{};
};
// Original transaction context only. copiesObserved counts copy-stage attempts,
// not a binding from an AV call to a particular copy/component/application.
// No engine pointer is retained and no event counter is changed.
Scope MatchScope(void* receiver, void* source) noexcept;
}

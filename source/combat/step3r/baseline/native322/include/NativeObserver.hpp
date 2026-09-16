#pragma once
#include <cstddef>
#include "CurrentHit.hpp"
#include "NvseBootstrapApi.hpp"
#include "FlightAdmission.hpp"

namespace nvo::observer {
using Handler = void (__cdecl*)(void*, void*);
// Prefix-compatible form-valued NVSEArrayVarInterface::Element. Stored in a
// profile, not on a callback stack: xNVSE consumes its address after return.
struct alignas(8) FormResult {
    union { double number{}; void* form; };
    unsigned char type{};
};
static_assert(offsetof(FormResult, type) == 8 && sizeof(FormResult) == 16);
// xNVSE EventManager interface ID 8 has no leading version field.
// Unused function pointer slots: RegisterEvent, DispatchEvent, DispatchEventAlt.
struct EventApiPrefix {
    void (__cdecl* unused[3])();
    bool (__cdecl* SetNativeEventHandler)(const char*, Handler);
    bool (__cdecl* RemoveNativeEventHandler)(const char*, Handler);
    void (__cdecl* unusedAfter[3])(); // alias registration, two deferred dispatch APIs
    void (__cdecl* SetNativeHandlerFunctionValue)(FormResult&);
};
static_assert(sizeof(EventApiPrefix) == 36);
static_assert(offsetof(EventApiPrefix, SetNativeEventHandler) == 12);
static_assert(offsetof(EventApiPrefix, RemoveNativeEventHandler) == 16);
static_assert(offsetof(EventApiPrefix, SetNativeHandlerFunctionValue) == 32);

void Initialize(EventApiPrefix* api, const nvo::nvse::ConsolePrefix* console) noexcept;
void QueueCapture(const char* reason) noexcept;
void Tick() noexcept;
void Suspend(const char* reason) noexcept;
// Called by the spawn wrapper outside its lock. No observer/physics lock is
// held across the engine call; reservations are settled only by exact receipt.
admission::Reservation ReserveSpawn(unsigned session, void* actor, void* base, void* weapon) noexcept;
void FinishSpawn(const admission::Reservation& reservation, void* result, bool paired, bool cleanCancellation) noexcept;
void CurrentHit(const nvo::hit::Data* data, void* process, const void* caller) noexcept;
// Identity-only lookup for a synchronous pre-provider snapshot. Does not
// consume legacy context/log budgets and never dereferences a retained pointer.
struct LifetimeIdentity { unsigned session{}; unsigned long long lifetime{}; std::uint32_t ammo{}; };
LifetimeIdentity LookupLifetime(void* carrier, std::uint32_t ref,
    std::uint32_t source, std::uint32_t weapon) noexcept;
} // namespace nvo::observer

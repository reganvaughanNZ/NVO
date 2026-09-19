#pragma once
namespace nvo::avobserve {
void Initialize() noexcept;
void QueueCapture(unsigned session) noexcept;
void Tick() noexcept;
void Suspend(const char* reason) noexcept;
// Associates a real ITR pre-health callback with the active AV call, when its
// immutable receiver/source/delta match. Never reads/writes multiplier slots.
void HealthEvent(void* receiver, void* params) noexcept;
}

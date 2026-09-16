#pragma once
#include "CurrentHit.hpp"

namespace nvo::transaction {
// Read-only call scopes, not a damage API. The provider's return is not proof
// of committed health/limb loss. No snapshot pointer escapes its call scope.
void Initialize() noexcept;
void QueueCapture(unsigned session) noexcept;
void Tick() noexcept;
void Suspend(const char* reason) noexcept;
void CopyInput(const nvo::hit::Data* input, void* process) noexcept;
void HitEvent(void* thisObj, void* params) noexcept;
void HealthEvent(void* thisObj, void* params) noexcept;
}

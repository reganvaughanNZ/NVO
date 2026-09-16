#pragma once
#include <cstdint>

namespace nvo::spawn {
// Diagnostic only. A guarded provider continuation is forwarded exactly once;
// no projectile arguments, selection, flight or damage are changed here.
void BeginCapture(unsigned session, bool layoutReady) noexcept;
void Suspend(const char* reason) noexcept;
void Created(void* p, std::uint32_t ref, std::uint32_t source, std::uint32_t weapon) noexcept;
void Destroyed(void* p) noexcept;
}

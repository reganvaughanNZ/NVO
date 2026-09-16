#pragma once
#include "NativeObserver.hpp"

namespace nvo::damage {
// Independent, read-only ITR event streams. No health writes or result values.
void Initialize(nvo::observer::EventApiPrefix* api, const nvo::nvse::ConsolePrefix* console) noexcept;
void QueueCapture(const char* reason, unsigned session) noexcept;
void Tick() noexcept;
void Suspend(const char* reason) noexcept;
}

#pragma once
#include "NativeObserver.hpp"

namespace nvo::damage {
// Independent, read-only ITR event streams. No health writes or result values.
void Initialize(nvo::observer::EventApiPrefix* api, const nvo::nvse::ConsolePrefix* console) noexcept;
void QueueCapture(const char* reason, unsigned session) noexcept;
void Tick() noexcept;
void Suspend(const char* reason) noexcept;
// Scalar notice after a copied native transaction lacks either callback.
// Queues at most three checks per session; never calls the event API here.
void QueueCheck(unsigned session, unsigned long long transaction,
    unsigned hitCallbacks, unsigned healthCallbacks) noexcept;
}

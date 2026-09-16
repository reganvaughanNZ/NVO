#pragma once

namespace nvo::log {
// Creates NVOCombatCore.log alongside the running executable.
// Replaces the previous launch's log. No save path is recorded.
bool Initialize() noexcept;
bool Write(const char* format, ...) noexcept;
} // namespace nvo::log

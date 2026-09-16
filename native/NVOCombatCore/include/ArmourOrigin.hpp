#pragma once
#include "ArmourSnapshotReader.hpp"
#include "CoverageProfiles.hpp"
#include <cstdint>

namespace nvo::armour::origin {
constexpr unsigned kMaxMods=255;
struct Mod { char name[129]{}; std::uint8_t index{}; };
struct Table { bool stable{}; unsigned count{}; Mod mods[kMaxMods]{}; };
enum class Code { Resolved, TableUnavailable, InvalidForm, DynamicForm, IndexUnavailable };
struct Key { Code code{Code::TableUnavailable}; coverage::FormKey key{}; };
// Rebuild per capture session. Result contains copied names, no engine pointers.
bool CaptureStable(const reader::Memory&, std::uintptr_t handlerSlot, Table&) noexcept;
Key Resolve(const Table&, std::uint32_t runtimeForm) noexcept;
const char* Name(Code) noexcept;
}

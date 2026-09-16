#pragma once
#include "ArmourSnapshotReader.hpp"
#include <cstdint>

namespace nvo::armour::coverage_log {
// Called only on the existing armour observer's main-thread lifecycle/snapshot path.
void Begin(unsigned session) noexcept;
void Suspend(const char* reason) noexcept;
void Observe(unsigned session,unsigned sequence,std::uint64_t transaction,
    const reader::Snapshot&) noexcept;
}

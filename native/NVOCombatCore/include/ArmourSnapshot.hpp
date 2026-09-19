#pragma once
#include "CopyCapture.hpp"

namespace nvo::hit { struct Data; }
namespace nvo::transaction { struct CopyScope; }

namespace nvo::armour {
constexpr bool kGameplayWrites = false;
constexpr bool kSnapshotAuthority = false;
constexpr bool kArmourPreview = false;

void Initialize() noexcept;
void QueueCapture(unsigned session) noexcept;
void Tick() noexcept;
void Suspend(const char* reason) noexcept;
nvo::capture::ArmourReceipt Observe(const nvo::hit::Data* input, void* process,
    const nvo::transaction::CopyScope& scope) noexcept;
} // namespace nvo::armour

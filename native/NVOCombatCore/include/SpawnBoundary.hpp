#pragma once
#include <cstdint>
#include "FlightAdmission.hpp"

namespace nvo::spawn {
// Reserves lifecycle + physics storage before changing only the base argument.
// Unsupported paths keep their supplied projectile. No damage authority.
bool BeginCapture(unsigned session, bool layoutReady) noexcept;
void Suspend(const char* reason) noexcept;
admission::Reservation Created(void* p, std::uint32_t ref, std::uint32_t source, std::uint32_t weapon) noexcept;
void Destroyed(void* p) noexcept;
}

#pragma once
#include <cstdint>
#include <limits>
#include <optional>
#include <string_view>

// Packet 3S: offline contact-energy input contract. Not linked into the DLL.
// No engine headers, callbacks, armour conversion, health writes or apply API.
namespace nvo::energy {
inline constexpr bool kDamageAuthority = false;
inline constexpr double unknown = std::numeric_limits<double>::quiet_NaN();
inline constexpr double kKilogramsPerGrain = 0.00006479891;
inline constexpr double kMetresPerInch = 0.0254;
enum class SpeedUnit { Unknown, MetresPerSimulationSecond, EngineUnitsPerSecond };
enum class Clock { Unknown, ParentBulletUpdateDelta };
enum class Producer { Unknown, OwnedSegmentEstimate, EngineBaseline, BeforeMovement };
enum class Reason { None, UnsupportedProfile, Identity, Producer, Snapshot, Geometry, Units, Time, Speed, Arithmetic };
struct FormKeys {
    std::string_view weapon, ammo, sourceProjectile;
};
struct Profile {
    std::string_view id;
    FormKeys keys;
    double massGrains, diameterInches;
};
// Canonical originating plugin/local IDs; never strip a live load-order byte.
const Profile* FindProfile(const FormKeys&) noexcept;
struct Identity {
    std::uint64_t capture{}, session{}, lifetime{};
    std::uint32_t step{}, projectile{}, source{}, target{}, weapon{}, ammo{}, base{};
};
bool SameIdentity(const Identity&, const Identity&) noexcept;
struct Input {
    FormKeys keys;
    Identity contact, velocity;
    bool profileMappingVerified{}, completeSnapshot{}, multipleContacts{};
    bool movementApplied{}, baselineVerified{}, candidateAvailable{};
    Producer producer{Producer::Unknown};
    SpeedUnit speedUnit{SpeedUnit::Unknown};
    Clock clock{Clock::Unknown};
    double speed{unknown}, dt{unknown}, contactTime{unknown}, unitsPerMetre{unknown};
    double fraction{unknown}, tolerance{unknown}, offChord{unknown}, modelGap{unknown};
    double endpointError{unknown}, accountingError{unknown};
};
struct Estimate {
    double massKg{}, diameterM{}, conditionalJoules{};
};
struct Result {
    Reason reason{Reason::None};
    std::optional<Estimate> estimate;
    // Even a valid estimate has uncalibrated world/clock scale and an unverified
    // damage-time producer. No caller-supplied boolean can lift those barriers.
    static constexpr bool damageAuthority = false;
};
Result Evaluate(const Input&) noexcept;
const char* ReasonName(Reason) noexcept;
}

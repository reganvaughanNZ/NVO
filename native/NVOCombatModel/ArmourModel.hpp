#pragma once
#include <array>
#include <cstdint>
#include <limits>
#include <vector>

// Offline preview model. Deliberately no engine/NVSE headers, hooks or apply API.
namespace nvo::model {
inline constexpr bool kGameplayWrites = false;
inline constexpr double unknown = std::numeric_limits<double>::quiet_NaN();
enum class Family { Kinetic, Laser, Plasma, Flame, Blast, Unsupported };
enum class Unit { Unknown, Kilograms, Metres, MetresPerSecond, Dose, DosePerGameSecond, GameSeconds, Joules };
enum class Construction { Ball, AP, HP, Pellet, Unknown };
enum class Region { Head, Torso, LeftArm, RightArm, LeftLeg, RightLeg, Unknown };
enum class Mode { RealTime, Vats, Unknown };
enum class Anatomy { Biological, Mechanical, Unknown };
enum class Status { PreviewOnly, Unsupported, InvalidInput };
enum class Reason { None, Context, Family, Region, Measurement, Profile, Layer, Arithmetic };
constexpr std::uint32_t Cover(Region r) noexcept {
    return r >= Region::Head && r < Region::Unknown ? 1u << static_cast<unsigned>(r) : 0;
}
struct Measurement { double value{unknown}; Unit unit{Unit::Unknown}; bool verified{}; };
struct Context {
    std::uint64_t session{}, component{}, application{};
    std::uint32_t source{}, target{};
    Region actualRegion{Region::Unknown};
    Mode mode{Mode::Unknown};
    bool identitiesVerified{}, pathVerified{}, modifierOwnershipVerified{}, armourComplete{};
};
struct Threat {
    Family family{Family::Unsupported};
    Construction construction{Construction::Unknown};
    Measurement mass, diameter, impactSpeed, dose, doseRate, duration;
    bool profileVerified{}, contactVerified{}, unitsCalibrated{}, woundPayload{};
};
// Synthetic first model: coarse reported-region coverage, no incidence angle.
// Resistance is an AUTHORed stopping-energy threshold per construction, not
// a claim to simulate physical plate failure from energy alone.
struct Response {
    bool supported{};
    Unit unit{Unit::Unknown};
    std::array<double, 4> resistanceJ{{unknown, unknown, unknown, unknown}};
    double bluntFraction{unknown};
    double shieldFraction{unknown}; // non-kinetic fraction, linear in condition
    double wearPerAbsorbedUnit{unknown}; // normalized condition loss / J or dose
};
struct Layer {
    std::uint64_t instance{};
    std::uint32_t coverage{};
    double condition{unknown}; // [0,1]; snapshot at impact
    bool profileVerified{};
    std::array<Response, 5> response; // distinct Kinetic/Laser/Plasma/Flame/Blast
};
struct TargetProfile {
    Anatomy anatomy{Anatomy::Unknown};
    bool verified{};
    Unit inputUnit{Unit::Unknown}; // J for kinetic, NVO Dose for other families
    double directHpPerUnit{unknown}, bluntHpPerJoule{unknown}, limbPerHp{unknown};
    double tissueCoupling{unknown}; // [0,1], not another difficulty multiplier
};
struct Wear { std::uint64_t instance{}; double loss{}; };
// Region/owner-neutral kinetic arithmetic shared by the legacy preview and 4G.
// Caller supplies complete ordered contacted surfaces and already-evaluated
// stopping capacities. Transmitted energy is a SUBSET of stopped energy.
struct KineticLayer {
    std::uint64_t key{};
    double stoppingJ{unknown}, condition{unknown}, transmittedFraction{unknown}, lossPerStoppedJ{unknown};
};
struct KineticLayerResult {
    std::uint64_t key{};
    double incomingJ{}, stoppedJ{}, outgoingJ{}, transmittedJ{}, retainedJ{}, conditionLoss{};
};
struct KineticBudget {
    Status status{Status::InvalidInput};
    Reason reason{Reason::Layer};
    double incidentJ{}, residualJ{}, stoppedJ{}, transmittedJ{}, retainedJ{};
    std::vector<KineticLayerResult> layers;
};
KineticBudget ResolveKineticLayers(double incidentJ, const std::vector<KineticLayer>&);
struct Preview {
    Status status{Status::Unsupported}; Reason reason{Reason::Context};
    Unit unit{Unit::Unknown};
    double incident{}, residual{}, bluntJoules{}, absorbed{}, directHp{}, limb{};
    bool armourPenetrated{}, biologicalWoundEligible{}, mechanicalDamage{}, woundPayloadEligible{};
    std::vector<Wear> wear;
};
// This is a pure preview, not an admission token or commitment of engine damage.
// Caller retains component identity; no deduplication by weapon/frame/time.
Preview Resolve(const Context&, const Threat&, const TargetProfile&, const std::vector<Layer>&);
}

#pragma once
#include "ArmourModel.hpp"
#include <cstddef>
#include <thread>

// OFFLINE SIMULATION ONLY. No engine admission, projectile substitution or writes.
namespace nvo::model::offline {
enum class ComponentKind { Projectile, Beam, Exposure, Blast, Unknown };
enum class Code { Ok, Unsupported, Duplicate, IdentityConflict, Full, StaleSession,
    RetiredComponent, WrongThread, InvalidToken, BadTransition, SnapshotChanged,
    ModelRejected, ResourceFailure, Busy, InvalidBoundary, Exhausted };
enum class Phase { Free, Reserved, Resolved, SimulationStarted, Acknowledged, Rejected, Faulted };
struct Revisions {
    std::uint64_t classification{}, profile{}, settings{}, armour{}, anatomy{};
};
struct Envelope {
    Context context;
    Family family{Family::Unsupported};
    ComponentKind kind{ComponentKind::Unknown};
    Revisions revisions;
    std::uint64_t sourceGeneration{}, targetGeneration{};
};
struct Token {
    std::uint64_t ledger{}, session{}, generation{};
    std::size_t slot{static_cast<std::size_t>(-1)};
};
struct Admission { Code code{Code::Unsupported}; Token token; };
struct Inspection {
    Phase phase{Phase::Free};
    Status modelStatus{Status::Unsupported};
    Reason modelReason{Reason::None};
    double incident{}, hp{}, limb{};
    std::size_t wearEntries{};
};
struct Usage { std::size_t retained{}, capacity{}; std::uint64_t session{}, retiredThrough{}; };

class AdmissionLedger final {
public:
    static constexpr std::size_t kCapacity = 128;
    static constexpr std::size_t kMaxLayers = 16;
    explicit AdmissionLedger(std::size_t capacity = kCapacity);
    AdmissionLedger(const AdmissionLedger&) = delete;
    AdmissionLedger& operator=(const AdmissionLedger&) = delete;
    AdmissionLedger(AdmissionLedger&&) = delete;
    AdmissionLedger& operator=(AdmissionLedger&&) = delete;
    Code ResetSession(std::uint64_t nextSession);
    Admission Reserve(const Envelope&);
    Code ResolveReserved(Token, const Revisions& current, const Threat&,
                         const TargetProfile&, const std::vector<Layer>&);
    Code BeginSimulatedApplication(Token);
    Code AcknowledgeSimulation(Token);
    Code RejectOrFault(Token);
    // Producer must prove no future valid applications at/below this component ID.
    // Never retire active or uncertain partially-applied simulations.
    Code RetireThrough(std::uint64_t component, bool producerClosureVerified);
    Code Inspect(Token, Inspection&) const;
    Code GetUsage(Usage&) const;
private:
    struct Entry { Envelope envelope; std::uint64_t generation{}; Phase phase{Phase::Free}; Preview preview; };
    Code Locate(Token, std::size_t&) const;
    const std::thread::id owner_;
    const std::uint64_t ledger_;
    const std::size_t capacity_;
    std::array<Entry, kCapacity> entries_;
    std::uint64_t session_{}, nextGeneration_{1}, retiredThrough_{};
};
}

#include "AdmissionLedger.hpp"
#include <atomic>
#include <limits>
#include <new>
#include <utility>

namespace nvo::model::offline {
namespace {
std::uint64_t NextLedger() {
    static std::atomic<std::uint64_t> next{1};
    auto value = next.load(std::memory_order_relaxed);
    while (value != std::numeric_limits<std::uint64_t>::max())
        if (next.compare_exchange_weak(value, value + 1, std::memory_order_relaxed)) return value;
    return 0; // Exhausted cookies never wrap and alias a different ledger.
}
bool Same(const Revisions& a, const Revisions& b) {
    return a.classification == b.classification && a.profile == b.profile &&
        a.settings == b.settings && a.armour == b.armour && a.anatomy == b.anatomy;
}
bool Valid(const Envelope& e) {
    const auto& c = e.context;
    if (!c.session || !c.component || !c.application || !c.source || !c.target ||
        !e.sourceGeneration || !e.targetGeneration || !c.identitiesVerified ||
        !c.pathVerified || !c.modifierOwnershipVerified || !c.armourComplete ||
        !Cover(c.actualRegion) || (c.mode != Mode::RealTime && c.mode != Mode::Vats)) return false;
    const auto& r = e.revisions;
    if (!r.classification || !r.profile || !r.settings || !r.armour || !r.anatomy) return false;
    switch (e.family) {
    case Family::Kinetic: case Family::Plasma: return e.kind == ComponentKind::Projectile;
    case Family::Laser: return e.kind == ComponentKind::Beam || e.kind == ComponentKind::Projectile;
    case Family::Flame: return e.kind == ComponentKind::Exposure;
    case Family::Blast: return e.kind == ComponentKind::Blast;
    default: return false;
    }
}
bool SameKey(const Envelope& a, const Envelope& b) {
    // Per-target applications of a shared explosion remain distinct.
    return a.context.component == b.context.component && a.context.application == b.context.application &&
           a.context.target == b.context.target;
}
bool SameEnvelope(const Envelope& a, const Envelope& b) {
    const auto& x = a.context; const auto& y = b.context;
    return SameKey(a,b) && x.session == y.session && x.source == y.source &&
        x.actualRegion == y.actualRegion && x.mode == y.mode && x.identitiesVerified == y.identitiesVerified &&
        x.pathVerified == y.pathVerified && x.modifierOwnershipVerified == y.modifierOwnershipVerified &&
        x.armourComplete == y.armourComplete && a.family == b.family && a.kind == b.kind &&
        a.sourceGeneration == b.sourceGeneration && a.targetGeneration == b.targetGeneration &&
        Same(a.revisions,b.revisions);
}
bool Retirable(Phase p) { return p == Phase::Acknowledged || p == Phase::Rejected; }
}

AdmissionLedger::AdmissionLedger(std::size_t capacity)
    : owner_(std::this_thread::get_id()), ledger_(NextLedger()), capacity_(capacity <= kCapacity ? capacity : 0) {}

Code AdmissionLedger::ResetSession(std::uint64_t nextSession) {
    if (std::this_thread::get_id() != owner_) return Code::WrongThread;
    if (!nextSession || nextSession <= session_) return Code::StaleSession;
    for (auto& e : entries_) e = {};
    session_ = nextSession; retiredThrough_ = 0;
    return Code::Ok;
}

Admission AdmissionLedger::Reserve(const Envelope& e) {
    if (std::this_thread::get_id() != owner_) return {Code::WrongThread,{}};
    if (!ledger_ || nextGeneration_ == std::numeric_limits<std::uint64_t>::max()) return {Code::Exhausted,{}};
    if (!session_ || e.context.session != session_) return {Code::StaleSession,{}};
    if (e.context.component && e.context.component <= retiredThrough_) return {Code::RetiredComponent,{}};
    // Check retained identity BEFORE considering capacity or new input validity.
    for (std::size_t i=0; i<capacity_; ++i) {
        const auto& old=entries_[i];
        if (old.phase != Phase::Free && SameKey(old.envelope,e))
            return {SameEnvelope(old.envelope,e) ? Code::Duplicate : Code::IdentityConflict,{}};
    }
    if (!Valid(e)) return {Code::Unsupported,{}};
    for (std::size_t i=0; i<capacity_; ++i) {
        auto& slot=entries_[i];
        if (slot.phase != Phase::Free) continue;
        slot.envelope=e; slot.generation=nextGeneration_++; slot.phase=Phase::Reserved;
        return {Code::Ok,{ledger_,session_,slot.generation,i}};
    }
    return {Code::Full,{}};
}

Code AdmissionLedger::Locate(Token t, std::size_t& index) const {
    if (std::this_thread::get_id() != owner_) return Code::WrongThread;
    if (!t.ledger || t.ledger != ledger_ || !t.generation || t.slot >= capacity_) return Code::InvalidToken;
    if (t.session != session_) return Code::StaleSession;
    const auto& e=entries_[t.slot];
    if (e.phase == Phase::Free || t.generation != e.generation) return Code::InvalidToken;
    index=t.slot; return Code::Ok;
}

Code AdmissionLedger::ResolveReserved(Token t, const Revisions& current, const Threat& threat,
    const TargetProfile& target, const std::vector<Layer>& layers) {
    std::size_t i{}; const auto found=Locate(t,i); if (found != Code::Ok) return found;
    auto& e=entries_[i]; if (e.phase != Phase::Reserved) return Code::BadTransition;
    if (!Same(e.envelope.revisions,current)) { e.phase=Phase::Rejected; return Code::SnapshotChanged; }
    if (threat.family != e.envelope.family || layers.size() > kMaxLayers) {
        e.phase=Phase::Rejected; return Code::Unsupported;
    }
    try {
        auto preview=nvo::model::Resolve(e.envelope.context,threat,target,layers);
        e.preview=std::move(preview);
    } catch (const std::bad_alloc&) {
        e.preview={}; e.phase=Phase::Rejected; return Code::ResourceFailure;
    }
    if (e.preview.status != Status::PreviewOnly) { e.phase=Phase::Rejected; return Code::ModelRejected; }
    e.phase=Phase::Resolved; return Code::Ok;
}

Code AdmissionLedger::BeginSimulatedApplication(Token t) {
    std::size_t i{}; const auto found=Locate(t,i); if (found != Code::Ok) return found;
    auto& e=entries_[i]; if (e.phase != Phase::Resolved) return Code::BadTransition;
    e.phase=Phase::SimulationStarted; return Code::Ok; // Bookkeeping only, no side effects.
}
Code AdmissionLedger::AcknowledgeSimulation(Token t) {
    std::size_t i{}; const auto found=Locate(t,i); if (found != Code::Ok) return found;
    auto& e=entries_[i]; if (e.phase != Phase::SimulationStarted) return Code::BadTransition;
    e.phase=Phase::Acknowledged; return Code::Ok;
}
Code AdmissionLedger::RejectOrFault(Token t) {
    std::size_t i{}; const auto found=Locate(t,i); if (found != Code::Ok) return found;
    auto& e=entries_[i];
    if (e.phase == Phase::Reserved || e.phase == Phase::Resolved) {
        e.phase=Phase::Rejected; e.preview={}; return Code::Ok;
    }
    if (e.phase == Phase::SimulationStarted) { e.phase=Phase::Faulted; return Code::Ok; }
    return Code::BadTransition;
}

Code AdmissionLedger::RetireThrough(std::uint64_t component, bool producerClosureVerified) {
    if (std::this_thread::get_id() != owner_) return Code::WrongThread;
    if (!session_ || !producerClosureVerified || !component || component < retiredThrough_) return Code::InvalidBoundary;
    // Preflight every entry before changing anything. Faulted partial simulations
    // deliberately retain ownership until a new session instead of allowing replay.
    for (std::size_t i=0; i<capacity_; ++i) {
        const auto& e=entries_[i];
        if (e.phase != Phase::Free && e.envelope.context.component <= component && !Retirable(e.phase)) return Code::Busy;
    }
    for (std::size_t i=0; i<capacity_; ++i) {
        auto& e=entries_[i];
        if (e.phase != Phase::Free && e.envelope.context.component <= component) e={};
    }
    retiredThrough_=component; return Code::Ok;
}
Code AdmissionLedger::Inspect(Token t, Inspection& out) const {
    out={}; std::size_t i{}; const auto found=Locate(t,i); if (found != Code::Ok) return found;
    const auto& e=entries_[i]; const auto& p=e.preview;
    out={e.phase,p.status,p.reason,p.incident,p.directHp,p.limb,p.wear.size()}; return Code::Ok;
}
Code AdmissionLedger::GetUsage(Usage& out) const {
    out={}; if (std::this_thread::get_id() != owner_) return Code::WrongThread;
    out.capacity=capacity_; out.session=session_; out.retiredThrough=retiredThrough_;
    for (std::size_t i=0; i<capacity_; ++i) if (entries_[i].phase != Phase::Free) ++out.retained;
    return Code::Ok;
}
}

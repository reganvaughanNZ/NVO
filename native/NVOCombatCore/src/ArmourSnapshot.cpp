#include "ArmourSnapshot.hpp"
#include "ArmourSnapshotReader.hpp"
#include "ArmourCoverage.hpp"
#include "CurrentHit.hpp"
#include "HitTransaction.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <cstdint>
#include <cstring>

namespace {
using U32 = std::uint32_t;
using U64 = unsigned long long;
constexpr unsigned kSnapshotLimit = 64;
SRWLOCK gLock = SRWLOCK_INIT;

struct Lock final {
    Lock() noexcept { AcquireSRWLockExclusive(&gLock); }
    ~Lock() { ReleaseSRWLockExclusive(&gLock); }
    Lock(const Lock&) = delete;
    Lock& operator=(const Lock&) = delete;
};
struct ErrorGuard final {
    DWORD value = GetLastError();
    ~ErrorGuard() { SetLastError(value); }
};
struct Permit {
    U64 epoch{};
    unsigned session{}, ordinal{};
    bool valid{};
    nvo::capture::ArmourStatus refusal{nvo::capture::ArmourStatus::NotObserved};
};
struct SummaryData {
    unsigned session{}, attempts{}, completed{}, noArmour{}, rejected{}, unstable{};
    unsigned omitted{}, scopeRejected{}, unsupportedTargetSkipped{}, stale{};
};

bool gPending{}, gActive{};
unsigned gRequestedSession{}, gSession{};
DWORD gMainThread{};
U64 gEpoch{};
SummaryData gCounts{};
__declspec(thread) unsigned gObserveDepth{};
__declspec(thread) bool gObserveTainted{};

struct RecursionGuard final {
    bool outer{};
    RecursionGuard() noexcept {
        outer = gObserveDepth == 0;
        if (outer) gObserveTainted = false;
        else gObserveTainted = true;
        ++gObserveDepth;
    }
    ~RecursionGuard() { --gObserveDepth; }
};

bool RuntimeRead(void*, const void* source, void* destination, std::size_t size) noexcept
{
    return nvo::hit::ReadBytes(source, destination, size);
}

void WriteSummary(const char* reason, const SummaryData& value) noexcept
{
    nvo::log::Write("ARMOUR_SNAPSHOT_SUMMARY session=%u reason=%s attempts=%u complete_with_armour=%u complete_no_armour_observed=%u rejected=%u unstable=%u omitted_after_limit=%u scope_rejected=%u unsupported_target_skipped=%u stale_epoch=%u snapshot_authority=0 armour_preview=0 gameplay_writes=0",
        value.session, reason, value.attempts, value.completed, value.noArmour,
        value.rejected, value.unstable, value.omitted, value.scopeRejected,
        value.unsupportedTargetSkipped, value.stale);
}

bool Eligible(const nvo::transaction::CopyScope& scope) noexcept
{
    const Lock lock;
    if (!gActive || scope.session != gSession) return false;
    if (!scope.valid || !scope.mainThread || scope.tainted
        || !nvo::capture::Complete(nvo::transaction::CaptureKey(scope))) {
        ++gCounts.scopeRejected;
        return false;
    }
    return true;
}

void SkipUnsupported(const nvo::transaction::CopyScope& scope) noexcept
{
    const Lock lock;
    if (gActive && scope.session == gSession) ++gCounts.unsupportedTargetSkipped;
}

Permit Reserve(const nvo::transaction::CopyScope& scope) noexcept
{
    const Lock lock;
    if (!scope.valid || !scope.mainThread || scope.tainted) {
        if (gActive) ++gCounts.scopeRejected;
        return {0,0,0,false,nvo::capture::ArmourStatus::ScopeRejected};
    }
    if (!gActive || scope.session != gSession)
        return {0,0,0,false,nvo::capture::ArmourStatus::Stale};
    if (gCounts.attempts == kSnapshotLimit) {
        ++gCounts.omitted;
        return {0,0,0,false,nvo::capture::ArmourStatus::LimitReached};
    }
    ++gCounts.attempts;
    return {gEpoch, gSession, gCounts.attempts, true};
}

bool Commit(const Permit& permit, nvo::armour::reader::Code code) noexcept
{
    const Lock lock;
    if (!gActive || gEpoch != permit.epoch || gSession != permit.session) {
        ++gCounts.stale;
        return false;
    }
    using nvo::armour::reader::Code;
    if (code == Code::CompleteWithArmour) ++gCounts.completed;
    else if (code == Code::CompleteNoArmourObserved) ++gCounts.noArmour;
    else {
        ++gCounts.rejected;
        if (code == Code::Unstable) ++gCounts.unstable;
    }
    return true;
}

bool BoundaryMatches(const nvo::hit::Data* input, void* process,
    const nvo::transaction::CopyScope& scope, nvo::hit::Data& copied,
    nvo::hit::Form& target) noexcept
{
    nvo::hit::Form source{}, carrier{}, weapon{};
    void* ownerProcess{};
    return input && process && nvo::hit::ReadBytes(input, &copied, sizeof(copied))
        && nvo::hit::ReadForm(copied.source, source)
        && nvo::hit::ReadForm(copied.target, target)
        && nvo::hit::ReadForm(copied.carrier, carrier)
        && nvo::hit::ReadForm(copied.weapon, weapon)
        && source.id == scope.source && target.id == scope.target
        && carrier.id == scope.carrier && weapon.id == scope.weapon
        && copied.region == scope.region && copied.flags == scope.flags
        && nvo::hit::ReadBytes(static_cast<const char*>(copied.target) + 0x68,
            &ownerProcess, sizeof(ownerProcess)) && ownerProcess == process;
}

void LogRejected(const Permit& permit, const nvo::transaction::CopyScope& scope,
    const char* status) noexcept
{
    nvo::log::Write("ARMOUR_SNAPSHOT session=%u seq=%u tx=%llu target=%08X phase=copy_input status=%s stable_double_read=0 enumeration_complete=0 equipped_armour_count=0 region_coverage_complete=0 layer_order_verified=0 impact_snapshot_verified=0 bare_region_verified=0 snapshot_authority=0 armour_preview=0 gameplay_writes=0",
        permit.session, permit.ordinal, scope.id, scope.target, status);
}
} // namespace

void nvo::armour::Initialize() noexcept
{
    const ErrorGuard error;
    const Lock lock;
    gMainThread = GetCurrentThreadId();
    ++gEpoch;
}

void nvo::armour::QueueCapture(unsigned session) noexcept
{
    const Lock lock;
    gActive = false;
    gPending = true;
    gRequestedSession = session;
    ++gEpoch;
}

void nvo::armour::Tick() noexcept
{
    const ErrorGuard error;
    bool ready{};
    unsigned session{};
    {
        const Lock lock;
        if (!gPending) return;
        gPending = false;
        session = gRequestedSession;
        if (!gMainThread || GetCurrentThreadId() != gMainThread) {
            gActive = false;
            ++gEpoch;
        } else {
            gSession = session;
            gCounts = {};
            gCounts.session = session;
            gActive = true;
            ++gEpoch;
            ready = true;
        }
    }
    if (ready) {
        nvo::armour::coverage_log::Begin(session);
        nvo::log::Write("ARMOUR_READER_READY session=%u phase=jip_copy_input exact_itr_scope=1 stable_double_read=1 max_snapshots=64 max_items=32 raw_equip_slots_only=1 region_coverage_complete=0 layer_order_verified=0 impact_snapshot_verified=0 bare_region_verified=0 snapshot_authority=0 armour_preview=0 gameplay_writes=0",
            session);
    } else {
        nvo::log::Write("ARMOUR_READER_DISABLED session=%u reason=activation_not_on_main_thread snapshot_authority=0 gameplay_writes=0",
            session);
    }
}

void nvo::armour::Suspend(const char* reason) noexcept
{
    SummaryData summary{};
    bool write{};
    {
        const Lock lock;
        write = gActive;
        summary = gCounts;
        gPending = false;
        gActive = false;
        ++gEpoch;
    }
    if (write) WriteSummary(reason, summary);
    nvo::armour::coverage_log::Suspend(reason);
}

nvo::capture::ArmourReceipt nvo::armour::Observe(const nvo::hit::Data* input, void* process,
    const nvo::transaction::CopyScope& scope) noexcept
{
    const ErrorGuard error;
    RecursionGuard recursion;
    using Status = nvo::capture::ArmourStatus;
    nvo::capture::ArmourReceipt receipt{};
    if (!recursion.outer) { receipt.status=Status::Reentrant; return receipt; }
    if (!Eligible(scope)) { receipt.status=Status::ScopeRejected; return receipt; }
    receipt.key=nvo::transaction::CaptureKey(scope);

    hit::Data before{};
    hit::Form target{};
    if (!BoundaryMatches(input, process, scope, before, target)) {
        const Permit permit = Reserve(scope);
        if (!permit.valid) { receipt.status=permit.refusal; return receipt; }
        receipt.readerEpoch=permit.epoch; receipt.sequence=permit.ordinal;
        const bool committed=Commit(permit, reader::Code::InvalidArgument);
        LogRejected(permit, scope, "boundary_identity_rejected");
        receipt.status=committed?Status::BoundaryRejected:Status::Stale; return receipt;
    }
    if (target.type != 0x3B) {
        SkipUnsupported(scope);
        receipt.status=Status::UnsupportedTarget; return receipt;
    }

    const Permit permit = Reserve(scope);
    if (!permit.valid) { receipt.status=permit.refusal; return receipt; }
    receipt.readerEpoch=permit.epoch; receipt.sequence=permit.ordinal;
    if (GetCurrentThreadId() != gMainThread || GetCurrentThreadId() != scope.thread) {
        const bool committed=Commit(permit, reader::Code::UnsupportedTarget);
        LogRejected(permit, scope, "foreign_thread");
        receipt.status=committed?Status::ForeignThread:Status::Stale; return receipt;
    }

    const reader::Memory memory{nullptr, RuntimeRead};
    reader::Snapshot snapshot = reader::CaptureStable(memory, before.target, scope.target);
    hit::Data after{};
    hit::Form targetAfter{};
    const bool boundaryStable = BoundaryMatches(input, process, scope, after, targetAfter)
        && std::memcmp(&before, &after, sizeof(before)) == 0;
    if (!boundaryStable || gObserveTainted) {
        snapshot = {};
        snapshot.code = reader::Code::Unstable;
        snapshot.targetId = scope.target;
    }

    if (!Commit(permit, snapshot.code)) {
        LogRejected(permit, scope, "lifecycle_epoch_changed");
        receipt.status=Status::Stale; return receipt;
    }
    nvo::log::Write("ARMOUR_SNAPSHOT session=%u seq=%u tx=%llu target=%08X phase=copy_input status=%s stable_double_read=%u enumeration_complete=%u equipped_armour_count=%u entries=%u instances=%u extras=%u region_coverage_complete=0 layer_order_verified=0 impact_snapshot_verified=0 bare_region_verified=0 snapshot_authority=0 armour_preview=0 gameplay_writes=0",
        permit.session, permit.ordinal, scope.id, scope.target, reader::Name(snapshot.code),
        snapshot.stableDoubleRead ? 1u : 0u, snapshot.enumerationComplete ? 1u : 0u,
        snapshot.itemCount, snapshot.entriesVisited, snapshot.instancesVisited,
        snapshot.extrasVisited);
    nvo::log::Write("ARMOUR_COPY_SCOPE session=%u seq=%u generation=%llu tx=%llu copy=%llu reader_epoch=%llu lifetime=%llu source=%08X target=%08X carrier=%08X weapon=%08X ammo=%08X hit_region=%d component_verified=0 application_verified=0 impact_snapshot_verified=0 gameplay_writes=0",
        scope.session,permit.ordinal,scope.generation,scope.id,scope.copyOrdinal,permit.epoch,scope.lifetime,
        scope.source,scope.target,scope.carrier,scope.weapon,scope.ammo,scope.region);
    if (!reader::Complete(snapshot.code)) { receipt.status=Status::ReaderRejected; return receipt; }
    receipt.status=Status::Complete; receipt.items=snapshot.itemCount;
    receipt.enumerationComplete=snapshot.enumerationComplete; receipt.stableDoubleRead=snapshot.stableDoubleRead;
    for (unsigned i = 0; i < snapshot.itemCount; ++i) {
        const auto& item = snapshot.items[i];
        nvo::log::Write("ARMOUR_ITEM session=%u seq=%u item=%u instance=%016llX form=%08X part_mask=%08X base_health=%u current_health=%.9g explicit_health=%u condition_ratio=%.9g armour_rating_raw=%u damage_threshold=%.9g biped_flags=%08X armour_flags=%02X traversal_order_is_layer_order=0 region_coverage_known=0 gameplay_writes=0",
            permit.session, permit.ordinal, i + 1, item.instanceToken, item.formId,
            item.partMask, item.baseHealth, static_cast<double>(item.currentHealth),
            item.explicitHealth ? 1u : 0u, static_cast<double>(item.conditionRatio),
            static_cast<unsigned>(item.armourRating), static_cast<double>(item.damageThreshold),
            static_cast<unsigned>(item.bipedFlags), static_cast<unsigned>(item.armourFlags));
    }
    nvo::armour::coverage_log::Observe(permit.session, permit.ordinal, scope.id, snapshot);
    return receipt;
}

static_assert(!nvo::armour::kGameplayWrites);
static_assert(!nvo::armour::kSnapshotAuthority);
static_assert(!nvo::armour::kArmourPreview);

// Standalone x86 tests of the production transaction-scope implementation.
// Never calls Initialize/Install/Tick, hook bridges, providers, or game addresses.
// Activation below seeds diagnostic state; reads are limited to registered fixtures.
#include <Windows.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>

namespace fixture {
struct Range { const unsigned char* data{}; std::size_t size{}; };
Range ranges[16]{};
unsigned rangeCount{}, unexpectedReads{}, checks{}, failures{}, logCalls{};
unsigned callbackGapRequests{}, callbackGapSession{}, callbackGapHit{}, callbackGapHealth{};
unsigned long long callbackGapTransaction{};
bool callbackGapOutsideLock = true;
bool resetDuringLookup{};
void* carrier{};
std::uint32_t ammunition = 0x500;

void Register(const void* data, std::size_t size) {
    if (rangeCount == 16) std::abort();
    ranges[rangeCount++] = {static_cast<const unsigned char*>(data), size};
}
void Check(bool value, const char* label) {
    ++checks;
    if (!value) { ++failures; std::printf("FAIL %s\n", label); }
}
void Require(bool value) {
    if (!value) { std::puts("FAIL fixture setup"); std::exit(2); }
}
}

// Including the production translation unit permits checks of its real TLS
// frame bookkeeping without adding public test APIs to the plugin.
#include "../src/HitTransaction.cpp"

void nvo::damage::QueueCheck(unsigned session, unsigned long long transaction,
    unsigned hitCallbacks, unsigned healthCallbacks) noexcept {
    ++fixture::callbackGapRequests;
    fixture::callbackGapSession = session;
    fixture::callbackGapTransaction = transaction;
    fixture::callbackGapHit = hitCallbacks;
    fixture::callbackGapHealth = healthCallbacks;
    const bool outside = TryAcquireSRWLockExclusive(&gLock) != FALSE;
    fixture::callbackGapOutsideLock = fixture::callbackGapOutsideLock && outside;
    if (outside) ReleaseSRWLockExclusive(&gLock);
}
bool nvo::log::Write(const char*, ...) noexcept {
    ++fixture::logCalls;
    SetLastError(9001);
    return true;
}
bool nvo::hit::ReadBytes(const void* source, void* destination, std::size_t size) noexcept {
    if (!source || !destination) return false;
    const auto p = reinterpret_cast<std::uintptr_t>(source);
    for (unsigned i = 0; i < fixture::rangeCount; ++i) {
        const auto& r = fixture::ranges[i];
        const auto begin = reinterpret_cast<std::uintptr_t>(r.data);
        if (p >= begin && p - begin <= r.size && size <= r.size - (p - begin)) {
            std::memcpy(destination, source, size); return true;
        }
    }
    ++fixture::unexpectedReads;
    return false;
}
bool nvo::hit::ReadForm(void* form, Form& out) noexcept {
    out = {};
    if (!form) return true;
    unsigned char data[16]{};
    if (!ReadBytes(form, data, sizeof(data))) return false;
    out.type = data[4]; std::memcpy(&out.id, data + 12, sizeof(out.id));
    return true;
}
bool nvo::hit::IsProjectile(unsigned char type) noexcept {
    return (type >= 0x3D && type <= 0x40) || type == 0x69;
}
std::uint32_t nvo::hit::ProjectileAmmo(void* value, unsigned&) noexcept {
    return value == fixture::carrier ? fixture::ammunition : 0;
}
nvo::observer::LifetimeIdentity nvo::observer::LookupLifetime(
    void*, std::uint32_t, std::uint32_t, std::uint32_t) noexcept {
    if (fixture::resetDuringLookup) {
        fixture::resetDuringLookup = false;
        nvo::transaction::QueueCapture(gSession); // Production invalidation.
        gPending = false; gActive = true; // Simulate a completed same-session activation.
    }
    return {gSession, 71, fixture::ammunition};
}

namespace fixture {
struct Forms {
    unsigned char actor[0x80]{}, source[0x80]{}, projectile[0x80]{}, weapon[0x80]{};
    unsigned char other[0x80]{}, process[4]{};
    nvo::hit::Data data{};
    Forms() {
        rangeCount = 0;
        Register(actor, sizeof(actor)); Register(source, sizeof(source));
        Register(projectile, sizeof(projectile)); Register(weapon, sizeof(weapon));
        Register(other, sizeof(other)); Register(process, sizeof(process));
        Register(&data, sizeof(data));
        SetForm(actor, 0x3B, 0x100); SetForm(source, 0x3B, 0x200);
        SetForm(projectile, 0x3D, 0x300); SetForm(weapon, 0x28, 0x400);
        SetForm(other, 0x3B, 0x999);
        void* p = process; std::memcpy(actor + 0x68, &p, sizeof(p));
        data.source = source; data.target = actor; data.carrier = projectile;
        data.weapon = weapon; data.region = 0; data.flags = 4;
        data.health = 5; data.condition = 1; data.multiplier = 1;
        carrier = projectile;
    }
    static void SetForm(unsigned char* bytes, unsigned char type, std::uint32_t id) {
        bytes[4] = type; std::memcpy(bytes + 12, &id, sizeof(id));
    }
};
void Reset() {
    Require(gDepth == 0);
    for (auto& f : gFrames) f = {};
    gActive = true; gPending = false; gSession = 9; gGeneration = 3;
    gMainThread = GetCurrentThreadId();
    gNextId = gEntries = gReturns = gOpen = gInvalid = gOverflow = gUnscoped = 0;
    gHitStages = gCopyStages = gHealthStages = gOmittedStages = gLogFailures = gDetailed = 0;
    resetDuringLookup = false; logCalls = 0;
    callbackGapRequests = callbackGapSession = callbackGapHit = callbackGapHealth = 0;
    callbackGapTransaction = 0; callbackGapOutsideLock = true;
}
void Enter(Forms& f, std::uintptr_t caller = 0x1234) {
    Require(Before(f.actor, &f.data, 0, caller, 0));
}
}

int main() {
    using fixture::Check;
    using nvo::transaction::CopyInput;
    using nvo::transaction::IsCurrent;
    using nvo::transaction::MatchScope;
    static_assert(sizeof(void*) == 4, "Production transaction checks require x86.");
    fixture::Forms f;
    fixture::Reset();
    const auto absent = MatchScope(f.actor, f.source);
    Check(!absent.matched && !absent.id && !absent.generation && !absent.copiesObserved,
        "absent frame supplies no transaction context");
    const auto originalData = f.data;
    f.data.flags = 0x80000004u;
    f.data.criticalEffect = f.other;
    fixture::Enter(f);
    const auto initialScope = MatchScope(f.actor, f.source);
    Check(initialScope.matched && initialScope.id == gFrames[0].id
        && initialScope.session == 9 && initialScope.generation == 3 && initialScope.lifetime == 71
        && initialScope.copiesObserved == 0 && initialScope.carrier == 0x300
        && initialScope.carrierType == 0x3D && initialScope.carrierPresent
        && initialScope.weapon == 0x400 && initialScope.ammo == 0x500
        && initialScope.flags == 0x80000004u && initialScope.criticalEffectPresent,
        "matched scope carries exact generation and raw initial transaction context");
    f.data.source = f.other; f.data.target = f.other;
    f.data.carrier = nullptr; f.data.weapon = nullptr;
    f.data.flags = 0; f.data.criticalEffect = nullptr;
    fixture::ammunition = 0x777;
    const auto retainedScope = MatchScope(f.actor, f.source);
    Check(retainedScope.matched && retainedScope.id == initialScope.id
        && retainedScope.generation == initialScope.generation
        && retainedScope.lifetime == initialScope.lifetime
        && retainedScope.carrier == initialScope.carrier
        && retainedScope.carrierType == initialScope.carrierType && retainedScope.carrierPresent
        && retainedScope.weapon == initialScope.weapon && retainedScope.ammo == initialScope.ammo
        && retainedScope.flags == initialScope.flags && retainedScope.criticalEffectPresent,
        "mutating current hit data and ammo does not rewrite entry context");
    Check(!MatchScope(f.other, f.source).matched,
        "scope rejects a receiver different from the original transaction");
    Check(!MatchScope(f.actor, f.other).matched,
        "scope rejects a source different from the original transaction");
    f.data = originalData; fixture::ammunition = 0x500;
    const auto failedAttempt = CopyInput(nullptr, f.process);
    const auto afterFailedAttempt = MatchScope(f.actor, f.source);
    Check(!failedAttempt.valid && afterFailedAttempt.matched && afterFailedAttempt.copiesObserved == 1,
        "scope counts a rejected copy attempt without establishing a valid copy");
    const auto validAttempt = CopyInput(&f.data, f.process);
    Check(validAttempt.valid && MatchScope(f.actor, f.source).copiesObserved == 2,
        "scope counts both rejected and accepted copy attempts");
    const auto scopeLogs = fixture::logCalls;
    SetLastError(8123);
    Check(MatchScope(f.actor, f.source).copiesObserved == 2 && GetLastError() == 8123
        && fixture::logCalls == scopeLogs && gCopyStages == 2
        && gFrames[0].hitEvents == 0 && gFrames[0].healthEvents == 0,
        "scope lookup preserves error state and does not emit or count another event");
    gMainThread = GetCurrentThreadId() + 1;
    gFrames[0].thread = gMainThread;
    Check(!MatchScope(f.actor, f.source).matched,
        "scope requires the actual caller to be on the main thread");
    gMainThread = GetCurrentThreadId();
    Check(!MatchScope(f.actor, f.source).matched,
        "scope rejects a frame recorded on a different thread");
    gFrames[0].thread = gMainThread;
    After();
    Check(!MatchScope(f.actor, f.source).matched, "returned frame supplies no transaction context");

    fixture::Reset();
    fixture::Enter(f);
    auto first = CopyInput(&f.data, f.process);
    Check(first.valid && first.copyOrdinal == 1 && first.generation == 3
        && first.lifetime == 71 && first.region == 0, "first exact copy retains scalar scope");
    Check(IsCurrent(first) && nvo::capture::Complete(nvo::transaction::CaptureKey(first)),
        "current copy has complete diagnostic key");
    auto second = CopyInput(&f.data, f.process);
    Check(second.valid && second.id == first.id && second.copyOrdinal == 2
        && !IsCurrent(first) && IsCurrent(second), "later copy invalidates earlier current-copy predicate");
    for (unsigned i = 2; i < 25; ++i) second = CopyInput(&f.data, f.process);
    Check(second.valid && second.copyOrdinal == 25 && gFrames[0].stages == kStageRows
        && gCopyStages == 25, "copy identity survives stage log budget");
    SetLastError(8123);
    second = CopyInput(&f.data, f.process);
    Check(IsCurrent(second) && GetLastError() == 8123, "copy and liveness preserve Win32 error state");
    Check(After() == 0x1234 && gDepth == 0 && gOpen == 0 && gReturns == 1,
        "provider return unwinds original caller and counters");
    Check(!IsCurrent(second), "returned copy is no longer current");
    Check(fixture::callbackGapRequests == 1 && fixture::callbackGapSession == 9
        && fixture::callbackGapTransaction == second.id && fixture::callbackGapHit == 0
        && fixture::callbackGapHealth == 0 && fixture::callbackGapOutsideLock,
        "copied transaction with missing callbacks queues scalar check outside transaction lock");

    fixture::Reset(); fixture::Enter(f); After();
    Check(fixture::callbackGapRequests == 0, "transaction without copy never requests callback repair");
    fixture::Reset(); fixture::Enter(f); CopyInput(&f.data, f.process);
    gFrames[0].hitEvents = gFrames[0].healthEvents = 1; After();
    Check(fixture::callbackGapRequests == 0, "complete callback pair needs no deferred registry check");
    fixture::Reset(); fixture::Enter(f); CopyInput(&f.data, f.process);
    gFrames[0].hitEvents = 2; After();
    Check(fixture::callbackGapRequests == 1 && fixture::callbackGapHit == 2 && fixture::callbackGapHealth == 0,
        "missing health callback queues exact observed callback counts");
    fixture::Reset(); fixture::Enter(f); CopyInput(&f.data, f.process);
    gFrames[0].healthEvents = 3; After();
    Check(fixture::callbackGapRequests == 1 && fixture::callbackGapHit == 0 && fixture::callbackGapHealth == 3,
        "missing hit callback queues exact observed callback counts");
    fixture::Reset(); fixture::Enter(f); CopyInput(&f.data, f.process);
    gFrames[0].tainted = true; After();
    Check(fixture::callbackGapRequests == 0, "tainted copied transaction cannot request callback repair");
    fixture::Reset(); fixture::Enter(f); CopyInput(&f.data, f.process);
    gFrames[0].before.valid = false; After();
    Check(fixture::callbackGapRequests == 0, "invalid transaction input cannot request callback repair");
    fixture::Reset(); fixture::Enter(f); CopyInput(&f.data, f.process);
    gFrames[0].thread = GetCurrentThreadId() + 1; After();
    Check(fixture::callbackGapRequests == 0, "foreign-thread copied transaction cannot request callback repair");

    fixture::Reset(); gDetailed = kDetailCalls; fixture::Enter(f);
    Check(CopyInput(&f.data, f.process).valid && !gFrames[0].detail,
        "copy scope survives whole-call log budget");
    After();

    fixture::Reset(); fixture::Enter(f);
    nvo::hit::Data identical = f.data; fixture::Register(&identical, sizeof(identical));
    auto rejected = CopyInput(&identical, f.process);
    Check(!rejected.valid && rejected.identityMatch && !rejected.exactInput,
        "identical content at another pointer does not bind");
    auto* saved = f.data.source; f.data.source = f.other;
    Check(!CopyInput(&f.data, f.process).identityMatch, "changed source rejected"); f.data.source = saved;
    saved = f.data.target; f.data.target = f.other;
    Check(!CopyInput(&f.data, f.process).identityMatch, "changed target rejected"); f.data.target = saved;
    saved = f.data.carrier; f.data.carrier = f.other;
    Check(!CopyInput(&f.data, f.process).identityMatch, "changed carrier rejected"); f.data.carrier = saved;
    saved = f.data.weapon; f.data.weapon = f.other;
    Check(!CopyInput(&f.data, f.process).identityMatch, "changed weapon rejected"); f.data.weapon = saved;
    rejected = CopyInput(&f.data, f.other);
    Check(!rejected.valid && rejected.exactInput && !rejected.processMatch,
        "foreign process rejected despite exact input");
    Check(!CopyInput(nullptr, f.process).valid, "missing copy input rejected");
    gMainThread = GetCurrentThreadId() + 1;
    Check(!CopyInput(&f.data, f.process).valid, "foreign-thread scope rejected");
    gMainThread = GetCurrentThreadId();
    After();

    fixture::Reset(); fixture::Enter(f); first = CopyInput(&f.data, f.process);
    auto foreign = first; ++foreign.generation;
    Check(!IsCurrent(foreign), "different generation cannot be current");
    foreign = first; ++foreign.id;
    Check(!IsCurrent(foreign), "different transaction cannot be current");
    foreign = first; ++foreign.session;
    Check(!IsCurrent(foreign), "different session cannot be current");
    nvo::transaction::QueueCapture(gSession);
    Check(!gActive && !IsCurrent(first), "queue invalidates active copy before reactivation");
    gPending = false; gActive = true; gOpen = 0; gReturns = 0;
    Check(Current() == nullptr && !CopyInput(&f.data, f.process).valid
        && !nvo::transaction::MatchScope(f.actor, f.source).matched,
        "same-session new generation rejects old TLS frame");
    Check(After() == 0x1234 && gOpen == 0 && gReturns == 0 && gDepth == 0,
        "old-generation continuation unwinds without changing new counters");
    Check(fixture::callbackGapRequests == 0,
        "old-generation continuation cannot request a callback check for the new session");

    fixture::Reset(); fixture::resetDuringLookup = true;
    Check(!Before(f.actor, &f.data, 0, 0x1234, 0) && gDepth == 0 && gNextId == 0,
        "generation change during unlocked lifetime lookup rejects stale entry");

    fixture::Reset(); fixture::Enter(f); first = CopyInput(&f.data, f.process);
    const auto enclosingScope = MatchScope(f.actor, f.source);
    f.data.flags = 0x100u; f.data.criticalEffect = f.other;
    fixture::Enter(f, 0x5678); second = CopyInput(&f.data, f.process);
    Check(gFrames[1].parent == first.id && second.id != first.id && second.copyOrdinal == 1
        && !IsCurrent(first) && IsCurrent(second), "nested call retains independent copy scope");
    const auto nestedScope = MatchScope(f.actor, f.source);
    Check(nestedScope.matched && nestedScope.id == second.id && nestedScope.id != enclosingScope.id
        && nestedScope.generation == enclosingScope.generation
        && nestedScope.flags == 0x100u && nestedScope.criticalEffectPresent,
        "nested transaction supplies its own entry context");
    Check(After() == 0x5678 && IsCurrent(first), "inner return restores enclosing current scope");
    const auto restoredScope = MatchScope(f.actor, f.source);
    Check(restoredScope.matched && restoredScope.id == enclosingScope.id
        && restoredScope.generation == enclosingScope.generation
        && restoredScope.copiesObserved == enclosingScope.copiesObserved
        && restoredScope.flags == enclosingScope.flags && !restoredScope.criticalEffectPresent,
        "inner return restores enclosing entry context despite current hit data changes");
    f.data = originalData;
    After();

    fixture::Reset();
    for (unsigned i = 0; i < kDepth; ++i) fixture::Enter(f);
    first = CopyInput(&f.data, f.process);
    Check(!Before(f.actor, &f.data, 0, 0x5555, 0) && gDepth == kDepth
        && gOverflow == 1 && gFrames[kDepth - 1].tainted,
        "depth overflow taints enclosing frame without installing another continuation");
    Check(!IsCurrent(first) && !CopyInput(&f.data, f.process).valid,
        "tainted enclosing frame cannot supply a current copy");
    Check(!MatchScope(f.actor, f.source).matched,
        "tainted enclosing frame cannot supply transaction context");
    while (gDepth) After();
    Check(gOpen == 0 && gReturns == kDepth, "all installed overflow-path continuations unwind");

    fixture::Reset(); fixture::Enter(f); gFrames[0].tainted = true;
    fixture::Enter(f);
    Check(gFrames[1].tainted && !CopyInput(&f.data, f.process).valid,
        "tainted parent propagates to nested call");
    After(); After();

    fixture::Reset(); gNextId = (std::numeric_limits<U64>::max)();
    Check(!Before(f.actor, &f.data, 0, 0x1234, 0) && gDepth == 0
        && gNextId == (std::numeric_limits<U64>::max)(), "transaction IDs saturate without reuse");
    fixture::Reset(); fixture::Enter(f); first = CopyInput(&f.data, f.process);
    gFrames[0].copies = (std::numeric_limits<U64>::max)();
    Check(!CopyInput(&f.data, f.process).valid && gFrames[0].tainted
        && gFrames[0].copies == (std::numeric_limits<U64>::max)() && !IsCurrent(first),
        "copy ordinals saturate and taint instead of wrapping");
    After();
    fixture::Reset(); gGeneration = (std::numeric_limits<U64>::max)();
    nvo::transaction::Suspend("fixture");
    Check(!gActive && gGeneration == (std::numeric_limits<U64>::max)(),
        "saturated generation remains inactive and does not wrap");

    fixture::Reset(); f.data.health = std::numeric_limits<float>::quiet_NaN();
    fixture::Enter(f);
    Check(!CopyInput(&f.data, f.process).valid, "invalid provider input cannot yield a valid scope");
    Check(!MatchScope(f.actor, f.source).matched,
        "invalid original provider input cannot supply transaction context");
    After(); f.data.health = 5;
    Check(fixture::unexpectedReads == 0 && !gAttempted && !gInstalled,
        "all reads stayed in fixture memory and no hook installation was attempted");
    std::printf("RESULT checks=%u failures=%u\n", fixture::checks, fixture::failures);
    return fixture::failures ? 1 : 0;
}

// Standalone x86 fixtures of the production AV observer and its actual bridges.
// Engine getters are substituted; fixture reads allow only registered ranges.
// Never calls Initialize/Install/Tick or loads a game/provider/plugin DLL.
#include <Windows.h>
#include <atomic>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <string>
#include <thread>
#include <vector>

namespace fixture {
struct Range { const unsigned char* data{}; std::size_t size{}; std::uintptr_t address{}; };
Range ranges[8]{};
unsigned rangeCount{}, unexpectedReads{}, checks{}, failures{}, oversizedRows{};
void Register(const void* data, std::size_t size, std::uintptr_t address = 0) {
    if (rangeCount == 8) std::abort();
    ranges[rangeCount++] = {static_cast<const unsigned char*>(data), size,
        address ? address : reinterpret_cast<std::uintptr_t>(data)};
}
void Check(bool value, const char* label) {
    ++checks;
    if (!value) { ++failures; std::printf("FAIL %s\n", label); }
}
void Require(bool value) {
    if (!value) { std::puts("FAIL fixture setup"); std::exit(2); }
}
}

// This existing test branch only replaces engine getter calls. The production
// frame bookkeeping, attribution logic, and x86 assembly are compiled here.
#define NVO_AV_OFFLINE_PROBE
#include "../src/ActorValueObserver.cpp"

namespace fixture {
alignas(16) unsigned char targetForm[256]{}, sourceForm[256]{}, process[4]{};
float currentValues[64]{}, damageValues[64]{};
std::vector<std::string> rows;
std::atomic<unsigned> providerCalls{}, getterCalls{};
bool failLog{}, suspendInside{}, switchSession{}, changeIdentity{}, noChange{};
bool readFailure{}, nestedGetter{}, scopeMatch = true;
bool resetInProvider{}, resetInScope{}, resetInSourceRead{}, changeScope{}, emitHealth{};
bool nestAfterRearm{}, staleFrameUnchanged{};
unsigned resetGetterAt{}, getterPasses{}, nestingGoal{}, mockDepth{};
nvo::transaction::Scope transactionScope{};
void* healthArgs[3]{};
void Rearm();
using Route = U32(__thiscall*)(void*, U32, float, void*);
// Byte windows copied from retained 3L runtime-20260916-124233 health trace
// and 3K runtime-20260916-100050 HitMe trace. Aliases below never dereference
// these engine addresses; the bounded reader returns this local fixture data.
const unsigned char healthWindow[] = {
    0x8B,0x4D,0x10,0x51,0xD9,0x45,0xFC,0xD9,0xE0,0x51,0xD9,0x1C,0x24,0x6A,0x10,
    0x8B,0x55,0xF8,0x8B,0x02,0x8B,0x4D,0xF8,0x8B,0x90,0xAC,0x03,0x00,0x00,0xFF,0xD2
};
const unsigned char conditionWindow[] = {
    0x8B,0x53,0x08,0x8B,0x02,0x50,0xD9,0x85,0x70,0xFC,0xFF,0xFF,0xD9,0xE0,0x51,
    0xD9,0x1C,0x24,0x8B,0x8D,0xC4,0xFC,0xFF,0xFF,0x51,0x8B,0x55,0xE8,0x8B,0x02,
    0x8B,0x4D,0xE8,0x8B,0x90,0xAC,0x03,0x00,0x00,0xFF,0xD2
};
const unsigned char conditionLoopWindow[] = {
    0x8B,0x43,0x08,0x8B,0x08,0x51,0xD9,0x85,0x90,0xFC,0xFF,0xFF,0xD9,0xE0,0x51,
    0xD9,0x1C,0x24,0x8B,0x95,0xC4,0xFC,0xFF,0xFF,0x52,0x8B,0x45,0xE8,0x8B,0x10,
    0x8B,0x4D,0xE8,0x8B,0x82,0xAC,0x03,0x00,0x00,0xFF,0xD0
};
void RegisterRoutes() {
    Register(healthWindow, sizeof(healthWindow), 0x0089D80E);
    Register(conditionWindow, sizeof(conditionWindow), 0x0089BDAF);
    Register(conditionLoopWindow, sizeof(conditionLoopWindow), 0x0089BB65);
}

bool Has(const char* value) {
    for (const auto& row : rows) if (row.find(value) != std::string::npos) return true;
    return false;
}
unsigned Count(const char* value) {
    unsigned count{};
    for (const auto& row : rows) if (row.find(value) != std::string::npos) ++count;
    return count;
}
}

bool nvo::log::Write(const char* format, ...) noexcept {
    SetLastError(9001);
    if (fixture::failLog) return false;
    char buffer[4096]{};
    va_list args; va_start(args, format);
    const int length = vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    fixture::Require(length >= 0 && static_cast<std::size_t>(length) < sizeof(buffer));
    // NativeLog has 768 bytes and reserves two bytes for CRLF plus the NUL.
    if (length >= 766) { ++fixture::oversizedRows; return false; }
    fixture::rows.emplace_back(buffer);
    return true;
}
bool nvo::hit::ReadBytes(const void* source, void* destination, std::size_t size) noexcept {
    if (!source || !destination) return false;
    const auto p = reinterpret_cast<std::uintptr_t>(source);
    for (unsigned i = 0; i < fixture::rangeCount; ++i) {
        const auto& range = fixture::ranges[i];
        const auto begin = range.address;
        if (p >= begin && p - begin <= range.size && size <= range.size - (p - begin)) {
            std::memcpy(destination, range.data + (p - begin), size); return true;
        }
    }
    ++fixture::unexpectedReads;
    return false;
}
bool nvo::hit::ReadForm(void* pointer, Form& form) noexcept {
    form = {};
    if (!pointer) return true;
    unsigned char bytes[16]{};
    if (!ReadBytes(pointer, bytes, sizeof(bytes))) return false;
    form.type = bytes[4]; std::memcpy(&form.id, bytes + 12, sizeof(form.id));
    if (pointer == fixture::sourceForm && fixture::resetInSourceRead) {
        fixture::resetInSourceRead = false; fixture::Rearm();
    }
    return true;
}
nvo::transaction::Scope nvo::transaction::MatchScope(void* receiver, void* source) noexcept {
    const auto result = fixture::scopeMatch && receiver == fixture::targetForm && source == fixture::sourceForm
        ? fixture::transactionScope : Scope{};
    if (fixture::resetInScope) { fixture::resetInScope = false; fixture::Rearm(); }
    return result;
}
namespace {
bool ProbeReadValues(void* actor, U32 av, Values& values) noexcept {
    using namespace fixture;
    getterCalls += 2; ++getterPasses;
    Require(actor == targetForm && av < 64);
    if (readFailure) return false;
    if (nestedGetter) {
        nestedGetter = false;
        reinterpret_cast<Route>(EntryBridge)(targetForm, 17, -1, sourceForm);
    }
    nvo::hit::Form form{};
    if (!nvo::hit::ReadForm(actor, form) || !form.id
        || !nvo::hit::ReadBytes(actor, &values.table, 4)
        || !nvo::hit::ReadBytes(targetForm + 0xA4, &values.owner, 4)
        || !nvo::hit::ReadBytes(targetForm + 0x68, &values.process, 4)) return false;
    const auto* kind = Class(values.table);
    if (!kind || values.owner != kind->owner || !values.process) return false;
    values.id = form.id;
    values.effective = values.table == kClasses[1].table && av == 25 ? 45 : av;
    values.current = currentValues[values.effective];
    values.damage = damageValues[values.effective];
    if (resetGetterAt == getterPasses) Rearm();
    return std::isfinite(values.current) && std::isfinite(values.damage);
}
}
namespace fixture {
void ClearCounters() {
    gEntries = gReturns = gOpen = gInvalid = gOverflow = gNested = gDetailed = gLogFailures = 0;
    gScoped = gUnscoped = gRouteVerified = gRouteUnresolved = gHealthEvents = gHealthMismatches = gUnscopedHealth = 0;
    gOtherThread = 0;
}
void Rearm() {
    // Exercise production invalidation, then seed a completed guarded activation.
    // Never call Tick: it checks executable images and real provider hook state.
    nvo::avobserve::QueueCapture(gSession);
    Require(gEpochValid && nvo::capture::Advance(gGeneration));
    gPending = false; gActive = true; ClearCounters();
}
void SetHealthArgs(void* receiver, void* source, float delta) {
    healthArgs[0] = receiver; healthArgs[1] = source;
    U32 bits{}; std::memcpy(&bits, &delta, sizeof(bits));
    healthArgs[2] = reinterpret_cast<void*>(bits);
}
U32 __fastcall MockProvider(void* actor, void*, U32 av, float delta, void*) {
    ++providerCalls; ++mockDepth;
    Require(actor == targetForm && av < 64);
    if (mockDepth < nestingGoal)
        Require(reinterpret_cast<Route>(EntryBridge)(actor, av, delta, sourceForm) == 0xD00DFEED);
    U32 table{}; std::memcpy(&table, targetForm, 4);
    const U32 effective = table == kClasses[1].table && av == 25 ? 45 : av;
    if (!noChange && std::isfinite(delta)) {
        currentValues[effective] += delta; damageValues[effective] += delta;
    }
    if (changeIdentity) {
        const U32 changed = 0xFFAB1234; std::memcpy(targetForm + 12, &changed, 4);
    }
    if (suspendInside) nvo::avobserve::Suspend("mock_reload");
    if (switchSession) { ++gSession; gEntries = gReturns = gOpen = 0; }
    if (changeScope) ++transactionScope.generation;
    if (emitHealth) nvo::avobserve::HealthEvent(actor, healthArgs);
    if (resetInProvider) {
        resetInProvider = false;
        const auto staleGeneration = gFrames[gDepth - 1].generation;
        const auto staleNested = gFrames[gDepth - 1].nested;
        const auto staleTainted = gFrames[gDepth - 1].tainted;
        Rearm();
        if (nestAfterRearm) {
            nestAfterRearm = false;
            Require(reinterpret_cast<Route>(EntryBridge)(actor, av, delta, sourceForm) == 0xD00DFEED);
            staleFrameUnchanged = gDepth == 1 && gFrames[0].generation == staleGeneration
                && gFrames[0].nested == staleNested && gFrames[0].tainted == staleTainted;
        }
    }
    --mockDepth; return 0xD00DFEED;
}
void Reset(unsigned kind = 0) {
    Require(!gDepth && !mockDepth);
    rows.clear(); gActive = true; gPending = false; gEpochValid = true; gGeneration = 30;
    ++gSession; scopeMatch = true; gNextId = 0; ClearCounters();
    providerCalls = getterCalls = 0; nestingGoal = getterPasses = resetGetterAt = 0;
    unexpectedReads = oversizedRows = 0;
    failLog = suspendInside = switchSession = changeIdentity = noChange = readFailure = nestedGetter = false;
    resetInProvider = resetInScope = resetInSourceRead = changeScope = emitHealth = false;
    nestAfterRearm = staleFrameUnchanged = false;
    transactionScope = {88, gSession, true, 9, 71, 2, 0x300, 0x400, 0x500, 4, 0x3D, true, false};
    gOriginal = reinterpret_cast<void*>(MockProvider);
    rangeCount = 0; Register(targetForm, sizeof(targetForm)); Register(sourceForm, sizeof(sourceForm));
    Register(process, sizeof(process));
    Register(healthArgs, sizeof(healthArgs));
    for (unsigned i = 0; i < 64; ++i) { currentValues[i] = 10000; damageValues[i] = 0; }
    std::memcpy(targetForm, &kClasses[kind].table, 4);
    std::memcpy(targetForm + 0xA4, &kClasses[kind].owner, 4);
    U32 id = 0xFF001978; std::memcpy(targetForm + 12, &id, 4);
    targetForm[4] = kind == 1 ? 0x3C : 0x3B;
    id = 0x14; std::memcpy(sourceForm + 12, &id, 4); sourceForm[4] = 0x3B;
    void* processPointer = process; std::memcpy(targetForm + 0x68, &processPointer, 4);
    SetHealthArgs(targetForm, sourceForm, -12.5f);
}
U32 Call(U32 av = 16, float delta = -12.5f, void* source = sourceForm) {
    return reinterpret_cast<Route>(EntryBridge)(targetForm, av, delta, source);
}
void CallAt(std::uintptr_t caller, U32 av = 16, float delta = -12.5f, void* source = sourceForm) {
    const bool observed = Before(targetForm, av, delta, source, caller);
    Require(MockProvider(targetForm, nullptr, av, delta, source) == 0xD00DFEED);
    if (observed) Require(After() == caller);
}
}

// The fixture's ABI probe below is retained from the historical Packet3K probe.
// It checks the actual production EntryBridge and ReturnBridge with a synthetic
// provider, including incoming DF and outgoing flags, stack, GPRs and FX state.
using fixture::targetForm;
using fixture::sourceForm;
alignas(16) unsigned char expectedEntryFx[512]{}, actualEntryFx[512]{}, expectedExitFx[512]{}, actualExitFx[512]{};
U32 entrySource{};
U32 entryFlags{}, exitFlags{}, entryEax{}, entryEcx{}, entryEdx{}, entryArg{}, entryInput{}, entryEsp{};
U32 exitEax{}, exitEcx{}, exitEdx{}, beforeEsp{}, afterEsp{};
U32 savedRootSp{}, savedRootFx{};
__declspec(naked) void AbiProvider() {
    __asm {
        fxsave actualEntryFx
        pushfd
        pop entryFlags
        mov entryEax,eax
        mov entryEcx,ecx
        mov entryEdx,edx
        mov entryEsp,esp
        mov eax,[esp+4]
        mov entryInput,eax
        mov eax,[esp+8]
        mov entryArg,eax
        mov eax,[esp+12]
        mov entrySource,eax
        cld
        fninit
        fldpi
        pxor xmm0,xmm0
        mov eax,0DEADBEEFh
        mov ecx,012345678h
        mov edx,087654321h
        fxsave expectedExitFx
        push 0247h
        popfd
        ret 12
    }
}
__declspec(naked) void AbiProbe() {
    __asm {
        pushfd
        pushad
        mov savedRootSp,esp
        sub esp,528
        and esp,-16
        mov savedRootFx,esp
        fxsave [esp]
        fninit
        fld1
        pcmpeqd xmm0,xmm0
        push 03F80h
        ldmxcsr [esp]
        add esp,4
        fxsave expectedEntryFx
        mov beforeEsp,esp
        push offset sourceForm
        push 0C1480000h
        push 16
        mov eax,013579BDFh
        mov ecx,offset targetForm
        mov edx,02468ACE0h
        push 0646h
        popfd
        call EntryBridge
        fxsave actualExitFx
        pushfd
        pop exitFlags
        mov exitEax,eax
        mov exitEcx,ecx
        mov exitEdx,edx
        mov afterEsp,esp
        cld
        mov eax,savedRootFx
        fxrstor [eax]
        mov esp,savedRootSp
        popad
        popfd
        ret
    }
}

int main() {
    using namespace fixture;
    static_assert(sizeof(void*) == 4, "Production AV bridge checks require x86.");
    gMainThread = GetCurrentThreadId();
    for (unsigned kind = 0; kind < 3; ++kind) {
        Reset(kind);
        for (U32 av : {16u, 25u, 26u, 27u, 28u, 29u, 30u, 31u})
            Check(Call(av) == 0xD00DFEED, "original provider return preserved for watched AV");
        Check(gEntries == 8 && gReturns == 8 && !gDepth && !gOpen && !gInvalid && providerCalls == 8,
            "three supported classes preserve exact-once call and return bookkeeping");
        Check(Has("net_current=-12.5 net_damage=-12.5 valid=1") && Has("tx=88 scope_match=1"),
            "synthetic getter deltas and transaction link survive production bridge");
        Check(!unexpectedReads, "sampled calls only read registered synthetic memory");
        if (kind == 1) Check(Has("av=25 effective_av=45"), "synthetic creature condition remap is retained");
    }
    Reset(); noChange = true; Call();
    Check(Has("net_current=0 net_damage=0 valid=1"), "zero provider change is observed without invented damage");
    Reset(); scopeMatch = false; Call();
    Check(Has("tx=0 scope_match=0"), "unscoped call does not invent transaction association");
    Reset(); nestingGoal = 20; Call(16, -1);
    Check(providerCalls == 20 && gEntries == 16 && gReturns == 16 && gOverflow == 4 && !gDepth && !gOpen,
        "over-depth calls pass through once and recorded continuations unwind");
    Check(gInvalid == 16 && Has("tainted=1"), "overflow taints every enclosing sampled interval");
    Reset(); nestingGoal = 2; Call(16, -1);
    Check(Has("net_current=-2 net_damage=-2 valid=1 nested=1"), "nested interval records inclusive net measurement");
    Check(providerCalls == 2 && !gDepth && !gOpen, "nested providers are each called once");
    Reset(); failLog = true;
    for (unsigned i = 0; i < 300; ++i) Call(16, -1);
    Check(gEntries == 300 && gReturns == 300 && providerCalls == 300 && gDetailed == 96
        && gLogFailures == 384 && !gOpen && !gDepth,
        "detail limit and log failure do not change provider calls or frame bookkeeping");
    Reset(); suspendInside = true; Call();
    Check(!gActive && !gDepth && providerCalls == 1, "suspend preserves pending original continuation");
    Reset(); switchSession = true; Call();
    Check(!gDepth && !gOpen && !gReturns && providerCalls == 1, "old-session return cannot update new capture counters");
    Reset(); gActive = false; Call();
    Check(!gDepth && !gEntries && !getterCalls && providerCalls == 1, "inactive bridge passes through with no reads");
    Reset(); readFailure = true; Call();
    Check(gInvalid == 1 && providerCalls == 1 && !gDepth, "failed getter invalidates observation and preserves original call");
    Reset(); changeIdentity = true; Call();
    Check(gInvalid == 1 && getterCalls == 2 && providerCalls == 1, "changed actor identity refuses post-provider getter");
    Reset(); nestedGetter = true; Call(16, -1);
    Check(gInvalid == 1 && providerCalls == 2 && !gDepth, "getter reentrancy taints interval while both calls survive");
    Reset();
    for (U32 av : {17u, 24u, 32u}) Call(av, -1);
    Call(16, 0); Call(16, 1); Call(16, std::numeric_limits<float>::quiet_NaN());
    std::thread foreign([] { Call(16, -1); }); foreign.join();
    Check(providerCalls == 7 && !getterCalls && !gEntries && gOtherThread == 1,
        "unwatched positive nonfinite and foreign-thread calls never sample getters");
    Reset(); SetLastError(8123); Call();
    Check(GetLastError() == 8123, "observer preserves Win32 error despite diagnostic logger mutation");

    using AttributionRoute = nvo::attribution::Route;
    using Witness = nvo::attribution::Witness;
    Reset(); RegisterRoutes();
    const auto healthRoute = ReadRoute(0x0089D82D, 16);
    const auto conditionRoute = ReadRoute(0x0089BDD8, 25);
    const auto conditionLoopRoute = ReadRoute(0x0089BB8E, 31);
    Check(healthRoute.route == AttributionRoute::HealthHelper && healthRoute.witness == Witness::Verified,
        "retained health window verifies the precise helper caller");
    Check(conditionRoute.route == AttributionRoute::HitCondition && conditionRoute.witness == Witness::Verified,
        "retained condition window verifies its precise caller");
    Check(conditionLoopRoute.route == AttributionRoute::HitCondition && conditionLoopRoute.witness == Witness::Verified,
        "retained condition loop window verifies its precise caller");
    Check(ReadRoute(0x0089D82D, 25).witness == Witness::ArgumentMismatch
        && ReadRoute(0x0089BDD8, 16).witness == Witness::ArgumentMismatch
        && ReadRoute(0x0089BB8E, 24).witness == Witness::ArgumentMismatch,
        "known callers with wrong AV arguments remain unresolved");
    Check(ReadRoute(0x00123456, 16).route == AttributionRoute::Unclassified
        && ReadRoute(0x00123456, 16).witness == Witness::UnknownCaller && !unexpectedReads,
        "unknown caller is unresolved without any route memory read");
    Reset();
    Check(ReadRoute(0x0089D82D, 16).witness == Witness::BytesUnavailable && unexpectedReads == 1,
        "known caller with unavailable bytes is unresolved");
    Reset(); unsigned char changedWindow[sizeof(healthWindow)]{};
    std::memcpy(changedWindow, healthWindow, sizeof(changedWindow)); changedWindow[0] ^= 1;
    Register(changedWindow, sizeof(changedWindow), 0x0089D80E);
    Check(ReadRoute(0x0089D82D, 16).witness == Witness::BytesMismatch && !unexpectedReads,
        "one changed route instruction byte refuses verified label");
    Reset(); Register(healthWindow, sizeof(healthWindow) - 1, 0x0089D80E);
    Check(ReadRoute(0x0089D82D, 16).witness == Witness::BytesUnavailable && unexpectedReads == 1,
        "partial caller window cannot be accepted by bounded reader");
    Reset(); RegisterRoutes(); emitHealth = true; CallAt(0x0089D82D);
    Check(gRouteVerified == 1 && gScoped == 1 && gHealthEvents == 1 && !gHealthMismatches
        && providerCalls == 1 && !gDepth && !gOpen && !unexpectedReads,
        "verified helper call joins matching callback and scope without duplicate provider execution");
    Check(Has("tx=88 tx_generation=9 copies_seen=2 lifetime=71 carrier=00000300 carrier_type=3D carrier_kind=projectile")
        && Has("route=health_helper_call route_witness=verified_window")
        && Has("health_callbacks=1 callback_mismatches=0"),
        "attribution rows retain original scalar context and independently witnessed route");
    Check(Has("component_verified=0 application_verified=0 primary_or_secondary=unresolved")
        && Has("additive_net=0"), "verified diagnostic witnesses never become component application or additive damage authority");
    Reset(); RegisterRoutes(); transactionScope.flags = 0x2004; transactionScope.criticalEffectPresent = true;
    transactionScope.carrierType = 0x33; CallAt(0x0089D82D);
    Check(Has("carrier_kind=other") && Has("explosion_flag=present critical_effect=reference_present")
        && Has("primary_or_secondary=unresolved"),
        "explosion and critical metadata remain context instead of inferred secondary ownership");
    Reset(); Call();
    Check(gRouteUnresolved == 1 && Has("route=unclassified_call route_witness=unknown_caller"),
        "real fixture bridge return address remains an unknown engine route");
    Reset(); changeScope = true; Call();
    Check(Has("scope_retained=0") && Has("tx_generation=9 copies_seen=2") && gInvalid == 0,
        "same transaction ID with changed generation loses association while original context remains logged");
    Reset(); Call(16, -12.5f, nullptr);
    Check(gUnscoped == 1 && Has("source=00000000") && Has("context=no_matching_hit_scope") && !unexpectedReads,
        "null source remains unscoped without inventing an origin");
    Reset(); Call(16, -12.5f, reinterpret_cast<void*>(0x1234));
    Check(gInvalid == 1 && providerCalls == 1 && unexpectedReads == 1 && Has("tainted=1"),
        "unreadable source taints observation and original provider still executes once");

    Reset(); Require(Before(targetForm, 16, -12.5f, sourceForm, 0x1234));
    nvo::avobserve::HealthEvent(targetForm, healthArgs);
    nvo::avobserve::HealthEvent(targetForm, healthArgs);
    Check(gFrames[0].healthEvents == 2 && gHealthEvents == 2 && !unexpectedReads,
        "two actual callback observations are retained without synthesizing applications");
    Check(After() == 0x1234 && Has("health_callbacks=2 callback_mismatches=0") && Has("application_verified=0"),
        "multiple matching callbacks stay a diagnostic count");
    Reset(); Require(Before(targetForm, 16, -12.5f, sourceForm, 0x1234));
    nvo::avobserve::HealthEvent(sourceForm, healthArgs);
    SetHealthArgs(sourceForm, sourceForm, -12.5f); nvo::avobserve::HealthEvent(targetForm, healthArgs);
    SetHealthArgs(targetForm, nullptr, -12.5f); nvo::avobserve::HealthEvent(targetForm, healthArgs);
    for (float delta : {-12.0f, 0.0f, 12.5f, std::numeric_limits<float>::quiet_NaN()}) {
        SetHealthArgs(targetForm, sourceForm, delta); nvo::avobserve::HealthEvent(targetForm, healthArgs);
    }
    nvo::avobserve::HealthEvent(targetForm, nullptr);
    Check(gHealthMismatches == 8 && !gHealthEvents && gFrames[0].healthMismatches == 8 && !unexpectedReads,
        "callback receiver source delta finite sign and readable arguments must all match");
    SetHealthArgs(targetForm, sourceForm, -12.5f);
    std::thread foreignCallback([] { nvo::avobserve::HealthEvent(targetForm, healthArgs); }); foreignCallback.join();
    Check(gHealthMismatches == 8 && !gHealthEvents, "foreign-thread callback cannot join main-thread AV frame");
    SetLastError(4567); nvo::avobserve::HealthEvent(targetForm, healthArgs);
    Check(gHealthEvents == 1 && GetLastError() == 4567 && !unexpectedReads,
        "callback reads exactly three immutable slots and preserves Win32 error");
    Require(After() == 0x1234);
    Reset(); Require(Before(targetForm, 25, -12.5f, sourceForm, 0x1234));
    nvo::avobserve::HealthEvent(targetForm, healthArgs);
    Check(gHealthMismatches == 1 && !gHealthEvents, "health callback cannot join condition interval");
    Require(After() == 0x1234);
    Reset(); nvo::avobserve::HealthEvent(targetForm, reinterpret_cast<void*>(0x1234));
    Check(gUnscopedHealth == 1 && !unexpectedReads, "out-of-frame callback is unresolved before reading arguments");
    Reset(); Require(Before(targetForm, 16, -12.5f, sourceForm, 0x1234)); gFrames[0].tainted = true;
    nvo::avobserve::HealthEvent(targetForm, healthArgs);
    Check(gHealthMismatches == 1 && !gHealthEvents, "tainted frame cannot claim callback association");
    Require(After() == 0x1234);

    for (unsigned pass : {1u, 2u}) {
        Reset(); resetGetterAt = pass; const auto oldGeneration = gGeneration; Call();
        Check(gGeneration != oldGeneration && gActive && gEpochValid && providerCalls == 1 && !gDepth
            && !gEntries && !gReturns && !gOpen && !gInvalid && !gScoped && !gRouteUnresolved,
            "same-session generation cancellation during either getter preserves new capture counters");
        Check(Count("AV_APPLY_END") == 0 && Count("AV_ATTRIBUTION_END") == 0,
            "cancelled getter interval cannot publish a current end measurement");
    }
    Reset(); resetInProvider = true; Call();
    Check(gActive && !gDepth && !gEntries && !gReturns && !gOpen && !gInvalid && getterCalls == 2 && providerCalls == 1,
        "same-session reset inside provider skips old post-getter and cannot corrupt new counters");
    Reset(); resetInProvider = nestAfterRearm = true;
    Call(16, -12.5f, reinterpret_cast<void*>(0x1234));
    Check(staleFrameUnchanged && Has("call=2 parent=0") && Has("valid=1 nested=0 tainted=0"),
        "fresh nested generation has no stale parent identity taint or nesting mutation");
    Check(providerCalls == 2 && getterCalls == 6 && gEntries == 1 && gReturns == 1 && !gOpen && !gDepth
        && !gInvalid && !gNested && gScoped == 1 && gUnscoped == 0 && unexpectedReads == 1,
        "both providers unwind once while only fresh-generation counters and measurement survive");
    Reset(); Require(Before(targetForm, 16, -12.5f, sourceForm, 0x1234)); Rearm();
    gNextId = (std::numeric_limits<U64>::max)(); Call();
    Check(!gFrames[0].tainted && !gFrames[0].nested && gInvalid == 1 && !gEntries && !gNested,
        "fresh-generation identity exhaustion cannot taint or count stale continuation as nested");
    Require(After() == 0x1234);
    Check(!gDepth && !gOpen && !gReturns && providerCalls == 1,
        "stale continuation unwinds without changing new saturated-generation counters");
    Reset(); gEpochValid = false; resetInScope = true; Call();
    Check(resetInScope && !gEntries && !getterCalls && providerCalls == 1,
        "invalid epoch passes through before even querying transaction context");
    Reset(); resetInScope = true; Call();
    Check(!gEntries && !gReturns && !gOpen && !getterCalls && providerCalls == 1,
        "generation change during scope lookup cancels reservation without suppressing provider");
    Reset(); resetInSourceRead = true; Call();
    Check(!gEntries && !gReturns && !gOpen && !getterCalls && providerCalls == 1,
        "generation change during source read cancels reservation without suppressing provider");
    Reset(); gNextId = (std::numeric_limits<U64>::max)(); Call();
    Check(gNextId == (std::numeric_limits<U64>::max)() && gInvalid == 1 && !gEntries && !gReturns
        && !getterCalls && providerCalls == 1, "saturated AV identity refuses reuse and still calls provider once");
    Reset(); gNextId = (std::numeric_limits<U64>::max)() - 1; Call(); Call();
    Check(gNextId == (std::numeric_limits<U64>::max)() && gEntries == 1 && gReturns == 1 && gInvalid == 1
        && providerCalls == 2, "last representable AV identity is issued once and never wraps");
    Reset(); gGeneration = (std::numeric_limits<U64>::max)(); nvo::avobserve::QueueCapture(gSession); Call();
    Check(!gEpochValid && !gActive && !gPending && !gEntries && !getterCalls && providerCalls == 1,
        "saturated lifecycle generation refuses capture reactivation and remains pass-through");
    Reset(); RegisterRoutes(); gGeneration = (std::numeric_limits<U64>::max)();
    gSession = (std::numeric_limits<unsigned>::max)(); gNextId = (std::numeric_limits<U64>::max)() - 1;
    transactionScope.id = transactionScope.generation = transactionScope.lifetime = transactionScope.copiesObserved
        = (std::numeric_limits<U64>::max)();
    transactionScope.session = gSession;
    transactionScope.carrier = transactionScope.weapon = transactionScope.ammo = transactionScope.flags = 0xFFFFFFFF;
    transactionScope.carrierType = 0xFF; transactionScope.criticalEffectPresent = true;
    CallAt(0x0089D82D); Summary("fixture_maximum_fields");
    Check(!oversizedRows && !gLogFailures && Count("AV_ATTRIBUTION_BEGIN") == 1 && Count("AV_ATTRIBUTION_END") == 1,
        "maximum scalar widths fit the real NativeLog line capacity");

    Reset(); gOriginal = reinterpret_cast<void*>(AbiProvider); AbiProbe();
    Check(entryEax == 0x13579BDF && entryEcx == reinterpret_cast<U32>(targetForm) && entryEdx == 0x2468ACE0,
        "actual x86 entry bridge preserves incoming volatile GPRs");
    Check(entryInput == 16 && entryArg == 0xC1480000 && entrySource == reinterpret_cast<U32>(sourceForm),
        "actual x86 entry bridge preserves thiscall stack arguments");
    Check(entryEsp == beforeEsp - 16 && beforeEsp == afterEsp, "actual x86 bridges preserve stack and callee cleanup");
    Check((entryFlags & 0xCD5) == (0x646 & 0xCD5), "actual x86 entry bridge preserves incoming flags including DF");
    Check(exitEax == 0xDEADBEEF && exitEcx == 0x12345678 && exitEdx == 0x87654321,
        "actual x86 return bridge preserves provider return GPRs");
    Check((exitFlags & 0xCD5) == (0x247 & 0xCD5), "actual x86 return bridge preserves provider flags");
    Check(std::memcmp(expectedEntryFx, actualEntryFx, 416) == 0, "actual x86 entry bridge preserves x87 SSE and MXCSR");
    Check(std::memcmp(expectedExitFx, actualExitFx, 416) == 0, "actual x86 return bridge preserves x87 SSE and MXCSR");
    Check(gEntries == 1 && gReturns == 1 && !gDepth && !gOpen && !unexpectedReads,
        "actual x86 ABI probe returns through one balanced synthetic interval");
    std::printf("AV attribution checks: %u passed, %u failed\n", checks - failures, failures);
    std::puts("game_or_plugin_dll_loaded=false hooks_installed=false getter_values=synthetic");
    return failures ? 1 : 0;
}

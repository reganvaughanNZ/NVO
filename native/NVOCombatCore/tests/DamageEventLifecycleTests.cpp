// Standalone x86 checks of the production callback lifecycle implementation.
// The provider module, event manager, forms and arguments are synthetic.
// Never loads a DLL, queries a real game module, installs hooks or runs a game.
#include <Windows.h>
#include <cstdint>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwchar>
#include <limits>
#include <string>
#include <vector>

namespace fixture {
struct Range { const unsigned char* data{}; std::size_t size{}; };
Range ranges[16]{};
unsigned rangeCount{}, checks{}, failures{}, unexpectedReads{}, moduleQueries{};
unsigned setCalls{}, firstCalls{}, removeCalls{}, resultCalls{}, unusedCalls{};
unsigned transactionHitCalls{}, transactionHealthCalls{}, avHealthCalls{};
bool modulePresent = true;
unsigned char module[0x400]{};
std::vector<std::string> logs;
HMODULE WINAPI ModuleHandle(LPCWSTR name) noexcept;
void Check(bool value, const char* label) {
    ++checks;
    if (!value) { ++failures; std::printf("FAIL %s\n", label); }
}
void Require(bool value) {
    if (!value) { std::puts("FAIL fixture setup"); std::exit(2); }
}
void Register(const void* data, std::size_t size) {
    Require(rangeCount < 16);
    ranges[rangeCount++] = {static_cast<const unsigned char*>(data), size};
}
}

// Only this Windows module lookup is replaced. The real ProviderMatches and
// every lifecycle/callback body remain in this production translation unit.
#define GetModuleHandleW fixture::ModuleHandle
#include "../src/DamageEvents.cpp"
#undef GetModuleHandleW

bool nvo::log::Write(const char* format, ...) noexcept {
    char text[2048]{};
    va_list args;
    va_start(args, format);
    const int count = vsnprintf(text, sizeof(text), format, args);
    va_end(args);
    fixture::Require(count >= 0 && static_cast<std::size_t>(count) < sizeof(text));
    fixture::logs.emplace_back(text);
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
            std::memcpy(destination, source, size);
            return true;
        }
    }
    ++fixture::unexpectedReads;
    return false;
}
bool nvo::hit::ReadForm(void* form, Form& out) noexcept {
    out = {};
    if (!form) return true;
    unsigned char bytes[16]{};
    if (!ReadBytes(form, bytes, sizeof(bytes))) return false;
    out.type = bytes[4];
    std::memcpy(&out.id, bytes + 12, sizeof(out.id));
    return true;
}
void nvo::transaction::HitEvent(void*, void*) noexcept { ++fixture::transactionHitCalls; }
void nvo::transaction::HealthEvent(void*, void*) noexcept { ++fixture::transactionHealthCalls; }
void nvo::avobserve::HealthEvent(void*, void*) noexcept { ++fixture::avHealthCalls; }

namespace fixture {
using Handler = nvo::observer::Handler;
struct Entry { Handler handler{}; bool removed{}; };
struct Event { std::vector<Entry> entries; bool refuse{}; };
Event events[2];
enum class DuringSet { None, Suspend, Queue, ThreadQueue, NestedTick };
DuringSet duringSet = DuringSet::None;
unsigned nextSession{};
nvo::observer::EventApiPrefix api{};

unsigned Index(const char* name) {
    if (std::strcmp(name, "ITR:OnPreHitDamage") == 0) return 0;
    if (std::strcmp(name, "ITR:OnPreHealthDamage") == 0) return 1;
    Require(false); return 0;
}
void __cdecl Peer(void*, void*) {}
DWORD WINAPI QueueThread(void*) {
    nvo::damage::QueueCapture("fixture_thread", nextSession);
    return 0;
}
DWORD WINAPI ForeignTickThread(void*) {
    nvo::damage::QueueCheck(1, 500, 0, 0);
    nvo::damage::Tick();
    return 0;
}
bool __cdecl Set(const char* name, Handler handler) {
    ++setCalls;
    const auto action = duringSet;
    duringSet = DuringSet::None;
    if (action == DuringSet::Suspend) nvo::damage::Suspend("fixture_reentrant");
    else if (action == DuringSet::Queue) nvo::damage::QueueCapture("fixture_reentrant", nextSession);
    else if (action == DuringSet::NestedTick) nvo::damage::Tick();
    else if (action == DuringSet::ThreadQueue) {
        HANDLE thread = CreateThread(nullptr, 0, QueueThread, nullptr, 0, nullptr);
        Require(thread != nullptr);
        // A held production lifecycle lock would deadlock this bounded join.
        Require(WaitForSingleObject(thread, 5000) == WAIT_OBJECT_0);
        Require(CloseHandle(thread) != FALSE);
    }
    auto& event = events[Index(name)];
    if (event.refuse) return false;
    for (auto& entry : event.entries) if (entry.handler == handler) {
        if (!entry.removed) return false;
        entry.removed = false;
        return true;
    }
    event.entries.push_back({handler, false});
    return true;
}
bool __cdecl Remove(const char* name, Handler handler) {
    ++removeCalls;
    for (auto& entry : events[Index(name)].entries) if (entry.handler == handler && !entry.removed) {
        entry.removed = true;
        return true;
    }
    return false;
}
bool __cdecl First(const char* name, Handler handler, int priority, void** scripts, std::uint32_t scriptCount,
    const char** plugins, std::uint32_t pluginCount, const char** handlers, std::uint32_t handlerCount) {
    ++firstCalls;
    Require(priority == 1 && !scripts && !scriptCount && !plugins && !pluginCount && !handlers && !handlerCount);
    for (const auto& entry : events[Index(name)].entries)
        if (!entry.removed) return entry.handler == handler;
    return false;
}
void __cdecl Value(nvo::observer::FormResult&) { ++resultCalls; }
void __cdecl Unused() { ++unusedCalls; }
HMODULE WINAPI ModuleHandle(LPCWSTR name) noexcept {
    ++moduleQueries;
    Require(std::wcscmp(name, L"itr-nvse.dll") == 0);
    return modulePresent ? reinterpret_cast<HMODULE>(module) : nullptr;
}
void MakeModule() {
    std::memset(module, 0, sizeof(module));
    IMAGE_DOS_HEADER dos{};
    dos.e_magic = IMAGE_DOS_SIGNATURE; dos.e_lfanew = 0x80;
    IMAGE_NT_HEADERS32 nt{};
    nt.Signature = IMAGE_NT_SIGNATURE;
    nt.FileHeader.Machine = IMAGE_FILE_MACHINE_I386;
    nt.FileHeader.TimeDateStamp = 0x6A948FDD;
    nt.OptionalHeader.Magic = IMAGE_NT_OPTIONAL_HDR32_MAGIC;
    nt.OptionalHeader.SizeOfImage = 0xB3000;
    std::memcpy(module, &dos, sizeof(dos));
    std::memcpy(module + 0x80, &nt, sizeof(nt));
    rangeCount = 0;
    Register(module, sizeof(module));
}
void Flush() { for (auto& event : events) event.entries.clear(); }
void MarkRemoved() { for (auto& event : events) for (auto& entry : event.entries) entry.removed = true; }
void Drain() {
    for (auto& event : events) {
        auto& entries = event.entries;
        for (auto it = entries.begin(); it != entries.end();)
            if (it->removed) it = entries.erase(it); else ++it;
    }
}
unsigned ListenerCount(unsigned index) {
    unsigned count{};
    for (const auto& entry : events[index].entries) if (!entry.removed) ++count;
    return count;
}
bool LogHas(const char* first, const char* second = "") {
    for (const auto& row : logs)
        if (row.find(first) != std::string::npos && row.find(second) != std::string::npos) return true;
    return false;
}
unsigned LogCount(const char* text) {
    unsigned count{};
    for (const auto& row : logs) if (row.find(text) != std::string::npos) ++count;
    return count;
}
void Reset() {
    nvo::damage::Suspend("fixture_reset");
    Flush();
    for (auto& event : events) event.refuse = false;
    duringSet = DuringSet::None;
    modulePresent = true;
    MakeModule();
    api = {};
    for (auto& unused : api.unused) unused = Unused;
    for (auto& unused : api.unusedAfter) unused = Unused;
    for (auto& unused : api.unusedPriority) unused = Unused;
    api.SetNativeEventHandler = Set;
    api.RemoveNativeEventHandler = Remove;
    api.SetNativeHandlerFunctionValue = Value;
    api.IsEventHandlerFirst = First;
    nvo::damage::Initialize(&api, nullptr);
    setCalls = firstCalls = moduleQueries = transactionHitCalls = transactionHealthCalls = avHealthCalls = 0;
    logs.clear();
}
void Tick(unsigned count = 1) { while (count--) nvo::damage::Tick(); }
void Start(unsigned session = 1) {
    nvo::damage::QueueCapture("fixture_start", session);
    Tick();
}
void* Packed(float value) {
    std::uintptr_t bits{};
    std::memcpy(&bits, &value, sizeof(bits));
    return reinterpret_cast<void*>(bits);
}
struct Arguments {
    unsigned char target[16]{}, source[16]{}, weapon[16]{};
    float hitMultiplier = 17.25f, healthMultiplier = 29.5f;
    void* hit[6]{};
    void* health[4]{};
    Arguments() {
        target[4] = source[4] = 0x3B; weapon[4] = 0x28;
        const std::uint32_t targetId = 0x100, sourceId = 0x14, weaponId = 0x200;
        std::memcpy(target + 12, &targetId, 4);
        std::memcpy(source + 12, &sourceId, 4);
        std::memcpy(weapon + 12, &weaponId, 4);
        hit[0] = target; hit[1] = source; hit[2] = weapon;
        hit[3] = Packed(12.5f); hit[4] = nullptr; hit[5] = &hitMultiplier;
        health[0] = target; health[1] = source; health[2] = Packed(-6.25f); health[3] = &healthMultiplier;
        Register(target, sizeof(target)); Register(source, sizeof(source)); Register(weapon, sizeof(weapon));
        // Mutable multiplier argument slots and pointees are intentionally
        // outside all readable ranges. Any attempt to read them is recorded.
        Register(hit, 5 * sizeof(void*)); Register(health, 3 * sizeof(void*));
    }
};
void Emit(unsigned index, void* receiver, void* args) {
    // Explicit test delivery, never a probe dispatched by production code.
    const auto snapshot = events[index].entries;
    for (const auto& entry : snapshot) if (!entry.removed) entry.handler(receiver, args);
}
}

int main() {
    using namespace fixture;
    static_assert(sizeof(void*) == 4, "Production callback checks require x86.");
    static_assert(sizeof(nvo::observer::EventApiPrefix) == 48);
    static_assert(offsetof(nvo::observer::EventApiPrefix, IsEventHandlerFirst) == 44);

    Reset();
    nvo::damage::QueueCapture("fixture_start", 1);
    Check(setCalls == 0 && firstCalls == 0 && moduleQueries == 0 && !gActive,
        "queuing activation makes no registry or provider calls");
    Tick();
    Check(gActive && gSession == 1 && setCalls == 2 && firstCalls == 4 && moduleQueries == 1,
        "initial main-loop check calls first-set-first for both events");
    Check(ListenerCount(0) == 1 && ListenerCount(1) == 1,
        "first activation installs one diagnostic callback per event");
    Check(LogHas("hit_before=unverified hit_set=added_or_revived hit_after=present")
        && LogHas("provider_emission=unverified") && !LogHas("DAMAGE_EVENT_EMISSION"),
        "registry witness is distinct from observed callback emission");
    Tick(); Check(setCalls == 2, "no survival API call at loop one");
    Tick(); Check(setCalls == 4, "first bounded survival check occurs at loop two");
    Tick(29); Check(setCalls == 4, "no additional survival call through loop thirty-one");
    Tick(); Check(setCalls == 6, "second bounded survival check occurs at loop thirty-two");
    Tick(31); Check(setCalls == 6, "no additional survival call through loop sixty-three");
    Tick(); Check(setCalls == 8, "third bounded survival check occurs at loop sixty-four");
    Tick(1000);
    Check(setCalls == 8 && firstCalls == 16 && moduleQueries == 4 && gChecks == 4 && gLoops == 65,
        "scheduled registry and provider costs stop at four checks without counter wrap");
    Check(LogHas("hit_before=present hit_set=unchanged_or_refused hit_after=present") && gActive,
        "false Set on active duplicate retains callback monitoring");
    Check(transactionHitCalls == 0 && transactionHealthCalls == 0 && gHitCalls == 0 && gHealthCalls == 0,
        "registry checks never fabricate callback delivery");

    Reset();
    for (auto& event : events) event.entries.push_back({Peer, false});
    Start(); Tick(2);
    Check(gActive && ListenerCount(0) == 2 && ListenerCount(1) == 2
        && LogHas("hit_before=unverified hit_set=unchanged_or_refused hit_after=unverified"),
        "a competing first listener leaves own duplicate registration unverified and active");
    {
        Arguments args;
        void* hitBefore[6]{}; void* healthBefore[4]{};
        std::memcpy(hitBefore, args.hit, sizeof(hitBefore));
        std::memcpy(healthBefore, args.health, sizeof(healthBefore));
        SetLastError(8123);
        Emit(0, args.target, args.hit); Emit(1, args.target, args.health);
        Check(GetLastError() == 8123, "real callback bodies preserve caller Win32 error state");
        Check(gHitCalls == 1 && gHealthCalls == 1 && transactionHitCalls == 1 && transactionHealthCalls == 1 && avHealthCalls == 1,
            "peer ambiguity does not suppress supplied callback delivery");
        Check(LogHas("DAMAGE_EVENT_EMISSION session=1 stream=pre_hit observed=1")
            && LogHas("DAMAGE_EVENT_EMISSION session=1 stream=pre_health observed=1")
            && LogHas("input_damage=12.5") && LogHas("delta=-6.25"),
            "only supplied callbacks log emission and unpack x86 float bits");
        for (unsigned i = 0; i < 202; ++i) { Emit(0, args.target, args.hit); Emit(1, args.target, args.health); }
        Check(gHitCalls == 203 && gHealthCalls == 203 && gHitRows == 200 && gHealthRows == 200
            && LogCount("DAMAGE_EVENT_EMISSION") == 2 && LogCount("INPUT_LIMIT") == 2,
            "callback totals continue beyond separately bounded detail and first-emission logs");
        Check(std::memcmp(hitBefore, args.hit, sizeof(hitBefore)) == 0
            && std::memcmp(healthBefore, args.health, sizeof(healthBefore)) == 0
            && args.hitMultiplier == 17.25f && args.healthMultiplier == 29.5f && resultCalls == 0,
            "callback arguments multiplier slots and pointees remain untouched");
        nvo::damage::QueueCapture("fixture_reload", 2);
        Emit(0, args.target, args.hit); Emit(1, args.target, args.health);
        Check(!gActive && gHitCalls == 203 && gHealthCalls == 203,
            "queued lifecycle deactivates old callback counters before binding");
        Tick();
        Check(gActive && gSession == 2 && gHitCalls == 0 && gHealthCalls == 0 && gHitRows == 0
            && gHealthRows == 0 && gInvalid == 0 && !LogHas("DAMAGE_EVENT_EMISSION session=2"),
            "new session starts all callback counters at zero without claimed emission");
    }

    Reset(); Start(); MarkRemoved(); Tick(2); Drain();
    Check(ListenerCount(0) == 1 && ListenerCount(1) == 1
        && LogCount("hit_set=added_or_revived") == 2,
        "Set revives deferred-removed callbacks and later drain retains revived entries");
    Reset(); Start(); MarkRemoved(); Drain(); Tick(2);
    Check(ListenerCount(0) == 1 && ListenerCount(1) == 1,
        "survival check readds callbacks already erased by deferred drain");
    Reset(); Start(); Flush(); Tick();
    Check(ListenerCount(0) == 0 && setCalls == 2, "provider flush empties the fixture registry until a bounded check");
    Tick();
    Check(ListenerCount(0) == 1 && ListenerCount(1) == 1 && setCalls == 4,
        "scheduled Set repairs a simulated post-activation provider flush");
    {
        Arguments args; Emit(0, args.target, args.hit); Emit(1, args.target, args.health);
        Check(gHitCalls == 1 && gHealthCalls == 1, "repaired fixture listeners deliver subsequent supplied callbacks");
    }

    Reset(); Start(); Tick(65);
    nvo::damage::QueueCheck(2, 1, 0, 0);
    nvo::damage::QueueCheck(1, 0, 0, 0);
    nvo::damage::QueueCheck(1, 1, 1, 1);
    Tick();
    Check(setCalls == 8 && gGapRequests == 0, "wrong session missing transaction and complete callback pairs do not queue checks");
    Flush();
    nvo::damage::QueueCheck(1, 41, 0, 0);
    nvo::damage::QueueCheck(1, 42, 0, 1);
    Check(setCalls == 8 && firstCalls == 16 && gGapRequests == 1,
        "transaction gap request defers all API work and coalesces while pending");
    Tick();
    Check(setCalls == 10 && ListenerCount(0) == 1 && ListenerCount(1) == 1
        && LogHas("reason=copied_transaction_callback_gap tx=41 tx_hit=0 tx_health=0"),
        "main-loop gap check repairs flush and retains triggering scalar counts");
    nvo::damage::QueueCheck(1, 43, 1, 0); Tick();
    nvo::damage::QueueCheck(1, 44, 0, 1); Tick();
    for (unsigned i = 0; i < 20; ++i) { nvo::damage::QueueCheck(1, 50 + i, 0, 0); Tick(); }
    Check(gGapRequests == 3 && gChecks == 7 && setCalls == 14 && firstCalls == 28 && moduleQueries == 7,
        "session admits at most three gap checks and seven total registry checks");
    Check(LogHas("tx=43 tx_hit=1 tx_health=0") && LogHas("tx=44 tx_hit=0 tx_health=1"),
        "either missing callback stream qualifies without inventing the other");
    Reset(); Start(); Tick(); nvo::damage::QueueCheck(1, 7, 0, 0); Tick();
    Check(gChecks == 2 && setCalls == 4 && gLoops == 2 && gGapRequests == 1,
        "same-loop scheduled and gap checks share one registry attempt");
    nvo::damage::QueueCheck(1, 8, 0, 0); nvo::damage::Suspend("fixture_stop"); Tick(100);
    Check(setCalls == 4 && !gActive && !gCheckPending && !gPending,
        "suspension cancels pending gap work and all subsequent scheduled work");

    Reset(); modulePresent = false; Start(); Tick(100);
    Check(!gActive && setCalls == 0 && firstCalls == 0 && moduleQueries == 1
        && LogHas("DAMAGE_EVENTS_DISABLED reason=itr_build_missing_or_unrecognized"),
        "missing provider refuses activation without registry calls or unbounded retry");
    Reset(); module[0x80 + offsetof(IMAGE_NT_HEADERS32, FileHeader)
        + offsetof(IMAGE_FILE_HEADER, TimeDateStamp)] ^= 1; Start();
    Check(!gActive && setCalls == 0 && firstCalls == 0,
        "mismatched fixture PE timestamp refuses provider identity");
    Reset(); nvo::damage::Initialize(nullptr, nullptr); Start();
    Check(!gActive && setCalls == 0 && moduleQueries == 0
        && LogHas("DAMAGE_EVENTS_DISABLED reason=event_interface_unavailable"),
        "missing event interface refuses activation before provider access");
    Reset(); api.SetNativeEventHandler = nullptr; Start();
    Check(!gActive && firstCalls == 0 && moduleQueries == 0,
        "missing Set entry point refuses activation");
    Reset(); api.IsEventHandlerFirst = nullptr; Start();
    Check(!gActive && setCalls == 0 && moduleQueries == 0,
        "missing positive-witness entry point refuses activation");
    Reset(); api.RemoveNativeEventHandler = nullptr; Start();
    Check(gActive && ListenerCount(0) == 1 && ListenerCount(1) == 1,
        "callback monitoring has no dependency on Remove entry point");
    Reset(); for (auto& event : events) event.refuse = true; Start();
    Check(gActive && ListenerCount(0) == 0 && ListenerCount(1) == 0
        && LogHas("hit_before=unverified hit_set=unchanged_or_refused hit_after=unverified")
        && !LogHas("DAMAGE_EVENT_EMISSION") && !LogHas("DAMAGE_EVENTS_READY"),
        "API refusal remains unverified and never becomes registration or emission success");

    Reset(); duringSet = DuringSet::Suspend; Start(); Tick(100);
    Check(!gActive && setCalls == 1 && firstCalls == 1 && !LogHas("DAMAGE_EVENT_REGISTRY"),
        "reentrant suspension cancels the stale attempt before further API calls or activation");
    Reset(); duringSet = DuringSet::Queue; nextSession = 22; Start(21);
    Check(!gActive && gPending && setCalls == 1 && firstCalls == 1 && !LogHas("DAMAGE_EVENTS_CAPTURE"),
        "reentrant reload preserves the new pending session and cancels stale commit");
    Tick();
    Check(gActive && gSession == 22 && gChecks == 1 && gHitCalls == 0 && gHealthCalls == 0
        && LogHas("DAMAGE_EVENTS_CAPTURE session=22") && !LogHas("DAMAGE_EVENTS_CAPTURE session=21"),
        "pending replacement session binds cleanly after reentrant reload");
    Reset(); duringSet = DuringSet::ThreadQueue; nextSession = 32; Start(31);
    Check(!gActive && gPending && setCalls == 1 && firstCalls == 1,
        "concurrent lifecycle invalidation completes outside the registry call lock and cancels stale activation");
    Tick(); Check(gActive && gSession == 32, "concurrently queued replacement session activates on main tick");
    Reset(); duringSet = DuringSet::NestedTick; Start();
    Check(gActive && gChecks == 1 && setCalls == 2 && firstCalls == 4,
        "reentrant Tick cannot start a nested registry attempt");
    HANDLE thread = CreateThread(nullptr, 0, ForeignTickThread, nullptr, 0, nullptr);
    Require(thread != nullptr); Require(WaitForSingleObject(thread, 5000) == WAIT_OBJECT_0);
    Require(CloseHandle(thread) != FALSE);
    Check(setCalls == 2 && firstCalls == 4 && gGapRequests == 0 && gLoops == 0,
        "foreign thread cannot run Tick or enqueue a transaction gap");
    SetLastError(7123); Tick(2);
    Check(GetLastError() == 7123, "registry Tick preserves caller Win32 error state");

    Reset();
    gGeneration = (std::numeric_limits<unsigned long long>::max)();
    Start(); Tick(100);
    Check(!gActive && !gEpochValid && !gPending && setCalls == 0 && firstCalls == 0,
        "exhausted generation refuses activation without identity reuse");
    Check(unexpectedReads == 0, "all production reads stayed in registered fixture PE forms and immutable argument slots");
    Check(removeCalls == 0 && resultCalls == 0 && unusedCalls == 0,
        "all scenarios avoided Remove dispatch script and native-result APIs");
    std::printf("RESULT checks=%u failures=%u\n", fixture::checks, fixture::failures);
    return fixture::failures ? 1 : 0;
}

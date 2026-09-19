#include "DamageEvents.hpp"
#include "NativeLog.hpp"
#include "HitTransaction.hpp"
#include "ActorValueObserver.hpp"
#include <Windows.h>
#include <cmath>
#include <cstring>

namespace {
constexpr unsigned kLimit = 200;
constexpr char kHitEvent[] = "ITR:OnPreHitDamage";
constexpr char kHealthEvent[] = "ITR:OnPreHealthDamage";
nvo::observer::EventApiPrefix* gApi{};
const nvo::nvse::ConsolePrefix* gConsole{};
SRWLOCK gLock = SRWLOCK_INIT;
class Lock final {
public:
    Lock() noexcept { AcquireSRWLockExclusive(&gLock); }
    ~Lock() { ReleaseSRWLockExclusive(&gLock); }
    Lock(const Lock&) = delete;
    Lock& operator=(const Lock&) = delete;
};
class PreserveError final {
    DWORD value = GetLastError();
public:
    ~PreserveError() { SetLastError(value); }
};
bool gActive{}, gPending{}, gWarned{};
bool gChecking{}, gCheckPending{};
bool gEpochValid{};
unsigned gSession{}, gRequestedSession{};
unsigned gMainThread{}, gLoops{}, gChecks{}, gGapRequests{};
unsigned gGapHit{}, gGapHealth{};
unsigned long long gGeneration{}, gGapTransaction{};
const char* gReason = "unknown";
unsigned long long gHitCalls{}, gHealthCalls{};
unsigned gHitRows{}, gHealthRows{}, gInvalid{};

void Summary(const char* reason) noexcept
{
    nvo::log::Write("DAMAGE_EVENT_SUMMARY session=%u reason=%s hit_callbacks=%llu hit_rows=%u health_callbacks=%llu health_rows=%u invalid=%u registry_checks=%u gap_requests=%u damage_replacement=0 damage_applications=unverified",
        gSession, reason, gHitCalls, gHitRows, gHealthCalls, gHealthRows, gInvalid, gChecks, gGapRequests);
}

bool IsActor(const nvo::hit::Form& form) noexcept
{
    return form.id && (form.type == 0x3B || form.type == 0x3C);
}
float FloatArg(void* packed) noexcept
{
    // ITR PackEventFloatArg sends IEEE float bits in one x86 argument slot.
    // This is not a float pointer and must never be dereferenced.
    const auto bits = reinterpret_cast<std::uintptr_t>(packed);
    float value{};
    static_assert(sizeof(bits) == sizeof(value));
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}
const char* Direction(const nvo::hit::Form& source, std::uint32_t target) noexcept
{
    if (!source.id) return "unknown_source";
    if (!IsActor(source)) return "nonactor_source";
    if (source.id == target) return "self";
    if (source.id == 0x14) return "player_to_actor";
    if (target == 0x14) return "actor_to_player";
    return "actor_to_actor";
}

void __cdecl OnHitInput(void* thisObj, void* params) noexcept
{
    const PreserveError error;
    nvo::transaction::HitEvent(thisObj, params);
    const Lock lock;
    if (!gActive) return;
    ++gHitCalls;
    if (gHitCalls == 1) nvo::log::Write("DAMAGE_EVENT_EMISSION session=%u stream=pre_hit observed=1 damage_replacement=0", gSession);
    if (gHitRows >= kLimit) return;
    ++gHitRows;
    // Intentionally do not read argument 5, the mutable multiplier pointer.
    void* args[5]{};
    nvo::hit::Form target{}, source{}, weapon{};
    bool valid = nvo::hit::ReadBytes(params, args, sizeof(args))
        && args[0] == thisObj
        && nvo::hit::ReadForm(args[0], target) && IsActor(target)
        && nvo::hit::ReadForm(args[1], source)
        && nvo::hit::ReadForm(args[2], weapon)
        && (!args[2] || weapon.type == 0x28);
    const float value = FloatArg(args[3]);
    const auto region = static_cast<std::int32_t>(reinterpret_cast<std::uintptr_t>(args[4]));
    valid = valid && std::isfinite(value) && value > 0;
    if (!valid) {
        ++gInvalid;
        nvo::log::Write("DAMAGE_INPUT_INVALID session=%u seq=%u reason=argument_contract", gSession, gHitRows);
    } else {
        nvo::log::Write("DAMAGE_INPUT session=%u seq=%u tick_ms=%llu provider=ITR20202 phase=pre_hit source=%08X source_type=%02X target=%08X target_type=%02X weapon=%08X region=%d region_kind=%s input_damage=%.6g value_kind=health_or_limb_fallback direction=%s projectile=unknown ammo=unknown damage_applied=unverified",
            gSession, gHitRows, GetTickCount64(), source.id, static_cast<unsigned>(source.type), target.id, static_cast<unsigned>(target.type), weapon.id,
            region, region == 14 ? "weapon" : region == -1 ? "unspecified" : "reported_part",
            static_cast<double>(value), Direction(source, target.id));
    }
    if (gHitRows == kLimit) nvo::log::Write("DAMAGE_INPUT_LIMIT session=%u maximum=%u", gSession, kLimit);
    // Do not call SetNativeHandlerFunctionValue or change any event argument.
    // xNVSE supplies an invalid result; ITR ignores nonnumeric/invalid results.
}

void __cdecl OnHealthInput(void* thisObj, void* params) noexcept
{
    const PreserveError error;
    nvo::transaction::HealthEvent(thisObj, params);
    nvo::avobserve::HealthEvent(thisObj, params);
    const Lock lock;
    if (!gActive) return;
    ++gHealthCalls;
    if (gHealthCalls == 1) nvo::log::Write("DAMAGE_EVENT_EMISSION session=%u stream=pre_health observed=1 damage_replacement=0", gSession);
    if (gHealthRows >= kLimit) return;
    ++gHealthRows;
    // Argument 3 (mutable multiplier) is deliberately not read or written.
    void* args[3]{};
    nvo::hit::Form target{}, source{};
    bool valid = nvo::hit::ReadBytes(params, args, sizeof(args))
        && args[0] == thisObj
        && nvo::hit::ReadForm(args[0], target) && IsActor(target)
        && nvo::hit::ReadForm(args[1], source);
    const float delta = FloatArg(args[2]);
    valid = valid && std::isfinite(delta) && delta < 0;
    if (!valid) {
        ++gInvalid;
        nvo::log::Write("HEALTH_INPUT_INVALID session=%u seq=%u reason=argument_contract", gSession, gHealthRows);
    } else {
        nvo::log::Write("HEALTH_INPUT session=%u seq=%u tick_ms=%llu provider=ITR20202 phase=pre_health source=%08X source_type=%02X target=%08X target_type=%02X delta=%.6g direction=%s cause=unclassified actual_hp_loss=unverified",
            gSession, gHealthRows, GetTickCount64(), source.id, static_cast<unsigned>(source.type), target.id, static_cast<unsigned>(target.type),
            static_cast<double>(delta), Direction(source, target.id));
    }
    if (gHealthRows == kLimit) nvo::log::Write("HEALTH_INPUT_LIMIT session=%u maximum=%u", gSession, kLimit);
}

bool ProviderMatches() noexcept
{
    // Public event ABI, no ITR address calls or memory patches. Restrict this
    // packet to the inspected 2.2.2 module metadata; installer pins full SHA256.
    const auto itr = GetModuleHandleW(L"itr-nvse.dll");
    IMAGE_DOS_HEADER dos{};
    IMAGE_NT_HEADERS32 nt{};
    if (!itr || !nvo::hit::ReadBytes(itr, &dos, sizeof(dos)) || dos.e_magic != IMAGE_DOS_SIGNATURE
        || dos.e_lfanew < 0x40 || dos.e_lfanew > 0x1000) return false;
    return nvo::hit::ReadBytes(reinterpret_cast<const char*>(itr) + dos.e_lfanew, &nt, sizeof(nt))
        && nt.Signature == IMAGE_NT_SIGNATURE && nt.FileHeader.Machine == IMAGE_FILE_MACHINE_I386
        && nt.OptionalHeader.Magic == IMAGE_NT_OPTIONAL_HDR32_MAGIC
        && nt.FileHeader.TimeDateStamp == 0x6A948FDD && nt.OptionalHeader.SizeOfImage == 0xB3000;
}
bool Current(unsigned long long generation) noexcept
{
    const Lock lock;
    return gEpochValid && generation == gGeneration;
}
struct Registration { bool before{}, added{}, after{}; };
Registration Ensure(const char* event, nvo::observer::Handler callback,
    unsigned long long generation) noexcept
{
    Registration r{};
    if (!Current(generation)) return r;
    r.before = gApi->IsEventHandlerFirst(event, callback, 1, nullptr, 0, nullptr, 0, nullptr, 0);
    if (!Current(generation)) return r;
    // xNVSE Set is idempotent: true only adds/revives; an active duplicate
    // returns false. Never remove a healthy handler to "refresh" it.
    r.added = gApi->SetNativeEventHandler(event, callback);
    if (!Current(generation)) return r;
    r.after = gApi->IsEventHandlerFirst(event, callback, 1, nullptr, 0, nullptr, 0, nullptr, 0);
    return r;
}
void Disabled(const char* reason) noexcept
{
    nvo::log::Write("DAMAGE_EVENTS_DISABLED reason=%s damage_replacement=0", reason);
    if (!gWarned && gConsole && gConsole->version >= 2 && gConsole->RunScriptLine) {
        gWarned = true;
        gConsole->RunScriptLine("PrintC \"[NVO] Additional damage diagnostics unavailable. See NVOCombatCore.log.\"", nullptr);
    }
}
}

void nvo::damage::Initialize(nvo::observer::EventApiPrefix* api, const nvo::nvse::ConsolePrefix* console) noexcept
{
    gApi = api;
    gConsole = console;
    gMainThread = GetCurrentThreadId();
}
void nvo::damage::QueueCapture(const char* reason, unsigned session) noexcept
{
    const Lock lock;
    gActive = false;
    gEpochValid = nvo::capture::Advance(gGeneration);
    gPending = gEpochValid;
    gCheckPending = false;
    gReason = reason;
    gRequestedSession = session;
}
void nvo::damage::Suspend(const char* reason) noexcept
{
    const Lock lock;
    gPending = false;
    gCheckPending = false;
    if (gActive) Summary(reason);
    gActive = false;
    gEpochValid = false;
    nvo::capture::Advance(gGeneration);
}
void nvo::damage::QueueCheck(unsigned session, unsigned long long transaction,
    unsigned hitCallbacks, unsigned healthCallbacks) noexcept
{
    const Lock lock;
    if (GetCurrentThreadId() != gMainThread || !gActive || session != gSession
        || !transaction || (hitCallbacks && healthCallbacks) || gCheckPending || gGapRequests >= 3) return;
    ++gGapRequests;
    gCheckPending = true;
    gGapTransaction = transaction; gGapHit = hitCallbacks; gGapHealth = healthCallbacks;
}
void nvo::damage::Tick() noexcept
{
    const PreserveError error;
    if (GetCurrentThreadId() != gMainThread) return;
    unsigned session{};
    unsigned loop{}, gapHit{}, gapHealth{};
    unsigned long long generation{}, transaction{};
    bool initial{};
    const char* reason{};
    {
        const Lock lock;
        if (gChecking || (!gPending && !gActive)) return;
        initial = gPending;
        if (initial) {
            gPending = false;
            session = gRequestedSession;
            reason = gReason;
            gLoops = gChecks = gGapRequests = 0;
            gHitCalls = gHealthCalls = 0;
            gHitRows = gHealthRows = gInvalid = 0;
            gSession = session;
        } else {
            if (gLoops < 65) ++gLoops;
            const bool scheduled = gLoops == 2 || gLoops == 32 || gLoops == 64;
            // Saturate beyond the final scheduled check; never wrap/repeat it.
            if (!gCheckPending && !scheduled) return;
            session = gSession;
            reason = gCheckPending ? "copied_transaction_callback_gap" : "registration_survival";
            if (gCheckPending) {
                transaction = gGapTransaction; gapHit = gGapHit; gapHealth = gGapHealth;
                gCheckPending = false;
            }
        }
        generation = gGeneration;
        loop = gLoops;
        gChecking = true;
    }
    // Public API only, no fabricated damage event and no private provider reads.
    // Outside our lock; reentrant lifecycle changes invalidate this attempt.
    const char* failure = nullptr;
    if (!gApi || !gApi->SetNativeEventHandler || !gApi->IsEventHandlerFirst)
        failure = "event_interface_unavailable";
    else if (!ProviderMatches()) failure = "itr_build_missing_or_unrecognized";
    Registration hit{}, health{};
    if (!failure) {
        hit = Ensure(kHitEvent, OnHitInput, generation);
        health = Ensure(kHealthEvent, OnHealthInput, generation);
    }
    {
    const Lock lock;
    gChecking = false;
    if (!gEpochValid || generation != gGeneration) return;
    if (failure) { gActive = false; }
    else {
    ++gChecks;
    gActive = true;
    nvo::log::Write("DAMAGE_EVENT_REGISTRY session=%u generation=%llu check=%u loop=%u reason=%s tx=%llu tx_hit=%u tx_health=%u hit_before=%s hit_set=%s hit_after=%s health_before=%s health_set=%s health_after=%s hit_callbacks=%llu health_callbacks=%llu provider_emission=unverified observer_writes=0",
        session, generation, gChecks, loop, reason, transaction, gapHit, gapHealth,
        hit.before ? "present" : "unverified", hit.added ? "added_or_revived" : "unchanged_or_refused", hit.after ? "present" : "unverified",
        health.before ? "present" : "unverified", health.added ? "added_or_revived" : "unchanged_or_refused", health.after ? "present" : "unverified", gHitCalls, gHealthCalls);
    if (initial) nvo::log::Write("DAMAGE_EVENTS_CAPTURE session=%u provider=ITR20202 registry_witness=positive_only survival_checks=3 gap_checks_max=3 hit_limit=%u health_limit=%u damage_replacement=0 provider_emission=unverified",
        session, kLimit, kLimit);
    }
    }
    if (failure) Disabled(failure); // Console API must also stay outside gLock.
}

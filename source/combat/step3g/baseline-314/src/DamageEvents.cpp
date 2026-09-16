#include "DamageEvents.hpp"
#include "NativeLog.hpp"
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
unsigned gSession{}, gRequestedSession{};
const char* gReason = "unknown";
unsigned long long gHitCalls{}, gHealthCalls{};
unsigned gHitRows{}, gHealthRows{}, gInvalid{};

void Summary(const char* reason) noexcept
{
    nvo::log::Write("DAMAGE_EVENT_SUMMARY session=%u reason=%s hit_callbacks=%llu hit_rows=%u health_callbacks=%llu health_rows=%u invalid=%u damage_replacement=0 damage_applications=unverified",
        gSession, reason, gHitCalls, gHitRows, gHealthCalls, gHealthRows, gInvalid);
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
    const Lock lock;
    if (!gActive) return;
    ++gHitCalls;
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
    const Lock lock;
    if (!gActive) return;
    ++gHealthCalls;
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
void Unbind() noexcept
{
    if (gApi && gApi->RemoveNativeEventHandler) {
        gApi->RemoveNativeEventHandler(kHitEvent, OnHitInput);
        gApi->RemoveNativeEventHandler(kHealthEvent, OnHealthInput);
    }
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
}
void nvo::damage::QueueCapture(const char* reason, unsigned session) noexcept
{
    const Lock lock;
    gActive = false;
    gPending = true;
    gReason = reason;
    gRequestedSession = session;
}
void nvo::damage::Suspend(const char* reason) noexcept
{
    const Lock lock;
    gPending = false;
    if (gActive) Summary(reason);
    gActive = false;
}
void nvo::damage::Tick() noexcept
{
    unsigned session{};
    const char* reason{};
    {
        const Lock lock;
        if (!gPending) return;
        gPending = false;
        session = gRequestedSession;
        reason = gReason;
    }
    // Keep event API calls outside our lock; callbacks use it too.
    if (!gApi || !gApi->SetNativeEventHandler || !gApi->RemoveNativeEventHandler) {
        Disabled("event_interface_unavailable");
        return;
    }
    Unbind();
    if (!ProviderMatches()) {
        Disabled("itr_build_missing_or_unrecognized");
        return;
    }
    const bool hit = gApi->SetNativeEventHandler(kHitEvent, OnHitInput);
    const bool health = gApi->SetNativeEventHandler(kHealthEvent, OnHealthInput);
    if (!hit || !health) {
        Unbind();
        Disabled("provider_event_registration_failed");
        return;
    }
    const Lock lock;
    gSession = session;
    gHitCalls = gHealthCalls = 0;
    gHitRows = gHealthRows = gInvalid = 0;
    gActive = true;
    nvo::log::Write("DAMAGE_EVENTS_READY session=%u reason=%s provider=ITR20202 handlers=2 hit_limit=%u health_limit=%u observer_writes=0 provider_emission=unverified",
        gSession, reason, kLimit, kLimit);
}

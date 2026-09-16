#include "NativeObserver.hpp"
#include "NativeLog.hpp"
#include "FlightPreview.hpp"
#include <Windows.h>
#include <cstdint>
#include <cstring>
#include <atomic>

namespace {
using U32 = std::uint32_t;
constexpr unsigned kMaxEvents = 600;
constexpr unsigned kMaxContexts = 200;
constexpr unsigned kSlots = 512;
SRWLOCK gLock = SRWLOCK_INIT;
class Lock final {
public:
    Lock() noexcept { AcquireSRWLockExclusive(&gLock); }
    ~Lock() { ReleaseSRWLockExclusive(&gLock); }
    Lock(const Lock&) = delete;
    Lock& operator=(const Lock&) = delete;
};
nvo::observer::EventApiPrefix* gApi{};
const nvo::nvse::ConsolePrefix* gConsole{};
bool gWarned{};
std::atomic<bool> gPending{false};
const char* gReason = "unknown"; // static literals only
bool gActive{};
bool gContextsEnabled{};
unsigned gContexts{}, gContextFailures{}, gLinkedContexts{}, gAmmoContexts{};
unsigned gSession{}, gRows{}, gCreated{}, gImpacts{}, gDestroyed{}, gHits{}, gHitWith{}, gBlasts{};
unsigned gUnmatched{}, gReused{}, gOverflow{}, gReadFailures{};
unsigned long long gNextLifetime{};

struct Life {
    std::uintptr_t address{}; // identity only; never dereferenced after callback
    U32 ref{}, source{}, weapon{}, ammo{};
    unsigned long long serial{};
    unsigned impacts{};
};
Life gLives[kSlots]{};

// Read only live callback-supplied form IDs, not actors' saved lastHitData.
// TESForm::refID is at 0x0C for the supported runtime (pinned GameForms.h).
// Isolate SEH from functions with C++ destructors. Never catch/write game state.
bool ReadId(void* form, U32* out) noexcept
{
    *out = 0;
    if (!form) return true;
    __try {
        std::memcpy(out, static_cast<const char*>(form) + 0x0C, sizeof(*out));
        return true;
    } __except (GetExceptionCode() == EXCEPTION_ACCESS_VIOLATION
        ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) {
        return false;
    }
}
U32 Id(void* form) noexcept
{
    U32 value{};
    if (!ReadId(form, &value)) ++gReadFailures;
    return value;
}
void* Arg(void* params, unsigned index) noexcept
{
    return params ? static_cast<void**>(params)[index] : nullptr;
}
Life* Find(void* form, U32 id) noexcept
{
    const auto address = reinterpret_cast<std::uintptr_t>(form);
    if (!address) return nullptr;
    for (auto& life : gLives)
        if (life.address == address && life.ref == id) return &life;
    return nullptr;
}
void Summary(const char* reason) noexcept
{
    if (!gSession) return;
    unsigned live{};
    for (const auto& life : gLives) if (life.address) ++live;
    nvo::log::Write("SUMMARY session=%u reason=%s rows=%u create=%u impact=%u destroy=%u hit_notice=%u weapon_notice=%u blast=%u unmatched=%u reused_live_address=%u overflow=%u read_failures=%u open_lifetimes=%u",
        gSession, reason, gRows, gCreated, gImpacts, gDestroyed, gHits, gHitWith,
        gBlasts, gUnmatched, gReused, gOverflow, gReadFailures, live);
    nvo::log::Write("CURRENT_HIT_SUMMARY session=%u reason=%s contexts=%u invalid_contexts=%u linked_lifetimes=%u known_ammo=%u damage_applications=unverified",
        gSession, reason, gContexts, gContextFailures, gLinkedContexts, gAmmoContexts);
}
void FinishedRow() noexcept
{
    if (++gRows == kMaxEvents) {
        Summary("capture_limit");
        nvo::log::Write("CAPTURE_LIMIT session=%u maximum=%u reload_to_capture_again=1", gSession, kMaxEvents);
        // Current contexts have their own budget so classic-event spam cannot
        // exhaust the new diagnostic before it records a fresh hit.
    }
}

void __cdecl OnCreate(void* projectile, void* params) noexcept
{
    const Lock lock;
    if (!gActive) return;
    const U32 ref = Id(projectile), source = Id(Arg(params, 0)), weapon = Id(Arg(params, 1));
    const auto serial = ++gNextLifetime;
    Life* slot = nullptr;
    bool replaced = false;
    if (projectile) {
        for (auto& life : gLives) {
            if (life.address == reinterpret_cast<std::uintptr_t>(projectile)) {
                slot = &life; replaced = true; ++gReused; break;
            }
        }
        if (!slot) for (auto& life : gLives) if (!life.address) { slot = &life; break; }
    }
    const U32 ammo = nvo::hit::ProjectileAmmo(projectile, gReadFailures);
    if (slot) *slot = {reinterpret_cast<std::uintptr_t>(projectile), ref, source, weapon, ammo, serial, 0};
    else ++gOverflow;
    ++gCreated;
    if (gRows < kMaxEvents) {
        nvo::log::Write("EVENT session=%u seq=%u CREATE lifetime=%llu projectile=%08X source=%08X weapon=%08X tracked=%u replaced=%u ammo=%08X ammo_known=%u",
            gSession, gRows + 1, serial, ref, source, weapon, slot ? 1u : 0u, replaced ? 1u : 0u, ammo, ammo ? 1u : 0u);
        FinishedRow();
    }
    nvo::flight::Create(projectile, source, weapon, ammo, serial, slot != nullptr);
}
void __cdecl OnImpact(void* projectile, void* params) noexcept
{
    const Lock lock;
    if (!gActive) return;
    const U32 ref = Id(projectile), source = Id(Arg(params, 0)), weapon = Id(Arg(params, 1)), target = Id(Arg(params, 2));
    auto* life = Find(projectile, ref);
    if (life) ++life->impacts; else ++gUnmatched;
    ++gImpacts;
    if (gRows < kMaxEvents) {
        nvo::log::Write("EVENT session=%u seq=%u IMPACT lifetime=%llu projectile=%08X source=%08X weapon=%08X target=%08X matched=%u impact_index=%u origin_source=%08X origin_weapon=%08X region=unknown damage=unknown",
            gSession, gRows + 1, life ? life->serial : 0ull, ref, source, weapon, target, life ? 1u : 0u,
            life ? life->impacts : 0u, life ? life->source : 0u, life ? life->weapon : 0u);
        FinishedRow();
    }
    nvo::flight::EndSample(projectile, life ? life->serial : 0ull, false);
}
void __cdecl OnDestroy(void* projectile, void* params) noexcept
{
    const Lock lock;
    if (!gActive) return;
    const U32 ref = Id(projectile), source = Id(Arg(params, 0)), weapon = Id(Arg(params, 1));
    auto* life = Find(projectile, ref);
    if (!life) ++gUnmatched;
    const auto serial = life ? life->serial : 0ull;
    ++gDestroyed;
    if (gRows < kMaxEvents) {
        nvo::log::Write("EVENT session=%u seq=%u DESTROY lifetime=%llu projectile=%08X source=%08X weapon=%08X matched=%u impacts=%u",
            gSession, gRows + 1, life ? life->serial : 0ull, ref, source, weapon, life ? 1u : 0u, life ? life->impacts : 0u);
        if (life) *life = {};
        FinishedRow();
    } else if (life) *life = {};
    nvo::flight::EndSample(projectile, serial, true);
}
void __cdecl OnBlast(void* explosion, void* params) noexcept
{
    const Lock lock;
    if (!gActive || gRows >= kMaxEvents) return;
    ++gBlasts;
    const U32 ref = Id(explosion), target = Id(Arg(params, 0)), source = Id(Arg(params, 1));
    nvo::log::Write("EVENT session=%u seq=%u BLAST explosion=%08X target=%08X source=%08X projectile_link=unknown damage=unknown",
        gSession, gRows + 1, ref, target, source);
    FinishedRow();
}
void __cdecl OnHit(void*, void* params) noexcept
{
    const Lock lock;
    if (!gActive || gRows >= kMaxEvents) return;
    ++gHits;
    // Classic events pass nullptr as thisObj and {victim, otherForm} in params.
    const U32 target = Id(Arg(params, 0)), attacker = Id(Arg(params, 1));
    nvo::log::Write("EVENT session=%u seq=%u HIT_NOTICE target=%08X attacker=%08X coalesced=1 current_hit_context=0",
        gSession, gRows + 1, target, attacker);
    FinishedRow();
}
void __cdecl OnHitWith(void*, void* params) noexcept
{
    const Lock lock;
    if (!gActive || gRows >= kMaxEvents) return;
    ++gHitWith;
    const U32 target = Id(Arg(params, 0));
    nvo::hit::Form object{};
    if (!nvo::hit::ReadForm(Arg(params, 1), object)) ++gReadFailures;
    nvo::log::Write("EVENT session=%u seq=%u HIT_OBJECT_NOTICE target=%08X hit_object=%08X form_type=%02X coalesced=1 current_hit_context=0",
        gSession, gRows + 1, target, object.id, static_cast<unsigned>(object.type));
    FinishedRow();
}
void __cdecl OnPreCreate(void* actor, void* params) noexcept
{
    const Lock lock;
    if (!gActive || !gApi || !gApi->SetNativeHandlerFunctionValue) return;
    if (auto* value=nvo::flight::SelectProjectile(actor,Arg(params,0),Arg(params,1)))
        gApi->SetNativeHandlerFunctionValue(*value);
}
constexpr char kPreCreate[]="ShowOff:OnPreProjectileCreate";
struct Binding { const char* name; nvo::observer::Handler handler; };
constexpr Binding kBindings[] = {
    {"ShowOff:OnProjectileCreate", OnCreate},
    {"ShowOff:OnProjectileImpact", OnImpact},
    {"ShowOff:OnProjectileDestroy", OnDestroy},
    {"ShowOff:OnExplosionHit", OnBlast},
    {"onhit", OnHit},
    {"onhitwith", OnHitWith}
};
} // namespace

void nvo::observer::Initialize(EventApiPrefix* api, const nvo::nvse::ConsolePrefix* console) noexcept
{
    gApi = api;
    gConsole = console;
}

void nvo::observer::Suspend(const char* reason) noexcept
{
    const Lock lock;
    gPending.store(false);
    if (gActive) Summary(reason);
    gActive = false;
    nvo::flight::Suspend(reason);
    for (auto& life : gLives) life = {};
}

void nvo::observer::QueueCapture(const char* reason) noexcept
{
    const Lock lock;
    gReason = reason;
    nvo::flight::Suspend("capture_requeued");
    gActive = false;
    gPending.store(true);
}

void nvo::observer::Tick() noexcept
{
    if (!gPending.exchange(false)) return; // No per-frame polling of game objects.
    if (!gApi || !gApi->SetNativeEventHandler || !gApi->RemoveNativeEventHandler) {
        nvo::log::Write("OBSERVER_DISABLED reason=event_interface_unavailable damage_replacement=0");
        return;
    }
    // Event API calls must not occur while holding gLock: callbacks also use it.
    // Remove only our own handlers, then bind once after load-time flushes finish.
    gApi->RemoveNativeEventHandler(kPreCreate,OnPreCreate);
    const bool selectorReady=gApi->SetNativeHandlerFunctionValue
        && gApi->SetNativeEventHandler(kPreCreate,OnPreCreate);
    for (const auto& binding : kBindings)
        gApi->RemoveNativeEventHandler(binding.name, binding.handler);
    unsigned registered{};
    for (const auto& binding : kBindings) {
        if (gApi->SetNativeEventHandler(binding.name, binding.handler)) ++registered;
        else nvo::log::Write("OBSERVER_BIND_FAILED event=%s", binding.name);
    }
    if (registered != sizeof(kBindings) / sizeof(kBindings[0])) {
        for (const auto& binding : kBindings)
            gApi->RemoveNativeEventHandler(binding.name, binding.handler);
        nvo::log::Write("OBSERVER_DISABLED registered=%u required=6 reason=missing_events damage_replacement=0", registered);
        return;
    }
    const bool contextsReady = nvo::hit::EnsureInstalled();
    if (!contextsReady && !gWarned) {
        gWarned = true;
        if (gConsole && gConsole->version >= 2 && gConsole->RunScriptLine)
            gConsole->RunScriptLine("PrintC \"[NVO] Current-hit diagnostics unavailable. See NVOCombatCore.log.\"", nullptr);
    }
    {
    const Lock lock;
    ++gSession;
    gRows = gCreated = gImpacts = gDestroyed = gHits = gHitWith = gBlasts = 0;
    gUnmatched = gReused = gOverflow = gReadFailures = 0;
    gContexts = gContextFailures = gLinkedContexts = gAmmoContexts = 0;
    gContextsEnabled = contextsReady;
    for (auto& life : gLives) life = {};
    gActive = true;
    nvo::log::Write("CAPTURE session=%u reason=%s handlers=6 max_events=%u current_hit_observer=%u max_contexts=%u engine_damage_hooks=0 damage_replacement=0",
        gSession, gReason, kMaxEvents, gContextsEnabled ? 1u : 0u, kMaxContexts);
    nvo::flight::BeginCapture(gSession, contextsReady && nvo::hit::ProjectileLayoutReady(),selectorReady);
    }
    nvo::flight::EmitNotice(gConsole);
}

void nvo::observer::CurrentHit(const nvo::hit::Data* input, void* process, const void* caller) noexcept
{
    const Lock lock;
    if (!gActive || !gContextsEnabled || gContexts >= kMaxContexts) return;
    ++gContexts;
    nvo::hit::Data data{};
    nvo::hit::Form source{}, target{}, carrier{}, weapon{};
    void* ownerProcess{};
    bool valid = nvo::hit::ReadBytes(input, &data, sizeof(data))
        && nvo::hit::ReadForm(data.source, source) && nvo::hit::ReadForm(data.target, target)
        && nvo::hit::ReadForm(data.carrier, carrier) && nvo::hit::ReadForm(data.weapon, weapon);
    // Match the receiving process to the supplied actor; loading/foreign copies
    // are not silently promoted to current actor hits.
    valid = valid && (target.type == 0x3B || target.type == 0x3C)
        && nvo::hit::ReadBytes(static_cast<const char*>(data.target) + 0x68, &ownerProcess, sizeof(ownerProcess))
        && process && ownerProcess == process;
    if (!valid) {
        ++gContextFailures;
        nvo::log::Write("HIT_CONTEXT_INVALID session=%u seq=%u reason=read_or_target_process_mismatch",
            gSession, gContexts);
    } else {
        // Lifetime lookup is identity-only. No retained pointer is dereferenced.
        auto* life = nvo::hit::IsProjectile(carrier.type) ? Find(data.carrier, carrier.id) : nullptr;
        const U32 ammo = nvo::hit::ProjectileAmmo(data.carrier, gReadFailures);
        const auto returnAddress = reinterpret_cast<std::uintptr_t>(caller);
        const U32 callerRva = returnAddress >= 0x400000 && returnAddress < 0x147B000
            ? static_cast<U32>(returnAddress - 0x400000) : 0;
        if (life) ++gLinkedContexts;
        if (ammo) ++gAmmoContexts;
        nvo::log::Write("HIT_CONTEXT session=%u seq=%u tick_ms=%llu phase=copy_input source=%08X source_type=%02X target=%08X target_type=%02X weapon=%08X weapon_type=%02X carrier=%08X carrier_type=%02X lifetime=%llu linked=%u ammo=%08X ammo_known=%u creation_ammo=%08X region=%d health=%.6g base=%.6g fatigue=%.6g limb=%.6g armor=%.6g weapon_damage=%.6g flags=%08X explosion=%u critical=%u caller_game_rva=%08X damage_applied=unverified",
            gSession, gContexts, GetTickCount64(), source.id, static_cast<unsigned>(source.type), target.id, static_cast<unsigned>(target.type),
            weapon.id, static_cast<unsigned>(weapon.type), carrier.id, static_cast<unsigned>(carrier.type),
            life ? life->serial : 0ull, life ? 1u : 0u, ammo, ammo ? 1u : 0u, life ? life->ammo : 0u,
            data.region, static_cast<double>(data.health), static_cast<double>(data.base), static_cast<double>(data.fatigue),
            static_cast<double>(data.limb), static_cast<double>(data.armor), static_cast<double>(data.weaponDamage),
            data.flags, data.flags & 0x2000 ? 1u : 0u, data.flags & 4 ? 1u : 0u, callerRva);
    }
    if (gContexts == kMaxContexts) {
        nvo::log::Write("CURRENT_HIT_LIMIT session=%u maximum=%u reload_to_capture_again=1", gSession, kMaxContexts);
        Summary("current_hit_limit");
    }
}

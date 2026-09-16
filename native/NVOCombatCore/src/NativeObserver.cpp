#include "NativeObserver.hpp"
#include "NativeLog.hpp"
#include "FlightPreview.hpp"
#include "FlightPhysics.hpp"
#include "SpawnBoundary.hpp"
#include <Windows.h>
#include <cstdint>
#include <cstring>
#include <atomic>
#include <limits>

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
using nvo::admission::Phase;
nvo::admission::Pool<kSlots> gLifeSlots;
unsigned gReserved{},gCommitted{},gCancelled{},gAdmissionFailed{},gLifeRefused{},gPhysicsRefused{};

struct Life {
    std::uintptr_t address{}; // identity only; never dereferenced after callback
    U32 ref{}, source{}, weapon{}, ammo{};
    unsigned long long serial{};
    unsigned impacts{};
    nvo::admission::Ticket ticket{};
};
Life gLives[kSlots]{};
unsigned long long NextLifetime() noexcept {
    if (gNextLifetime==(std::numeric_limits<unsigned long long>::max)()) return 0;
    return ++gNextLifetime;
}

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
    nvo::log::Write("FLIGHT_ADMISSION_SUMMARY session=%u reason=%s reserved=%u committed=%u cancelled=%u failed=%u lifecycle_refused=%u physics_refused=%u slots_held=%u process_fault=%u capacity=512 damage_replacement=0",
        gSession,reason,gReserved,gCommitted,gCancelled,gAdmissionFailed,gLifeRefused,gPhysicsRefused,gLifeSlots.Used(),static_cast<unsigned>(nvo::admission::processFault.load()));
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
    const auto reservation=nvo::spawn::Created(projectile,ref,source,weapon);
    auto serial = reservation ? reservation.serial : NextLifetime();
    Life* slot = nullptr;
    bool replaced = false;
    bool admitted = false;
    nvo::admission::Ticket ticket{};
    const U32 ammo = nvo::hit::ProjectileAmmo(projectile, gReadFailures);
    if (projectile) {
        for (auto& life : gLives) {
            if (life.address == reinterpret_cast<std::uintptr_t>(projectile)) {
                replaced = true; ++gReused; break;
            }
        }
        if (replaced) nvo::admission::Block(nvo::admission::Fault::Lifetime);
        else if (reservation && reservation.session==gSession
            && gLifeSlots.State(reservation.life)==Phase::Reserved
            && nvo::flight::ValidateCreation(projectile,reservation.profile,source,weapon,ammo)) {
            ticket=reservation.life;
            if (gLifeSlots.Bind(ticket)) {
                slot=&gLives[ticket.slot];
                admitted=nvo::physics::Attach(reservation.physics,projectile,ref);
            }
        } else if (!reservation && serial && ref) {
            ticket=gLifeSlots.Reserve();
            if (ticket && gLifeSlots.Bind(ticket) && gLifeSlots.Commit(ticket)) slot=&gLives[ticket.slot];
        }
    }
    if (slot) *slot = {reinterpret_cast<std::uintptr_t>(projectile), ref, source, weapon, ammo, serial, 0,ticket};
    else ++gOverflow;
    ++gCreated;
    if (gRows < kMaxEvents) {
        nvo::log::Write("EVENT session=%u seq=%u CREATE lifetime=%llu projectile=%08X source=%08X weapon=%08X tracked=%u replaced=%u ammo=%08X ammo_known=%u",
            gSession, gRows + 1, serial, ref, source, weapon, slot ? 1u : 0u, replaced ? 1u : 0u, ammo, ammo ? 1u : 0u);
        FinishedRow();
    }
    nvo::flight::Create(projectile, source, weapon, ammo, serial, slot != nullptr, admitted);
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
    nvo::spawn::Destroyed(projectile);
    const U32 ref = Id(projectile), source = Id(Arg(params, 0)), weapon = Id(Arg(params, 1));
    auto* life = Find(projectile, ref);
    if (!life) ++gUnmatched;
    const auto serial = life ? life->serial : 0ull;
    ++gDestroyed;
    if (gRows < kMaxEvents) {
        nvo::log::Write("EVENT session=%u seq=%u DESTROY lifetime=%llu projectile=%08X source=%08X weapon=%08X matched=%u impacts=%u",
            gSession, gRows + 1, life ? life->serial : 0ull, ref, source, weapon, life ? 1u : 0u, life ? life->impacts : 0u);
        if (life) { gLifeSlots.Destroy(life->ticket); *life = {}; }
        FinishedRow();
    } else if (life) { gLifeSlots.Destroy(life->ticket); *life = {}; }
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
    const bool wasActive=gActive;
    if (wasActive) Summary(reason);
    gActive = false;
    nvo::spawn::Suspend(reason);
    nvo::flight::Suspend(reason);
    for (auto& life : gLives) life = {};
    gLifeSlots.Reset();
    if (wasActive) nvo::log::Write("LIFECYCLE_POOL_RESET session=%u reason=%s slots_held=%u",gSession,reason,gLifeSlots.Used());
}

void nvo::observer::QueueCapture(const char* reason) noexcept
{
    const Lock lock;
    gReason = reason;
    nvo::spawn::Suspend("capture_requeued");
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
    gReserved=gCommitted=gCancelled=gAdmissionFailed=gLifeRefused=gPhysicsRefused=0;
    gContextsEnabled = contextsReady;
    for (auto& life : gLives) life = {};
    gLifeSlots.Reset();
    gActive = true;
    nvo::log::Write("CAPTURE session=%u reason=%s handlers=6 max_events=%u current_hit_observer=%u max_contexts=%u engine_damage_hooks=0 damage_replacement=0",
        gSession, gReason, kMaxEvents, gContextsEnabled ? 1u : 0u, kMaxContexts);
    const bool selectorReady=nvo::spawn::BeginCapture(gSession, contextsReady && nvo::hit::ProjectileLayoutReady());
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
        if (life) {
            const nvo::physics::HitQuery query{gSession,gContexts,life->serial,
                carrier.id,source.id,target.id,weapon.id,ammo,data.region,data.flags,
                {data.position[0],data.position[1],data.position[2]}};
            nvo::physics::ObserveHit(data.carrier,query);
        }
    }
    if (gContexts == kMaxContexts) {
        nvo::log::Write("CURRENT_HIT_LIMIT session=%u maximum=%u reload_to_capture_again=1", gSession, kMaxContexts);
        Summary("current_hit_limit");
    }
}

nvo::observer::LifetimeIdentity nvo::observer::LookupLifetime(void* carrier, U32 ref,
    U32 source, U32 weapon) noexcept
{
    const Lock lock;
    if (!gActive) return {};
    const auto* life = Find(carrier, ref);
    if (!life || life->source != source || life->weapon != weapon) return {};
    return {gSession, life->serial, life->ammo};
}

nvo::admission::Reservation nvo::observer::ReserveSpawn(unsigned session,void* actor,void* base,void* weapon) noexcept
{
    const Lock lock;
    admission::Reservation r{};
    if (!gActive || session!=gSession || admission::Blocked()) return r;
    if (!nvo::flight::PrepareProjectile(actor,base,weapon,r.profile)) return {};
    r.life=gLifeSlots.Reserve();
    if (!r.life) {
        if (++gLifeRefused<=4) nvo::log::Write("FLIGHT_ADMISSION_REFUSED session=%u reason=lifecycle_capacity supplied_projectile_unchanged=1",gSession);
        return {};
    }
    r.serial=NextLifetime(); r.session=gSession;
    if (r.serial) r.physics=nvo::physics::Reserve(r.serial,r.profile);
    if (!r.physics) {
        const auto before=gLifeSlots.Used();
        const bool cancelled=gLifeSlots.Cancel(r.life);
        if (!cancelled) admission::Block(admission::Fault::Lifetime);
        if (++gPhysicsRefused<=4) nvo::log::Write("FLIGHT_ADMISSION_REFUSED session=%u reason=physics_capacity_or_guard supplied_projectile_unchanged=1 lifecycle_rollback=%u slots_before=%u slots_after=%u weapon=%08X ammo=%08X",
            gSession,cancelled?1u:0u,before,gLifeSlots.Used(),r.profile.weapon,r.profile.ammo);
        return {};
    }
    gLives[r.life.slot]={};
    gLives[r.life.slot].serial=r.serial; gLives[r.life.slot].ticket=r.life;
    ++gReserved;
    nvo::flight::Selected(r.profile,r.serial);
    return r;
}
void nvo::observer::FinishSpawn(const admission::Reservation& r,void* result,bool paired,bool cleanCancellation) noexcept
{
    const Lock lock;
    if (!r) return;
    if (!gActive || gSession!=r.session) {
        admission::Block(admission::Fault::StaleSession);
        return; // Pool tokens changed on reset; never dereference/release a new occupant.
    }
    if (cleanCancellation) {
        const bool life=gLifeSlots.Cancel(r.life);
        const bool physics=nvo::physics::Cancel(r.physics);
        if (life) gLives[r.life.slot]={};
        if (life && physics) {
            ++gCancelled;
            if (gCancelled<=8) nvo::log::Write("FLIGHT_ADMISSION_CANCEL session=%u lifetime=%llu reason=no_object_returned both_reservations_released=1",gSession,r.serial);
            return;
        }
    } else if (paired && gLifeSlots.State(r.life)==Phase::Bound) {
        const auto& life=gLives[r.life.slot];
        if (life.address==reinterpret_cast<std::uintptr_t>(result) && life.serial==r.serial && !life.impacts
            && nvo::flight::ValidateCreation(result,r.profile,life.source,life.weapon,life.ammo)
            && nvo::physics::Commit(r.physics) && gLifeSlots.Commit(r.life)) {
            ++gCommitted;
            if (gCommitted<=32) nvo::log::Write("FLIGHT_ADMISSION_COMMIT session=%u lifetime=%llu projectile=%08X exact_return=1 physics_and_lifecycle_owned=1",gSession,r.serial,life.ref);
            return;
        }
    }
    admission::Block(paired?admission::Fault::Binding:admission::Fault::Pairing);
    gLifeSlots.Fault(r.life);
    nvo::physics::Fault(r.physics);
    ++gAdmissionFailed;
    if (gAdmissionFailed<=8) nvo::log::Write("FLIGHT_ADMISSION_REJECT session=%u lifetime=%llu reason=post_selection_receipt_or_binding process_admissions_blocked=1 ownership_retained_until_destroy_or_session_reset=1 prior_changes_rolled_back=0 current_private_projectile_left_to_engine=1",
        gSession,r.serial);
}

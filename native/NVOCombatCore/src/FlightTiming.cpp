#include "FlightTiming.hpp"
#include "FlightPhysics.hpp"
#include "CurrentHit.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <atomic>
#include <cmath>
#include <cstring>

namespace {
using U32 = std::uint32_t;
using U64 = unsigned long long;
constexpr std::uintptr_t kVtable = 0x108FA44, kSlot = kVtable + 0x310;
constexpr std::uintptr_t kUpdate = 0x9B8030;
constexpr unsigned kTracks = 8, kSteps = 64, kDepth = 8;
SRWLOCK gLock = SRWLOCK_INIT;
struct Lock {
    Lock() noexcept { AcquireSRWLockExclusive(&gLock); }
    ~Lock() { ReleaseSRWLockExclusive(&gLock); }
};
struct ErrorGuard {
    DWORD previous = GetLastError();
    ~ErrorGuard() { SetLastError(previous); }
};
struct Sample {
    U32 ref{}, source{}, weapon{}, base{}, flags{}, state{};
    float life{}, distance{}, pos[3]{}, mult{}, speed{};
    unsigned char impacted{};
    bool contacts{};
};
struct Track {
    std::uintptr_t address{}; // Identity, not an asynchronously dereferenced pointer.
    U64 serial{};
    U32 ref{}, source{}, weapon{}, ammo{}, base{};
    float lastLife{}, lastDistance{};
    unsigned steps{}, moving{}, stationary{}, collision{}, invalid{}, callbacks{};
    DWORD lastThread{};
    bool capped{}, inUpdate{}, blocked{};
};
struct Frame {
    std::uintptr_t caller{}, address{};
    U64 serial{};
    unsigned session{}, step{}, callbacksBefore{};
    DWORD thread{};
    float dt{}, gapLife{}, gapDistance{};
    Sample before{};
};
// Call-scoped thread storage: do not clear it on reload. Every substituted
// return must unwind its own entry even if the capture was suspended meanwhile.
__declspec(thread) Frame gFrames[kDepth];
__declspec(thread) unsigned gDepth;
Track gTracks[kTracks]{};
unsigned gSession{}, gAccepted{}, gRows{}, gInvalid{}, gRetiredDuring{}, gOtherThread{}, gNestedLimit{}, gOverlaps{}, gThreadChanges{};
DWORD gThread{};
bool gActive{}, gAttempted{}, gInstalled{}, gWarned{};
std::atomic<bool> gNotice{false};
void* gOriginal{};

template<class T> bool ReadAt(const void* p, unsigned offset, T& out) noexcept
{
    return p && nvo::hit::ReadBytes(static_cast<const char*>(p) + offset, &out, sizeof(out));
}
bool SampleOf(void* p, Sample& s) noexcept
{
    std::uintptr_t table{};
    void* source{}, *weapon{}, *base{}, *contact{};
    nvo::hit::Form f{}, a{}, w{}, b{};
    if (!ReadAt(p, 0, table) || table != kVtable || !nvo::hit::ReadForm(p, f)
        || !nvo::hit::IsProjectile(f.type) || !f.id
        || !ReadAt(p, 0x20, base) || !ReadAt(p, 0xF8, weapon) || !ReadAt(p, 0xFC, source)
        || !nvo::hit::ReadForm(base, b) || b.type != 0x33
        || !nvo::hit::ReadForm(weapon, w) || w.type != 0x28
        || !nvo::hit::ReadForm(source, a)
        || !ReadAt(p, 0x30, s.pos) || !ReadAt(p, 0x88, contact)
        || !ReadAt(p, 0x90, s.impacted) || !ReadAt(p, 0xC8, s.flags)
        || !ReadAt(p, 0xD0, s.mult) || !ReadAt(p, 0xD8, s.life)
        || !ReadAt(p, 0x110, s.distance) || !ReadAt(p, 0x150, s.state)
        || !ReadAt(base, 0x68, s.speed)) return false;
    s.ref = f.id; s.source = a.id; s.weapon = w.id; s.base = b.id; s.contacts = contact != nullptr;
    for (auto value : s.pos) if (!std::isfinite(value) || std::abs(value) > 1e9f) return false;
    return std::isfinite(s.life) && s.life >= 0 && s.life <= 1e7f
        && std::isfinite(s.distance) && s.distance >= 0 && s.distance <= 1e12f
        && std::isfinite(s.mult) && s.mult >= 0 && s.mult <= 1000
        && std::isfinite(s.speed) && s.speed >= 0 && s.speed <= 1e9f;
}
bool Identity(const Sample& s, const Track& t) noexcept
{
    return s.ref == t.ref && s.source == t.source && s.weapon == t.weapon && s.base == t.base;
}
Track* Find(std::uintptr_t address, U64 serial = 0) noexcept
{
    for (auto& t : gTracks) if (t.address == address && t.serial && (!serial || t.serial == serial)) return &t;
    return nullptr;
}
void TrackSummary(const Track& t, const char* reason) noexcept
{
    nvo::log::Write("FLIGHT_TIMING_SHOT session=%u lifetime=%llu projectile=%08X weapon=%08X reason=%s steps=%u moving=%u no_motion=%u collision=%u invalid=%u impact_callbacks=%u capped=%u pending_update=%u blocked=%u last_update_thread=%lu",
        gSession, t.serial, t.ref, t.weapon, reason, t.steps, t.moving, t.stationary, t.collision, t.invalid, t.callbacks,
        t.capped ? 1u : 0u, t.inUpdate ? 1u : 0u, t.blocked ? 1u : 0u, t.lastThread);
}

bool __cdecl Before(void* p, float dt, std::uintptr_t caller) noexcept
{
    const ErrorGuard error;
    const Lock lock;
    if (!gActive) return false;
    auto* t = Find(reinterpret_cast<std::uintptr_t>(p));
    if (!t || t->blocked) return false;
    const DWORD thread = GetCurrentThreadId();
    if (t->inUpdate) {
        // Never pair a before/after snapshot with an overlapping update, even
        // if the second call is a reentrant call on the same thread. Retire this
        // lifetime from timing. The original engine function still runs once.
        t->blocked = true; ++gOverlaps;
        nvo::log::Write("FLIGHT_TIMING_OVERLAP session=%u lifetime=%llu owner_thread=%lu incoming_thread=%lu observation_blocked=1 timing_writes=0", gSession, t->serial, t->lastThread, thread);
        return false;
    }
    if (gDepth >= kDepth) { ++gNestedLimit; return false; }
    if (t->steps >= kSteps) {
        if (!t->capped) { t->capped = true; TrackSummary(*t, "step_limit"); }
        return false;
    }
    Sample s{};
    if (!std::isfinite(dt) || dt < 0 || dt > 1 || !SampleOf(p, s) || !Identity(s, *t)) {
        ++gInvalid; ++t->invalid;
        if (t->invalid == 1) TrackSummary(*t, "before_sample_rejected");
        return false;
    }
    auto& f = gFrames[gDepth++];
    f = {};
    f.caller = caller; f.address = t->address; f.serial = t->serial;
    f.session = gSession; f.step = ++t->steps; f.dt = dt; f.before = s;
    f.callbacksBefore = t->callbacks; f.thread = thread;
    f.gapLife = s.life - t->lastLife; f.gapDistance = s.distance - t->lastDistance;
    t->inUpdate = true;
    if (thread != gThread) ++gOtherThread;
    if (t->lastThread != thread) {
        if (t->lastThread) ++gThreadChanges;
        // Bounded by kTracks*kSteps. No assumption that job threads keep affinity.
        nvo::log::Write("FLIGHT_TIMING_THREAD session=%u lifetime=%llu step=%u init_thread=%lu previous_thread=%lu update_thread=%lu", gSession, t->serial, f.step, gThread, t->lastThread, thread);
        t->lastThread = thread;
    }
    return true;
}
std::uintptr_t __cdecl After() noexcept
{
    const ErrorGuard error;
    // Only Before=true installs this continuation. No lifecycle method resets
    // gDepth. Nested calls pop in reverse order, including suspended captures.
    const Frame f = gFrames[--gDepth];
    const Lock lock;
    if (!gActive || f.session != gSession) return f.caller;
    auto* t = Find(f.address, f.serial);
    if (!t) {
        ++gRetiredDuring;
        nvo::log::Write("FLIGHT_STEP_UNAVAILABLE session=%u lifetime=%llu step=%u reason=identity_retired update_thread=%lu no_post_read=1",
            f.session, f.serial, f.step, f.thread);
        return f.caller;
    }
    t->inUpdate = false;
    if (t->blocked) {
        nvo::log::Write("FLIGHT_STEP_UNAVAILABLE session=%u lifetime=%llu step=%u reason=overlapping_update update_thread=%lu no_post_read=1", f.session, f.serial, f.step, f.thread);
        return f.caller;
    }
    // Shared counter, protected by gLock: callbacks need not run on this thread.
    // Counts callback deliveries in this observation window, not impact time.
    const unsigned impacts = t->callbacks - f.callbacksBefore;
    Sample s{};
    if (!SampleOf(reinterpret_cast<void*>(f.address), s) || !Identity(s, *t)) {
        ++gInvalid; ++t->invalid;
        nvo::log::Write("FLIGHT_STEP_UNAVAILABLE session=%u lifetime=%llu step=%u reason=after_sample_rejected", f.session, f.serial, f.step);
        return f.caller;
    }
    const auto& b = f.before;
    const double ds = static_cast<double>(s.distance) - b.distance;
    double displacement2 = 0;
    for (unsigned i = 0; i < 3; ++i) {
        const double delta = static_cast<double>(s.pos[i]) - b.pos[i];
        displacement2 += delta * delta;
    }
    const double setting = static_cast<double>(b.speed) * b.mult;
    const bool collision = t->callbacks || b.impacted || s.impacted || b.contacts || s.contacts;
    const bool moving = ds > 0;
    const bool valid = moving && !collision && f.dt > 0 && !(b.flags & 1) && !(s.flags & 1)
        && b.speed == s.speed && b.mult == s.mult && setting > 0 && std::isfinite(ds / f.dt);
    const double speed = valid ? ds / f.dt : -1;
    const char* phase = collision ? "collision" : moving ? "moving" : ds == 0 ? "no_motion" : "counter_reversed";
    if (collision) ++t->collision; else if (moving) ++t->moving; else if (ds == 0) ++t->stationary;
    if (ds < 0) { ++t->invalid; ++gInvalid; }
    t->lastLife = s.life; t->lastDistance = s.distance;
    ++gRows;
    nvo::log::Write("FLIGHT_STEP session=%u lifetime=%llu step=%u projectile=%08X weapon=%08X phase=%s dt_arg_s=%.9g life_before_s=%.9g life_after_s=%.9g gap_life_s=%.9g gap_distance=%.9g dist_before=%.9g dist_after=%.9g distance_delta=%.9g position_delta=%.9g setting_speed=%.9g speed_valid=%u step_speed=%.9g ratio=%.9g impacts_in_window=%u update_thread=%lu",
        f.session, f.serial, f.step, t->ref, t->weapon, phase, static_cast<double>(f.dt), static_cast<double>(b.life), static_cast<double>(s.life),
        static_cast<double>(f.gapLife), static_cast<double>(f.gapDistance), static_cast<double>(b.distance), static_cast<double>(s.distance), ds,
        std::sqrt(displacement2), setting, valid ? 1u : 0u, speed, valid ? speed / setting : -1, impacts, f.thread);
    nvo::log::Write("FLIGHT_STEP_STATE session=%u lifetime=%llu step=%u pos_before=(%.9g,%.9g,%.9g) pos_after=(%.9g,%.9g,%.9g) flags_before=%08X flags_after=%08X state_before=%u state_after=%u impacted_before=%u impacted_after=%u contacts_before=%u contacts_after=%u speed_before=%.9g speed_after=%.9g mult_before=%.9g mult_after=%.9g",
        f.session, f.serial, f.step, static_cast<double>(b.pos[0]), static_cast<double>(b.pos[1]), static_cast<double>(b.pos[2]),
        static_cast<double>(s.pos[0]), static_cast<double>(s.pos[1]), static_cast<double>(s.pos[2]), b.flags, s.flags, b.state, s.state,
        static_cast<unsigned>(b.impacted), static_cast<unsigned>(s.impacted), b.contacts ? 1u : 0u, s.contacts ? 1u : 0u,
        static_cast<double>(b.speed), static_cast<double>(s.speed), static_cast<double>(b.mult), static_cast<double>(s.mult));
    return f.caller;
}

__declspec(naked) void ReturnObserver()
{
    __asm {
        push 0 // Reserve original continuation without changing flags.
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        call After
        mov [ebx+36], eax
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        ret
    }
}
__declspec(naked) void UpdateObserver()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push dword ptr [ebx+36] // Original return address.
        push dword ptr [ebx+40] // Original float timestep, unchanged bits.
        push dword ptr [ebx+24] // Original ECX (this).
        call Before
        add esp, 12
        test al, al
        jz passthrough
        mov dword ptr [ebx+36], offset ReturnObserver
    passthrough:
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginal]
    }
}

bool SlotIs(void* target) noexcept
{
    void* actual{};
    return nvo::hit::ReadBytes(reinterpret_cast<void*>(kSlot), &actual, 4) && actual == target;
}
bool Fingerprint(std::uintptr_t address, unsigned size, std::uint64_t expected) noexcept
{
    unsigned char bytes[2200]{};
    if (size > sizeof(bytes) || !nvo::hit::ReadBytes(reinterpret_cast<void*>(address), bytes, size)) return false;
    if (!nvo::physics::NormalizeOwnedHooks(address, bytes, size)) return false;
    std::uint64_t h = 14695981039346656037ull;
    for (unsigned i = 0; i < size; ++i) h = (h ^ bytes[i]) * 1099511628211ull;
    return h == expected;
}
bool Guard() noexcept
{
    // Parent game/JIP guard must also be ready. This image is fixed at 00400000.
    const auto game = GetModuleHandleW(nullptr);
    IMAGE_DOS_HEADER dos{}; IMAGE_NT_HEADERS32 nt{}; MEMORY_BASIC_INFORMATION page{};
    if (reinterpret_cast<std::uintptr_t>(game) != 0x400000 || !nvo::hit::ProjectileLayoutReady()
        || !ReadAt(game, 0, dos) || dos.e_magic != IMAGE_DOS_SIGNATURE || dos.e_lfanew < 0x40 || dos.e_lfanew > 0x1000
        || !ReadAt(game, dos.e_lfanew, nt) || nt.Signature != IMAGE_NT_SIGNATURE
        || nt.FileHeader.Machine != IMAGE_FILE_MACHINE_I386 || nt.OptionalHeader.Magic != IMAGE_NT_OPTIONAL_HDR32_MAGIC
        || nt.FileHeader.TimeDateStamp != 0x4E0D50ED || nt.OptionalHeader.SizeOfImage != 0x107B000
        || !VirtualQuery(reinterpret_cast<void*>(kSlot), &page, sizeof(page))
        || page.State != MEM_COMMIT || page.Type != MEM_IMAGE || page.AllocationBase != game
        || (page.Protect & (PAGE_NOACCESS | PAGE_GUARD))) return false;
    return Fingerprint(kUpdate, 0x865, 0xA1B80FE6DF917F84ull)
        && Fingerprint(0x9BEF65, 0x41, 0xBDC0B598AD95B05Eull)
        && Fingerprint(0x9BF300, 0x63, 0x86FBDFE576BF1F9Bull)
        && Fingerprint(0x9BF370, 0xFC, 0x1A357A2E8A685927ull)
        && Fingerprint(0x9C4E60, 0x5E, 0xD82BC9F26A9C40F5ull);
}
bool EnsureInstalled() noexcept
{
    if (!Guard()) return false;
    const auto wrapper = reinterpret_cast<void*>(UpdateObserver);
    if (gAttempted) return gInstalled && SlotIs(wrapper);
    gAttempted = true;
    const auto original = reinterpret_cast<void*>(kUpdate);
    if (!SlotIs(original)) return false;
    DWORD old{}, ignored{};
    if (!VirtualProtect(reinterpret_cast<void*>(kSlot), 4, PAGE_READWRITE, &old)) return false;
    gOriginal = original;
    const bool changed = InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(kSlot), wrapper, original) == original;
    const bool restored = VirtualProtect(reinterpret_cast<void*>(kSlot), 4, old, &ignored) != 0;
    if (!restored) {
        // Restore only our slot while it remains writable; never clobber an owner.
        if (changed) InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(kSlot), original, wrapper);
        VirtualProtect(reinterpret_cast<void*>(kSlot), 4, old, &ignored);
        nvo::log::Write("FLIGHT_TIMING_DISABLED reason=page_protection_restore_failed");
        return false;
    }
    gInstalled = changed;
    return changed;
}
}

void nvo::timing::BeginCapture(unsigned session) noexcept
{
    const ErrorGuard error;
    const Lock lock;
    gActive = false; gSession = session; gThread = GetCurrentThreadId();
    gAccepted = gRows = gInvalid = gRetiredDuring = gOtherThread = gNestedLimit = gOverlaps = gThreadChanges = 0;
    for (auto& t : gTracks) t = {};
    if (!EnsureInstalled()) {
        nvo::log::Write("FLIGHT_TIMING_DISABLED session=%u reason=unsupported_code_or_slot_ownership timing_writes=0 damage_writes=0", session);
        if (!gWarned) { gWarned = true; gNotice.store(true); }
        return;
    }
    gActive = true;
    nvo::log::Write("FLIGHT_TIMING_READY session=%u slot=0108FD54 original=009B8030 max_lifetimes=%u max_steps_each=%u original_tail_calls=1 init_thread=%lu update_threads=any_serialized_per_lifetime event_counters=shared scope=private_pilot_only input_dt=engine_argument timing_writes=0 damage_writes=0",
        session, kTracks, kSteps, gThread);
}
void nvo::timing::Suspend(const char* reason) noexcept
{
    const ErrorGuard error;
    const Lock lock;
    if (gActive) {
        unsigned open = 0;
        for (const auto& t : gTracks) if (t.serial) { ++open; TrackSummary(t, reason); }
        nvo::log::Write("FLIGHT_TIMING_SUMMARY session=%u reason=%s accepted=%u steps_logged=%u invalid=%u retired_during_update=%u other_thread_steps=%u overlap_lifetimes=%u thread_changes=%u nesting_limit=%u open=%u timing_writes=0 damage_writes=0",
            gSession, reason, gAccepted, gRows, gInvalid, gRetiredDuring, gOtherThread, gOverlaps, gThreadChanges, gNestedLimit, open);
    }
    gActive = false;
    for (auto& t : gTracks) t = {};
}
void nvo::timing::EmitNotice(const nvse::ConsolePrefix* console) noexcept
{
    const ErrorGuard error;
    if (gNotice.exchange(false) && console && console->version >= 2 && console->RunScriptLine)
        console->RunScriptLine("PrintC \"[NVO] Flight timing diagnostics unavailable. See NVOCombatCore.log.\"", nullptr);
}
void nvo::timing::Track(void* p, U64 serial, U32 ref, U32 source, U32 weapon, U32 ammo, U32 base, float life, float distance) noexcept
{
    const ErrorGuard error;
    const Lock lock;
    if (!gActive || !p || !serial) return;
    if (auto* previous = Find(reinterpret_cast<std::uintptr_t>(p))) {
        TrackSummary(*previous, "identity_replaced"); *previous = {}; ++gInvalid;
    }
    if (gAccepted >= kTracks) return;
    for (auto& t : gTracks) if (!t.serial) {
        t = {}; t.address = reinterpret_cast<std::uintptr_t>(p); t.serial = serial;
        t.ref = ref; t.source = source; t.weapon = weapon; t.ammo = ammo; t.base = base;
        t.lastLife = life; t.lastDistance = distance; ++gAccepted;
        nvo::log::Write("FLIGHT_TIMING_TRACK session=%u lifetime=%llu projectile=%08X source=%08X weapon=%08X ammo=%08X base=%08X life_create_s=%.9g distance_create=%.9g",
            gSession, serial, ref, source, weapon, ammo, base, static_cast<double>(life), static_cast<double>(distance));
        return;
    }
}
void nvo::timing::Event(void* p, U64 serial, bool destroyed) noexcept
{
    const ErrorGuard error;
    const Lock lock;
    if (!gActive || !serial) return;
    const auto address = reinterpret_cast<std::uintptr_t>(p);
    auto* t = Find(address, serial);
    if (!t) return;
    // This callback may be on a different thread from Before/After. Never look
    // in its TLS for the active update. Shared identity retirement prevents the
    // post-call reader from dereferencing a projectile after a destroy notice.
    if (destroyed) { TrackSummary(*t, "destroy"); *t = {}; }
    else ++t->callbacks;
}

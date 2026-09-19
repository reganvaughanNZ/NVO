// Standalone x86 checks of the production NativeObserver translation unit.
// Forms, callback registration, admission profiles and dependent modules are
// bounded synthetic fixtures. No engine address, module, hook or game is used.
#include <Windows.h>
#include <array>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

#include "../src/NativeObserver.cpp"

namespace fixture {
using Bytes = std::array<unsigned char, 0x100>;
using nvo::admission::Reservation;
constexpr unsigned kProjectiles = 514;
Bytes source{}, weapon{}, base{}, target{};
std::array<Bytes, kProjectiles> projectiles{};
nvo::hit::Data hit{};
int process{};
unsigned checks{}, failures{}, unexpectedReads{}, registrations{}, removals{};
unsigned prepareCalls{}, selectedCalls{}, attachCalls{}, hitCalls{}, spawnCreates{}, spawnDestroys{};
unsigned createCalls{}, endCalls{};
unsigned long long lastCreatedLifetime{}, lastEndLifetime{}, lastHitLifetime{};
bool lastTracked{}, lastAdmitted{}, lastDestroyed{}, lastEndIdentityAvailable{};
bool logSucceeds = true, attachSucceeds = true;
bool physicsAvailable = true, projectileReadSucceeds = true, ammoReadSucceeds = true;
std::uint32_t projectileAmmo = 0x1005, projectileFormIdDelta{};
Reservation pending{};
nvo::admission::Pool<512> physicsPool;
nvo::observer::EventApiPrefix api{};
nvo::observer::Handler handlers[6]{};
std::vector<std::string> logs;

void Require(bool value) {
    if (!value) { std::puts("FAIL fixture setup"); std::exit(2); }
}
void Check(bool value, const char* label) {
    ++checks;
    if (!value) { ++failures; std::printf("FAIL %s\n", label); }
}
bool Inside(const void* from, std::size_t size, const void* start, std::size_t length) {
    const auto p = reinterpret_cast<std::uintptr_t>(from);
    const auto b = reinterpret_cast<std::uintptr_t>(start);
    return p >= b && size <= length && p - b <= length - size;
}
bool Readable(const void* from, std::size_t size) {
    return Inside(from, size, source.data(), source.size())
        || Inside(from, size, weapon.data(), weapon.size())
        || Inside(from, size, base.data(), base.size())
        || Inside(from, size, target.data(), target.size())
        || Inside(from, size, projectiles.data(), sizeof(projectiles))
        || Inside(from, size, &hit, sizeof(hit));
}
void Form(Bytes& bytes, std::uint32_t id, unsigned char type) {
    bytes.fill(0); bytes[4] = type;
    std::memcpy(bytes.data() + 0x0C, &id, sizeof(id));
}
std::uint32_t FormId(const Bytes& bytes) {
    std::uint32_t id{}; std::memcpy(&id, bytes.data() + 0x0C, sizeof(id)); return id;
}
unsigned EventIndex(const char* name) {
    for (unsigned i = 0; i < 6; ++i)
        if (std::strcmp(name, kBindings[i].name) == 0) return i;
    Require(false); return 0;
}
bool __cdecl Set(const char* name, nvo::observer::Handler handler) {
    ++registrations; handlers[EventIndex(name)] = handler; return true;
}
bool __cdecl Remove(const char* name, nvo::observer::Handler handler) {
    ++removals;
    const unsigned i = EventIndex(name);
    if (handlers[i] == handler) handlers[i] = nullptr;
    return true;
}
void Event(unsigned event, unsigned index = 0) {
    Require(event < 3 && index < kProjectiles && handlers[event]);
    void* params[]{source.data(), weapon.data(), target.data()};
    handlers[event](projectiles[index].data(), params);
}
nvo::observer::LifetimeIdentity Identity(unsigned index = 0) {
    return nvo::observer::LookupLifetime(projectiles[index].data(), FormId(projectiles[index]),
        FormId(source), FormId(weapon));
}
Reservation Reserve() {
    return nvo::observer::ReserveSpawn(gSession, source.data(), base.data(), weapon.data());
}
void Reload() {
    nvo::observer::Suspend("fixture_reload");
    nvo::observer::QueueCapture("fixture_reload");
    nvo::observer::Tick();
}
void Reset() {
    nvo::observer::Suspend("fixture_process_end");
    // Independent test process simulation only. Production reload is exercised
    // by Reload(), which never resets this process-wide latch or identity.
    nvo::admission::processFault.store(nvo::admission::Fault::None);
    gNextLifetime = 0;
    logSucceeds = attachSucceeds = physicsAvailable = projectileReadSucceeds = ammoReadSucceeds = true;
    projectileAmmo = 0x1005; projectileFormIdDelta = 0;
    registrations = removals = prepareCalls = selectedCalls = attachCalls = hitCalls = 0;
    spawnCreates = spawnDestroys = createCalls = endCalls = 0;
    lastCreatedLifetime = lastEndLifetime = lastHitLifetime = 0;
    lastTracked = lastAdmitted = lastDestroyed = lastEndIdentityAvailable = false;
    logs.clear();
    Form(source, 0x1001, 0x3B); Form(weapon, 0x1002, 0x28);
    Form(base, 0x1003, 0x33); Form(target, 0x1004, 0x3B);
    for (unsigned i = 0; i < kProjectiles; ++i) Form(projectiles[i], 0xFF001000 + i, 0x40);
    projectiles[1][4] = 0x3D; // Separate admitted ballistic fixture; 0x40 is FlameProjectile.
    void* owner = &process;
    std::memcpy(target.data() + 0x68, &owner, sizeof(owner));
    hit = {}; hit.source = source.data(); hit.target = target.data();
    hit.carrier = projectiles[0].data(); hit.weapon = weapon.data(); hit.region = 1;
    api = {}; api.SetNativeEventHandler = Set; api.RemoveNativeEventHandler = Remove;
    nvo::observer::Initialize(&api, nullptr);
    nvo::observer::QueueCapture("fixture_process_start");
    nvo::observer::Tick();
    Require(gActive && gLifeSlots.Used() == 0 && physicsPool.Used() == 0);
}
void Observe() {
    nvo::transaction::CopyScope scope{};
    nvo::capture::ArmourReceipt armour{};
    nvo::observer::CurrentHit(&hit, &process, nullptr, scope, armour);
}
bool Has(const char* fragment) {
    for (const auto& line : logs) if (line.find(fragment) != std::string::npos) return true;
    return false;
}
unsigned Count(const char* fragment) {
    unsigned count{};
    for (const auto& line : logs) if (line.find(fragment) != std::string::npos) ++count;
    return count;
}
void CreateReserved(const Reservation& r, unsigned index = 1) {
    Require(static_cast<bool>(r)); pending = r; Event(0, index); pending = {};
}
void Commit(const Reservation& r, unsigned index = 1) {
    nvo::observer::FinishSpawn(r, projectiles[index].data(), true, false);
}
}

namespace nvo::log {
bool Write(const char* format, ...) noexcept {
    char line[4096]{};
    va_list args; va_start(args, format);
    const int length = vsnprintf(line, sizeof(line), format, args);
    va_end(args);
    fixture::Require(length >= 0 && static_cast<std::size_t>(length) < sizeof(line));
    fixture::logs.emplace_back(line);
    return fixture::logSucceeds;
}
}
namespace nvo::hit {
bool ReadBytes(const void* from, void* to, std::size_t size) noexcept {
    if (!from || !to || !fixture::Readable(from, size)) { ++fixture::unexpectedReads; return false; }
    std::memcpy(to, from, size); return true;
}
bool ReadForm(void* form, Form& out) noexcept {
    out = {}; if (!form) return true;
    if (!fixture::projectileReadSucceeds && fixture::Inside(form, sizeof(fixture::Bytes),
        fixture::projectiles.data(), sizeof(fixture::projectiles))) return false;
    unsigned char bytes[16]{};
    if (!ReadBytes(form, bytes, sizeof(bytes))) return false;
    out.type = bytes[4]; std::memcpy(&out.id, bytes + 0x0C, sizeof(out.id));
    if (fixture::Inside(form, sizeof(fixture::Bytes), fixture::projectiles.data(), sizeof(fixture::projectiles)))
        out.id += fixture::projectileFormIdDelta;
    return true;
}
bool IsProjectile(unsigned char type) noexcept { return (type >= 0x3D && type <= 0x40) || type == 0x69; }
std::uint32_t ProjectileAmmo(void* projectile, unsigned& failures) noexcept {
    if (!projectile) return 0;
    if (!fixture::Readable(projectile, sizeof(fixture::Bytes))) { ++failures; ++fixture::unexpectedReads; return 0; }
    if (!fixture::ammoReadSucceeds) { ++failures; return 0; }
    return fixture::projectileAmmo;
}
bool ProjectileLayoutReady() noexcept { return true; }
bool EnsureInstalled() noexcept { return true; }
}
namespace nvo::spawn {
bool BeginCapture(unsigned, bool layoutReady) noexcept { return layoutReady; }
void Suspend(const char*) noexcept { fixture::pending = {}; }
admission::Reservation Created(void* p, std::uint32_t, std::uint32_t, std::uint32_t) noexcept {
    fixture::Require(fixture::Readable(p, sizeof(fixture::Bytes)));
    ++fixture::spawnCreates; return fixture::pending;
}
void Destroyed(void* p) noexcept {
    fixture::Require(fixture::Readable(p, sizeof(fixture::Bytes))); ++fixture::spawnDestroys;
}
}
namespace nvo::flight {
void BeginCapture(unsigned, bool, bool) noexcept {}
void Suspend(const char*) noexcept { fixture::physicsPool.Reset(); }
void EmitNotice(const nvse::ConsolePrefix*) noexcept {}
bool PrepareProjectile(void* actor, void* projectileBase, void* weaponPointer, admission::Profile& profile) noexcept {
    ++fixture::prepareCalls;
    if (actor != fixture::source.data() || projectileBase != fixture::base.data()
        || weaponPointer != fixture::weapon.data()) return false;
    profile = {}; profile.actor = actor; profile.weaponPointer = weaponPointer;
    profile.projectile = projectileBase; profile.source = fixture::FormId(fixture::source);
    profile.weapon = fixture::FormId(fixture::weapon); profile.ammo = 0x1005;
    profile.base = fixture::FormId(fixture::base); profile.original = 0x1006; profile.changesBase = true;
    return true;
}
bool ValidateCreation(void* projectile, const admission::Profile& profile, std::uint32_t source,
    std::uint32_t weapon, std::uint32_t ammo) noexcept {
    return fixture::Readable(projectile, sizeof(fixture::Bytes))
        && source == profile.source && weapon == profile.weapon && ammo == profile.ammo;
}
void Selected(const admission::Profile&, unsigned long long) noexcept { ++fixture::selectedCalls; }
void Create(void* p, std::uint32_t, std::uint32_t, std::uint32_t, unsigned long long lifetime,
    bool tracked, bool admitted) noexcept {
    fixture::Require(fixture::Readable(p, sizeof(fixture::Bytes)));
    ++fixture::createCalls; fixture::lastCreatedLifetime = lifetime;
    fixture::lastTracked = tracked; fixture::lastAdmitted = admitted;
}
void EndSample(void* p, unsigned long long lifetime, bool destroyed, bool identityAvailable) noexcept {
    fixture::Require(fixture::Readable(p, sizeof(fixture::Bytes)));
    ++fixture::endCalls; fixture::lastEndLifetime = lifetime; fixture::lastDestroyed = destroyed;
    fixture::lastEndIdentityAvailable = identityAvailable;
}
}
namespace nvo::physics {
admission::Ticket Reserve(unsigned long long, const admission::Profile&) noexcept {
    return fixture::physicsAvailable ? fixture::physicsPool.Reserve() : admission::Ticket{};
}
bool Attach(admission::Ticket ticket, void* p, std::uint32_t) noexcept {
    fixture::Require(fixture::Readable(p, sizeof(fixture::Bytes)));
    ++fixture::attachCalls;
    return fixture::attachSucceeds && fixture::physicsPool.Bind(ticket);
}
bool Commit(admission::Ticket ticket) noexcept { return fixture::physicsPool.Commit(ticket); }
bool Cancel(admission::Ticket ticket) noexcept { return fixture::physicsPool.Cancel(ticket); }
void Fault(admission::Ticket ticket) noexcept { fixture::physicsPool.Fault(ticket); }
void ObserveHit(void* p, const HitQuery& query) noexcept {
    fixture::Require(fixture::Readable(p, sizeof(fixture::Bytes)));
    ++fixture::hitCalls; fixture::lastHitLifetime = query.lifetime;
}
}

int main() {
    using namespace fixture;
    using nvo::admission::Fault;
    using nvo::admission::Phase;
    static_assert(sizeof(void*) == 4, "This fixture must run under the x86 target ABI");
    Reset();
    Check(registrations == 6 && removals == 6, "production capture registers all six callbacks");
    Event(0);
    const auto first = Identity();
    Check(first.lifetime != 0 && first.session == gSession && first.ammo == 0x1005,
        "ordinary observer creation exposes diagnostic identity");
    Check(lastTracked && !lastAdmitted && attachCalls == 0, "observer creation has no admitted physics ownership");
    Check(!nvo::observer::LookupLifetime(projectiles[0].data(), FormId(projectiles[0]), 9, FormId(weapon)).lifetime,
        "wrong source cannot resolve lifetime");
    Check(!nvo::observer::LookupLifetime(projectiles[0].data(), FormId(projectiles[0]), FormId(source), 9).lifetime,
        "wrong weapon cannot resolve lifetime");
    Observe();
    Check(hitCalls == 1 && lastHitLifetime == first.lifetime, "unambiguous current hit retains diagnostic lifetime");
    for (unsigned i = 0; i < 12; ++i) Event(0);
    Check(!nvo::admission::Blocked(), "twelve observer flame repeats never latch a process fault");
    Check(!Identity().lifetime, "repeated observer address is withheld from lifetime lookup");
    Check(!lastTracked && !lastAdmitted && lastCreatedLifetime == 0,
        "ambiguous repeat is not published as tracked, admitted or a fresh lifetime");
    Check(gObserverRepeats == 12 && gOwnedConflicts == 0 && gOverflow == 0,
        "observer repeats are distinguished from ownership conflict and capacity overflow");
    Check(Count("PROJECTILE_LIFETIME_AMBIGUITY") == 8,
        "observer ambiguity detail logging stays within its independent eight-row budget");
    Observe();
    Check(hitCalls == 1, "ambiguous current hit cannot expose stale lifetime to physics");
    Event(1);
    Check(lastEndLifetime == first.lifetime && !lastDestroyed && !lastEndIdentityAvailable,
        "ambiguous impact forwards prior serial only for internal cleanup with identity unavailable");
    Check(Has("IMPACT lifetime=0"), "ambiguous impact log withholds the prior lifetime");
    Event(2);
    Check(lastEndLifetime == first.lifetime && lastDestroyed && !lastEndIdentityAvailable && !Identity().lifetime,
        "ambiguous destroy retains prior serial solely for internal sample cleanup");
    Check(Has("DESTROY lifetime=0") && Has("matched=0 impacts=1 cleanup_lifetime="),
        "ambiguous destroy log withholds matched lifetime while naming cleanup separately");
    Check(gLifeSlots.Used() == 0, "destroy releases quarantined lifecycle storage");
    Event(0);
    Check(Identity().lifetime > first.lifetime && !nvo::admission::Blocked(),
        "a later creation after destroy receives a fresh diagnostic lifetime");

    Reset(); Event(0); Event(0);
    auto reservation = Reserve();
    Check(static_cast<bool>(reservation), "9mm reservation remains possible after repeated observer flames");
    CreateReserved(reservation); Commit(reservation);
    Check(!nvo::admission::Blocked() && gLifeSlots.State(reservation.life) == Phase::Active
        && physicsPool.State(reservation.physics) == Phase::Active, "9mm lifecycle and physics commit after flames");
    Check(Identity(1).lifetime == reservation.serial && lastTracked && lastAdmitted,
        "admitted 9mm retains its reserved lifetime");
    Reload();
    Check(gLifeSlots.Used() == 0 && !Identity().lifetime && !nvo::admission::Blocked(),
        "reload clears quarantine without creating a process fault");
    reservation = Reserve();
    Check(static_cast<bool>(reservation), "9mm reservation remains possible after flame then reload");
    CreateReserved(reservation); Commit(reservation);
    Check(gLifeSlots.State(reservation.life) == Phase::Active, "post-reload 9mm commits normally");
    Event(0, 1);
    Check(nvo::admission::processFault.load() == Fault::Lifetime,
        "repeat of an existing admitted lifetime keeps hard lifetime fault");
    Check(gLifeSlots.State(reservation.life) != Phase::Empty, "admitted collision does not release owned lifecycle ticket");
    Event(1, 1);
    Check(lastEndLifetime == reservation.serial && !lastDestroyed && !lastEndIdentityAvailable
        && Has("IMPACT lifetime=0"),
        "ambiguous admitted impact retains retirement serial while withholding diagnostic identity");
    Event(2, 1);
    Check(lastEndLifetime == reservation.serial && lastDestroyed && !lastEndIdentityAvailable
        && gLifeSlots.State(reservation.life) == Phase::Empty,
        "ambiguous admitted destroy retires the original lifecycle with identity unavailable");
    Reload();
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Reserve(),
        "true ownership fault persists reload and blocks new reservation");
    Check(Has("reason=process_fault") && Has("process_fault=6"),
        "blocked post-reload reservation explicitly records its process fault");

    Reset(); Event(0);
    reservation = Reserve(); CreateReserved(reservation, 0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime,
        "incoming admitted reservation colliding with observer lifetime faults");
    Commit(reservation, 0);
    Check(gLifeSlots.State(reservation.life) != Phase::Active && gCommitted == 0,
        "colliding admitted reservation cannot commit");
    Check(nvo::admission::processFault.load() == Fault::Lifetime, "binding failure preserves first lifetime fault");

    Reset(); Event(0); Event(0);
    reservation = Reserve(); CreateReserved(reservation, 0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime,
        "incoming admitted reservation colliding with quarantine faults");
    Commit(reservation, 0);
    Check(gCommitted == 0, "quarantine cannot be promoted into admitted ownership");

    Reset(); reservation = Reserve(); CreateReserved(reservation);
    Check(gLifeSlots.State(reservation.life) == Phase::Bound, "unsettled admitted create binds lifecycle ticket");
    Event(0, 1);
    Check(nvo::admission::processFault.load() == Fault::Lifetime,
        "repeated pending admitted create keeps hard lifetime fault");
    Commit(reservation);
    Check(gCommitted == 0 && gLifeSlots.State(reservation.life) == Phase::Faulted
        && physicsPool.State(reservation.physics) == Phase::Faulted,
        "ambiguous pending admission cannot commit after the ownership fault");

    Reset(); reservation = Reserve(); CreateReserved(reservation, 0);
    Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime,
        "matching flame scalar identity cannot bypass an admitted ownership claim");

    Reset(); reservation = Reserve(); CreateReserved(reservation);
    nvo::admission::Block(Fault::Physics);
    Commit(reservation);
    Check(gCommitted == 0 && gLifeSlots.State(reservation.life) == Phase::Faulted,
        "otherwise valid pending admission cannot commit after an unrelated process fault");

    Reset(); Event(0);
    Form(projectiles[0], 0xFF008000, 0x40); Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "changed reference at observer flame address retains the hard lifetime fault");
    Event(2);
    Check(gLifeSlots.Used() == 1, "wrong-reference destroy cannot retire observer flame ambiguity");
    Reload();
    Check(gLifeSlots.Used() == 0 && nvo::admission::processFault.load() == Fault::Lifetime,
        "session reset clears changed-reference storage while preserving the fault");

    Reset(); Event(0); Form(source, 0x2001, 0x3B); Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "changed source excludes an observer flame repeat from quarantine exception");
    Reset(); Event(0); Form(weapon, 0x2002, 0x28); Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "changed weapon excludes an observer flame repeat from quarantine exception");
    Reset(); Event(0); projectileAmmo = 0x2005; Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "changed ammo excludes an observer flame repeat from quarantine exception");
    Reset(); Event(0); projectiles[0][4] = 0x3D; Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "changed current projectile type retains hard fault");
    Reset(); projectiles[0][4] = 0x3D; Event(0); projectiles[0][4] = 0x40; Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "current flame type cannot relabel a previously non-flame creation");
    Reset(); Event(0, 1); Event(0, 1);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity(1).lifetime,
        "matching non-flame observer creation still retains hard fault");
    Reset(); Event(0); projectileReadSucceeds = false; Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "failed current form read cannot qualify flame exception");
    Reset(); projectileReadSucceeds = false; Event(0); projectileReadSucceeds = true; Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "failed original form read cannot be replaced by a later flame type");
    Reset(); Event(0); projectileFormIdDelta = 1; Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "inconsistent current form ID cannot qualify flame exception");
    Reset(); projectileFormIdDelta = 1; Event(0); projectileFormIdDelta = 0; Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "inconsistent original form ID cannot become trusted stored flame type");
    Reset(); Event(0); Form(projectiles[0], 0, 0x40); Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "missing current reference retains hard fault");
    Reset(); Form(source, 0, 0x3B); Event(0); Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "matching unknown sources are not positive identity evidence");
    Reset(); Form(weapon, 0, 0x28); Event(0); Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "matching unknown weapons are not positive identity evidence");
    Reset(); projectileAmmo = 0; Event(0); Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "matching unknown ammo is not positive identity evidence");
    Reset(); Event(0); ammoReadSucceeds = false; Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "failed ammo read cannot qualify flame exception");
    Reset(); Event(0); Event(0); Form(source, 0x2001, 0x3B); Event(0);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && !Identity().lifetime,
        "already quarantined flame escalates to hard fault when scalar identity changes");

    Reset(); reservation = Reserve(); CreateReserved(reservation); Commit(reservation);
    Form(projectiles[1], 0xFF009000, 0x40); Event(0, 1);
    Check(nvo::admission::processFault.load() == Fault::Lifetime,
        "changed reference at admitted address keeps ownership fault");
    Event(2, 1);
    Check(gLifeSlots.State(reservation.life) != Phase::Empty && !Identity(1).lifetime,
        "wrong-reference destroy cannot release an admitted owner's ticket");
    Form(projectiles[1], 0xFF001001, 0x40); Event(2, 1);
    Check(gLifeSlots.State(reservation.life) == Phase::Empty && lastEndLifetime == reservation.serial,
        "exact-reference destroy releases ambiguous admitted lifecycle storage for cleanup");

    Reset();
    for (unsigned i = 0; i < kSlots; ++i) Event(0, i);
    Check(gLifeSlots.Used() == kSlots, "observer lifecycle capacity is bounded at 512");
    Event(0, kSlots);
    Check(!Identity(kSlots).lifetime && !nvo::admission::Blocked(),
        "observer pool saturation refuses new identity without ownership fault");
    Event(0, 0);
    Check(!Identity().lifetime && !nvo::admission::Blocked(),
        "repeat handling still quarantines at full pool capacity");
    Check(!Reserve() && !nvo::admission::Blocked(), "full lifecycle pool refuses 9mm without process fault");
    Event(2, 0);
    reservation = Reserve();
    Check(static_cast<bool>(reservation), "quarantine destroy returns capacity to new admission");
    nvo::observer::FinishSpawn(reservation, nullptr, false, true);
    Check(gLifeSlots.State(reservation.life) == Phase::Empty && physicsPool.Used() == 0,
        "clean null return cancels both reservations");

    Reset(); gRows = kMaxEvents; logSucceeds = false;
    Event(0); const auto budgetLifetime = Identity().lifetime; Event(0); Event(1);
    Check(!Identity().lifetime && !nvo::admission::Blocked() && lastEndLifetime == budgetLifetime
        && !lastEndIdentityAvailable,
        "event log exhaustion and failed writes do not alter observer quarantine");
    reservation = Reserve(); CreateReserved(reservation); Commit(reservation);
    Check(gLifeSlots.State(reservation.life) == Phase::Active,
        "admission commits independently of exhausted diagnostics and failed writes");
    Event(0, 1);
    Check(nvo::admission::processFault.load() == Fault::Lifetime,
        "admitted collision faults even after event log exhaustion");
    Event(2);
    Check(!Identity().lifetime, "quarantine destroy executes after event log exhaustion");

    Reset(); gNextLifetime = (std::numeric_limits<unsigned long long>::max)();
    Event(0);
    Check(!Identity().lifetime && gLifeSlots.Used() == 0 && !nvo::admission::Blocked(),
        "lifetime identity exhaustion cannot wrap into observer tracking");
    reservation = Reserve();
    Check(!reservation && gLifeSlots.Used() == 0 && physicsPool.Used() == 0,
        "lifetime identity exhaustion rolls back attempted admission");

    Reset(); physicsAvailable = false; reservation = Reserve();
    Check(!reservation && gLifeSlots.Used() == 0 && !nvo::admission::Blocked(),
        "physics capacity refusal releases reserved lifecycle ticket");
    Reset(); reservation = Reserve(); Reload();
    const auto current = Reserve();
    nvo::observer::FinishSpawn(reservation, nullptr, false, true);
    Check(nvo::admission::processFault.load() == Fault::StaleSession,
        "old session completion retains stale-session protection");
    Check(gLifeSlots.State(current.life) == Phase::Reserved && physicsPool.State(current.physics) == Phase::Reserved,
        "stale completion cannot cancel a current slot occupant");
    Reload();
    Check(nvo::admission::processFault.load() == Fault::StaleSession && !Reserve(),
        "stale-session fault also survives subsequent reload");
    Reset(); attachSucceeds = false; reservation = Reserve(); CreateReserved(reservation);
    Check(!lastAdmitted && gLifeSlots.State(reservation.life) == Phase::Bound,
        "failed physics attach still retains bound lifecycle obligation");
    Event(0, 1);
    Check(nvo::admission::processFault.load() == Fault::Lifetime && gOwnedConflicts == 1,
        "failed attachment does not downgrade reservation claim to observer-only status");
    Reset(); attachSucceeds = false; reservation = Reserve(); CreateReserved(reservation); Commit(reservation);
    Check(nvo::admission::Blocked() && gCommitted == 0,
        "failed physics attachment never becomes committed ownership");
    Event(0, 1);
    Check(gOwnedConflicts == 1 && gObserverRepeats == 0 && gLifeSlots.State(reservation.life) == Phase::Faulted,
        "faulted admitted claim remains owned and retained on a later repeated create");
    Check(unexpectedReads == 0, "every stub read stayed inside registered synthetic form and hit memory");
    std::printf("Projectile lifecycle checks: %u passed, %u failed\n", checks - failures, failures);
    return failures ? 1 : 0;
}

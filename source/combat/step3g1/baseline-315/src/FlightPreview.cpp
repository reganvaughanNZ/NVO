#include "FlightPreview.hpp"
#include "FlightTiming.hpp"
#include "FlightPhysics.hpp"
#include "CurrentHit.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <cwchar>
#include <iterator>
#include <atomic>
#include <cstdio>

namespace {
using U32 = std::uint32_t;
constexpr unsigned kProfiles = 16, kShots = 32, kSkipRows = 8;
struct Key { char plugin[260]{}; U32 local{}, resolved{}; };
struct Profile {
    char name[48]{};
    Key weapon{}, ammo{}, projectile{}, original{};
    double maximum{}, barrel{}, peak{}, muzzle{}, bc{};
    unsigned dragModel{};
    bool selectOnFire{}, flightEnabled{};
    void* originalPointer{};
    nvo::observer::FormResult result{};
    unsigned char originalData[84]{}, replacementData[84]{};
    unsigned fields{};
};
struct Mod { char name[260]{}; unsigned char index{}; };
struct Snapshot {
    U32 ref{}, source{}, weapon{}, base{};
    unsigned short flags{}, type{};
    float gravity{}, speed{}, range{}, mult{}, time{}, distance{};
};
struct RangeObservation { float range{}; U32 flags{}; unsigned char impacted{}; unsigned valid{}; };
struct Shot { unsigned long long serial{}; unsigned profile{}; Snapshot start{}; bool impacted{}; RangeObservation launchRange{}; };
Profile gProfiles[kProfiles]{};
Mod gMods[255]{};
Shot gShots[kShots]{};
unsigned gProfileCount{}, gModCount{}, gSession{}, gMaxShots{}, gSeen{}, gMatched{}, gSkipped{};
unsigned gReadFailures{}, gMismatch{}, gCreateRows{}, gImpactRows{}, gDestroyRows{}, gSkipRows{};
unsigned gRangeRows{}, gRangeReadFailures{}, gRangeLogFailures{};
double gUnitsPerMetre{};
bool gActive{}, gWarned{};
bool gSelectorReady{};
DWORD gCaptureThread{};
unsigned gSelected{}, gSelectionSkipped{}, gSelectionSkipRows{}, gSelectionOtherThread{};
std::atomic<bool> gNoticePending{false};
std::atomic<bool> gKitNoticePending{false};
bool gKitNotified{};
wchar_t gRoot[32768]{};

// The parent observer serializes all access. Preserve host Win32 error state
// even when config reads, guarded memory reads or logging fail.
struct ErrorGuard {
    DWORD previous = GetLastError();
    ~ErrorGuard() { SetLastError(previous); }
};
template<class T> bool ReadAt(const void* pointer, unsigned offset, T& value) noexcept
{
    return pointer && nvo::hit::ReadBytes(static_cast<const char*>(pointer) + offset, &value, sizeof(value));
}
char* Trim(char* s) noexcept
{
    while (*s == ' ' || *s == '\t' || *s == '\r') ++s;
    auto size = std::strlen(s);
    while (size && (s[size - 1] == ' ' || s[size - 1] == '\t' || s[size - 1] == '\r')) s[--size] = 0;
    return s;
}
bool Number(const char* s, double& result) noexcept
{
    // Locale-independent, nonnegative decimal grammar; no NaN, exponent,
    // trailing text, signs or locale changes in the host process.
    result = 0;
    double divisor = 1;
    bool dot = false, digit = false;
    unsigned digits = 0;
    for (; *s; ++s) {
        if (*s == '.' && !dot) { dot = true; continue; }
        if (*s < '0' || *s > '9' || ++digits > 15) return false;
        digit = true;
        if (dot) { divisor *= 10; result += (*s - '0') / divisor; }
        else result = result * 10 + (*s - '0');
    }
    return digit && std::isfinite(result);
}
bool ParseKey(const char* s, Key& key) noexcept
{
    const char* split = std::strrchr(s, ':');
    if (!split || split == s || split - s >= 260 || std::strlen(split + 1) != 6) return false;
    const auto length = static_cast<std::size_t>(split - s);
    for (std::size_t i = 0; i < length; ++i) {
        const auto c = static_cast<unsigned char>(s[i]);
        if (c < 32 || c > 126 || std::strchr("/\\:*?\"<>|", c)) return false;
    }
    if (length < 5) return false;
    std::memcpy(key.plugin, s, length);
    key.plugin[length] = 0;
    if (_stricmp(key.plugin + length - 4, ".esm") && _stricmp(key.plugin + length - 4, ".esp")) return false;
    key.local = 0;
    for (const char* p = split + 1; *p; ++p) {
        unsigned value = *p >= '0' && *p <= '9' ? static_cast<unsigned>(*p - '0') :
            *p >= 'A' && *p <= 'F' ? static_cast<unsigned>(*p - 'A' + 10) :
            *p >= 'a' && *p <= 'f' ? static_cast<unsigned>(*p - 'a' + 10) : 16;
        if (value > 15) return false;
        key.local = key.local * 16 + value;
    }
    return key.local != 0;
}
bool FilePresent(const wchar_t* relative) noexcept
{
    wchar_t path[32768]{};
    if (wcscpy_s(path, gRoot) || wcscat_s(path, relative)) return false;
    const DWORD flags = GetFileAttributesW(path);
    return flags != INVALID_FILE_ATTRIBUTES && !(flags & FILE_ATTRIBUTE_DIRECTORY);
}
const char* LoadConfig(bool& enabled) noexcept
{
    wchar_t path[32768]{};
    const DWORD len = GetModuleFileNameW(nullptr, gRoot, static_cast<DWORD>(std::size(gRoot)));
    if (!len || len >= std::size(gRoot)) return "game_path_unavailable";
    wchar_t* slash = std::wcsrchr(gRoot, L'\\');
    if (!slash) return "game_path_unavailable";
    slash[1] = 0;
    if (wcscpy_s(path, gRoot) || wcscat_s(path, L"Data\\NVSE\\Plugins\\NVOFlightPreview.ini")) return "config_path_too_long";
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) return "config_missing_or_unreadable";
    LARGE_INTEGER size{};
    char buffer[16385]{};
    DWORD got{};
    bool ok = GetFileSizeEx(file, &size) && size.QuadPart > 0 && size.QuadPart < static_cast<LONGLONG>(sizeof(buffer))
        && ReadFile(file, buffer, static_cast<DWORD>(size.QuadPart), &got, nullptr)
        && got == static_cast<DWORD>(size.QuadPart);
    CloseHandle(file);
    if (!ok || std::strlen(buffer) != got) return "config_size_encoding_or_read";
    unsigned globalFields = 0;
    bool globalSection = false, sawGlobal = false;
    Profile* profile = nullptr;
    char* cursor = buffer;
    // Permit a UTF-8 BOM; the rest of this pilot format is printable ASCII.
    if (got >= 3 && std::memcmp(cursor, "\xEF\xBB\xBF", 3) == 0) cursor += 3;
    while (*cursor) {
        char* next = std::strchr(cursor, '\n');
        if (next) *next++ = 0;
        char* comment = std::strchr(cursor, ';');
        if (comment) *comment = 0;
        char* line = Trim(cursor);
        if (*line == '[') {
            auto n = std::strlen(line);
            if (n < 3 || line[n - 1] != ']') return "bad_section";
            line[n - 1] = 0;
            const char* name = line + 1;
            if (std::strcmp(name, "Preview") == 0) {
                if (sawGlobal || gProfileCount) return "duplicate_or_late_preview_section";
                sawGlobal = globalSection = true;
                profile = nullptr;
            } else {
                if (!sawGlobal || gProfileCount >= kProfiles || std::strlen(name) >= sizeof(Profile::name)) return "bad_profile_section";
                for (const char* p = name; *p; ++p)
                    if (!(*p >= 'a' && *p <= 'z') && !(*p >= '0' && *p <= '9') && *p != '-' && *p != '_') return "bad_profile_name";
                for (unsigned i = 0; i < gProfileCount; ++i)
                    if (!std::strcmp(gProfiles[i].name, name)) return "duplicate_profile";
                profile = &gProfiles[gProfileCount++];
                strcpy_s(profile->name, name);
                globalSection = false;
            }
        } else if (*line) {
            char* equals = std::strchr(line, '=');
            if (!equals) return "missing_equals";
            *equals = 0;
            char* key = Trim(line);
            char* value = Trim(equals + 1);
            unsigned bit = 0;
            double number{};
            if (globalSection) {
                if (!Number(value, number)) return "bad_preview_number";
                if (!std::strcmp(key, "schema")) { bit = 1; if (number != 2) return "unsupported_schema"; }
                else if (!std::strcmp(key, "enabled")) { bit = 2; if (number != 0 && number != 1) return "bad_enabled"; enabled = number == 1; }
                else if (!std::strcmp(key, "donor_units_per_metre")) { bit = 4; if (number < 1 || number > 1000) return "bad_unit_scale"; gUnitsPerMetre = number; }
                else if (!std::strcmp(key, "max_matches")) { bit = 8; if (number < 1 || number > kShots || std::floor(number) != number) return "bad_match_limit"; gMaxShots = static_cast<unsigned>(number); }
                else return "unknown_preview_key";
                if (globalFields & bit) return "duplicate_preview_key";
                globalFields |= bit;
            } else if (profile) {
                if (!std::strcmp(key, "weapon")) { bit = 1; if (!ParseKey(value, profile->weapon)) return "bad_weapon_key"; }
                else if (!std::strcmp(key, "ammo")) { bit = 2; if (!ParseKey(value, profile->ammo)) return "bad_ammo_key"; }
                else if (!std::strcmp(key, "projectile")) { bit = 4; if (!ParseKey(value, profile->projectile)) return "bad_projectile_key"; }
                else if (!std::strcmp(key, "source_projectile")) { bit = 64; if (!ParseKey(value, profile->original)) return "bad_source_projectile_key"; }
                else {
                    if (!Number(value, number)) return "bad_profile_number";
                    if (!std::strcmp(key, "maximum_velocity_mps")) { bit = 8; if (number <= 0 || number > 10000) return "bad_maximum_velocity"; profile->maximum = number; }
                    else if (!std::strcmp(key, "barrel_in")) { bit = 16; if (number <= 0 || number > 1000) return "bad_barrel_length"; profile->barrel = number; }
                    else if (!std::strcmp(key, "peak_travel_in")) { bit = 32; if (number < 0 || number > 100) return "bad_peak_travel"; profile->peak = number; }
                    else if (!std::strcmp(key,"drag_model")) { bit=128; if (number!=1 && number!=7) return "bad_drag_model"; profile->dragModel=static_cast<unsigned>(number); }
                    else if (!std::strcmp(key,"ballistic_coefficient")) { bit=256; if (number<0.05 || number>2) return "bad_ballistic_coefficient"; profile->bc=number; }
                    else if (!std::strcmp(key,"select_on_fire")) { bit=512; if (number!=0 && number!=1) return "bad_select_on_fire"; profile->selectOnFire=number==1; }
                    else if (!std::strcmp(key,"flight_enabled")) { bit=1024; if (number!=0 && number!=1) return "bad_flight_enabled"; profile->flightEnabled=number==1; }
                    else return "unknown_profile_key";
                }
                if (profile->fields & bit) return "duplicate_profile_key";
                profile->fields |= bit;
            } else return "key_outside_section";
        }
        if (!next) break;
        cursor = next;
    }
    if (globalFields != 15 || !gProfileCount) return "incomplete_preview";
    for (unsigned i = 0; i < gProfileCount; ++i) {
        auto& p = gProfiles[i];
        if (p.fields != 2047) return "incomplete_profile";
        // BallistXMain's barrel relation, at its fixed reference temperature.
        // Source-data muzzle preview must match the supplied private record.
        p.muzzle = p.maximum * p.barrel / (p.barrel + 2 * p.peak);
        if (!std::isfinite(p.muzzle) || p.muzzle < 10 || p.muzzle > 1600) return "invalid_muzzle_preview";
    }
    return nullptr;
}
bool LoadMods() noexcept
{
    // Pinned xNVSE GameData.h/.cpp. Guarded game/JIP layout must be ready
    // before touching this address. Read data only; no fixed-address calls.
    void* handler{};
    U32 count{};
    if (!nvo::hit::ReadBytes(reinterpret_cast<void*>(0x11C3F2C), &handler, 4)
        || !ReadAt(handler, 0x218, count) || !count || count > 255) return false;
    for (U32 i = 0; i < count; ++i) {
        void* mod{};
        if (!ReadAt(handler, 0x21C + 4 * i, mod)
            || !ReadAt(mod, 0x20, gMods[i].name) || !std::memchr(gMods[i].name, 0, 260)
            || !ReadAt(mod, 0x40C, gMods[i].index) || gMods[i].index != i || !gMods[i].name[0]) return false;
        for (U32 j = 0; j < i; ++j) if (!_stricmp(gMods[j].name, gMods[i].name)) return false;
    }
    if (_stricmp(gMods[0].name, "FalloutNV.esm")) return false;
    gModCount = count;
    return true;
}
int ModIndex(const char* name) noexcept
{
    for (unsigned i = 0; i < gModCount; ++i) if (!_stricmp(gMods[i].name, name)) return gMods[i].index;
    return -1;
}
bool Resolve(Key& key) noexcept
{
    const int index = ModIndex(key.plugin);
    if (index < 0 || index >= 255) return false;
    key.resolved = (static_cast<U32>(index) << 24) | key.local;
    return true;
}
const char* CacheProjectiles() noexcept
{
    // DataHandler::projectileList (+140), read once per load, with a bounded
    // tList traversal. No engine allocation or LookupForm call is required.
    void* handler{};
    if (!nvo::hit::ReadBytes(reinterpret_cast<void*>(0x11C3F2C),&handler,4) || !handler)
        return "projectile_list_unavailable";
    void* node=static_cast<char*>(handler)+0x140;
    unsigned visited=0;
    while (node && visited++<65536) {
        void *form{},*next{}; nvo::hit::Form identity{};
        if (!ReadAt(node,0,form) || !ReadAt(node,4,next)
            || !nvo::hit::ReadForm(form,identity) || (form && identity.type!=0x33))
            return "projectile_list_layout";
        for (unsigned i=0;i<gProfileCount;++i) {
            auto& p=gProfiles[i];
            if (identity.id==p.original.resolved) p.originalPointer=form;
            if (identity.id==p.projectile.resolved) { p.result.form=form; p.result.type=2; }
        }
        node=next;
    }
    if (node) return "projectile_list_limit";
    for (unsigned i=0;i<gProfileCount;++i) {
        auto& p=gProfiles[i];
        if (!p.originalPointer || !p.result.form || !ReadAt(p.originalPointer,0x60,p.originalData)
            || !ReadAt(p.result.form,0x60,p.replacementData)) return "profile_projectile_missing";
        unsigned short flags{},type{},oldFlags{}; float gravity{},speed{};
        std::memcpy(&flags,p.replacementData,2); std::memcpy(&type,p.replacementData+2,2);
        std::memcpy(&gravity,p.replacementData+4,4); std::memcpy(&speed,p.replacementData+8,4);
        std::memcpy(&oldFlags,p.originalData,2);
        if (type!=1 || (flags&0x403) || gravity!=0 || !std::isfinite(speed)
            || std::abs(speed/(p.muzzle*gUnitsPerMetre)-1)>0.000003)
            return "private_projectile_flight_settings";
        if (p.selectOnFire) {
            if (p.original.resolved==p.projectile.resolved || (oldFlags&0x402)
                || flags!=(oldFlags&~1u) || std::memcmp(p.originalData+2,p.replacementData+2,2)
                || std::memcmp(p.originalData+12,p.replacementData+12,72))
                return "replacement_has_unexpected_changes";
        } else if (p.original.resolved!=p.projectile.resolved) return "unused_source_projectile";
    }
    return nullptr;
}
void SelectionSkip(const char* reason,U32 weapon,U32 ammo) noexcept
{
    ++gSelectionSkipped;
    if (gSelectionSkipRows++<16) nvo::log::Write("FLIGHT_SELECT_SKIP session=%u reason=%s weapon=%08X ammo=%08X source_projectile_retained=1",
        gSession,reason,weapon,ammo);
}
bool EquippedAmmo(void* actor,void* weapon,U32& ammo) noexcept
{
    // Strict subset of JIP TESObjectWEAP::GetEquippedAmmo: require a live
    // high/middle-high process, matching weapon entry and real ammo entry.
    // No default-ammo guess when the actor is unequipped or the state is absent.
    void *process{},*weaponEntry{},*ammoEntry{},*equipped{},*round{};
    unsigned char level{}; nvo::hit::Form form{};
    return ReadAt(actor,0x68,process) && process && ReadAt(process,0x28,level) && level<=1
        && ReadAt(process,0x114,weaponEntry) && ReadAt(weaponEntry,8,equipped) && equipped==weapon
        && ReadAt(process,0x118,ammoEntry) && ReadAt(ammoEntry,8,round)
        && nvo::hit::ReadForm(round,form) && form.type==0x29 && (ammo=form.id)!=0;
}
bool WriteKitFile(bool ready) noexcept
{
    // A user-executed console batch, not an automatic inventory grant. Rebuild
    // from this load's indices; invalidate it on an unavailable capture. The
    // reserved output is the only new file written, never an engine object.
    if (!gRoot[0]) return false;
    wchar_t path[32768]{};
    if (wcscpy_s(path, gRoot) || wcscat_s(path, L"NVOFlightPilot.txt")) return false;
    char commands[256]{};
    int length = 0;
    const int index = ModIndex("NVOFlightPilot.esp");
    if (ready) {
        if (index < 0 || index >= 255) return false;
        const U32 prefix = static_cast<U32>(index) << 24;
        length = sprintf_s(commands, "player.additem %08X 1\r\nplayer.additem %08X 1\r\nplayer.additem %08X 40\r\nplayer.additem %08X 40\r\n",
            prefix | 0x800u, prefix | 0x801u, prefix | 0x802u, prefix | 0x803u);
        if (length <= 0) return false;
    }
    // Check the opened file before truncating, so links cannot redirect writes.
    HANDLE file = CreateFileW(path, GENERIC_WRITE, 0, nullptr, OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OPEN_REPARSE_POINT, nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;
    BY_HANDLE_FILE_INFORMATION info{};
    LARGE_INTEGER zero{};
    DWORD written{};
    const bool writable = GetFileInformationByHandle(file, &info) && info.nNumberOfLinks == 1
        && !(info.dwFileAttributes & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DIRECTORY));
    bool ok = writable && SetFilePointerEx(file, zero, nullptr, FILE_BEGIN) && SetEndOfFile(file);
    if (ok && length) ok = WriteFile(file, commands, static_cast<DWORD>(length), &written, nullptr)
        && written == static_cast<DWORD>(length);
    if (!ok && writable) { SetFilePointerEx(file, zero, nullptr, FILE_BEGIN); SetEndOfFile(file); }
    CloseHandle(file);
    return ok;
}
bool SnapshotOf(void* projectile, Snapshot& s) noexcept
{
    nvo::hit::Form ref{}, base{}, weapon{}, source{};
    void *basePointer{}, *weaponPointer{}, *sourcePointer{};
    // Missile references only in this first pilot; do not reinterpret beams.
    if (!nvo::hit::ReadForm(projectile, ref) || ref.type != 0x3D
        || !ReadAt(projectile, 0x20, basePointer) || !nvo::hit::ReadForm(basePointer, base) || base.type != 0x33
        || !ReadAt(projectile, 0xF8, weaponPointer) || !nvo::hit::ReadForm(weaponPointer, weapon) || weapon.type != 0x28
        || !ReadAt(projectile, 0xFC, sourcePointer) || !nvo::hit::ReadForm(sourcePointer, source)
        || !ReadAt(basePointer, 0x60, s.flags) || !ReadAt(basePointer, 0x62, s.type)
        || !ReadAt(basePointer, 0x64, s.gravity) || !ReadAt(basePointer, 0x68, s.speed)
        || !ReadAt(basePointer, 0x6C, s.range) || !ReadAt(projectile, 0xD0, s.mult)
        || !ReadAt(projectile, 0xD8, s.time) || !ReadAt(projectile, 0x110, s.distance)) return false;
    s.ref = ref.id; s.base = base.id; s.weapon = weapon.id; s.source = source.id;
    return s.type == 1 && std::isfinite(s.gravity) && s.gravity >= 0 && s.gravity <= 1000
        && std::isfinite(s.speed) && s.speed >= 0 && s.speed <= 1e9f
        && std::isfinite(s.range) && s.range >= 0 && s.range <= 1e12f
        && std::isfinite(s.mult) && s.mult >= 0 && s.mult <= 1000
        && std::isfinite(s.time) && s.time >= 0 && s.time <= 1e7f
        && std::isfinite(s.distance) && s.distance >= 0 && s.distance <= 1e12f;
}
RangeObservation ReadRange(void* projectile) noexcept
{
    // Optional diagnostics only, after the existing lifetime/identity checks.
    // D4 is fRange in Stewie/ITR and is seeded/multiplied in the saved engine
    // route 009BDD10..009BDDC0. Do not use 14C: that field gates passing sound.
    // A failed read never gates tracking, movement or existing event handling.
    RangeObservation r{};
    if (ReadAt(projectile, 0xD4, r.range) && std::isfinite(r.range) && r.range >= 0 && r.range <= 1e12f)
        r.valid |= 1;
    else r.range = 0;
    if (ReadAt(projectile, 0xC8, r.flags)) r.valid |= 2;
    if (ReadAt(projectile, 0x90, r.impacted)) r.valid |= 4;
    return r;
}
void LogRange(const Shot& shot, const Snapshot& state, const RangeObservation& r, const char* phase) noexcept
{
    ++gRangeRows;
    if (r.valid != 7) ++gRangeReadFailures;
    const bool rangeKnown = (r.valid & 1) != 0;
    const bool startKnown = (shot.launchRange.valid & 1) != 0;
    const bool ratioKnown = rangeKnown && state.range > 0;
    const double remaining = rangeKnown ? static_cast<double>(r.range) - state.distance : 0;
    // First 32 matched lifetimes only, at create/first impact/destroy (<=96
    // attempts/load). No per-frame rows and no added console message.
    if (!nvo::log::Write("FLIGHT_RANGE session=%u lifetime=%llu phase=%s projectile=%08X source=%08X weapon=%08X ammo=%08X base=%08X valid_mask=%u base_range=%.9g instance_range=%.9g launch_valid_mask=%u launch_range=%.9g instance_to_base=%.9g ratio_known=%u range_changed=%u life_s=%.9g travel_units=%.9g range_minus_travel=%.9g range_reached=%u flags=%08X launch_flags=%08X impacted=%u impact_seen=%u cause=unverified observer_writes=0",
        gSession, shot.serial, phase, state.ref, state.source, state.weapon, gProfiles[shot.profile].ammo.resolved, state.base,
        r.valid, static_cast<double>(state.range), static_cast<double>(r.range), shot.launchRange.valid,
        static_cast<double>(shot.launchRange.range), ratioKnown ? static_cast<double>(r.range) / state.range : 0,
        ratioKnown ? 1u : 0u, rangeKnown && startKnown && r.range != shot.launchRange.range ? 1u : 0u,
        static_cast<double>(state.time), static_cast<double>(state.distance), remaining,
        rangeKnown && r.range > 0 && state.distance >= r.range ? 1u : 0u,
        r.flags, shot.launchRange.flags, static_cast<unsigned>(r.impacted), shot.impacted ? 1u : 0u)) ++gRangeLogFailures;
}
void Skip(const char* why, U32 weapon, U32 ammo, U32 base) noexcept
{
    ++gSkipped;
    if (gSkipRows++ < kSkipRows)
        nvo::log::Write("FLIGHT_PREVIEW_SKIP session=%u reason=%s weapon=%08X ammo=%08X projectile_base=%08X preview_writes=0",
            gSession, why, weapon, ammo, base);
}
} // namespace

void nvo::flight::BeginCapture(unsigned session, bool layoutReady, bool selectorReady) noexcept
{
    const ErrorGuard guard;
    gActive = false; gSession = session;
    gProfileCount = gModCount = gSeen = gMatched = gSkipped = gReadFailures = gMismatch = 0;
    gCreateRows = gImpactRows = gDestroyRows = gSkipRows = 0;
    gRangeRows = gRangeReadFailures = gRangeLogFailures = 0;
    gSelected=gSelectionSkipped=gSelectionSkipRows=gSelectionOtherThread=0;
    gSelectorReady=false; gCaptureThread=GetCurrentThreadId();
    for (auto& p : gProfiles) p = {};
    for (auto& m : gMods) m = {};
    for (auto& s : gShots) s = {};
    bool enabled = false;
    const char* reason = !layoutReady ? "projectile_layout_guard_unavailable" : LoadConfig(enabled);
    gKitNoticePending.store(false);
    // Even when the layout guard fails, derive the output path without touching
    // game layouts, so an earlier load's form indices cannot be reused.
    if (!layoutReady) {
        const DWORD n = GetModuleFileNameW(nullptr, gRoot, static_cast<DWORD>(std::size(gRoot)));
        wchar_t* slash = n && n < std::size(gRoot) ? std::wcsrchr(gRoot, L'\\') : nullptr;
        if (slash) slash[1] = 0; else gRoot[0] = 0;
    }
    const bool kitCleared = WriteKitFile(false);
    if (!reason && !enabled) reason = "disabled_by_config";
    if (!reason && !LoadMods()) reason = "loaded_mod_layout_or_identity_mismatch";
    if (!reason) for (unsigned i = 0; i < gProfileCount; ++i) {
        auto& p = gProfiles[i];
        if (!Resolve(p.weapon) || !Resolve(p.ammo) || !Resolve(p.projectile) || !Resolve(p.original)) { reason = "profile_plugin_not_loaded"; break; }
        for (unsigned j = 0; j < i; ++j) {
            const auto& q = gProfiles[j];
            if (p.weapon.resolved == q.weapon.resolved && p.ammo.resolved == q.ammo.resolved
                && p.projectile.resolved == q.projectile.resolved) reason = "duplicate_resolved_match";
            if (p.selectOnFire && q.selectOnFire && p.weapon.resolved==q.weapon.resolved
                && p.ammo.resolved==q.ammo.resolved && p.original.resolved==q.original.resolved)
                reason="duplicate_selection_match";
        }
    }
    if (!reason) reason=CacheProjectiles();
    if (reason) {
        nvo::log::Write("FLIGHT_PREVIEW_DISABLED session=%u reason=%s preview_writes=0 damage_writes=0", session, reason);
        if (!gWarned && std::strcmp(reason, "disabled_by_config")) {
            gWarned = true;
            gNoticePending.store(true);
        }
        return;
    }
    gActive = true;
    nvo::log::Write("FLIGHT_OWNER_AUDIT session=%u ballistx_plugin_loaded=%u ballistx_ammo_plugin_loaded=%u pbb_loose_loader_present=%u cbd_loose_loader_present=%u scope=loaded_names_and_loose_paths execution_or_bsa_audit=unverified native_flight_authority=see_PHYSICS_READY",
        session, ModIndex("BallistX.esp") >= 0 ? 1u : 0u, ModIndex("BallistXAmmo.esp") >= 0 ? 1u : 0u,
        FilePresent(L"Data\\NVSE\\Plugins\\scripts\\gr_PBBmain.txt") ? 1u : 0u,
        FilePresent(L"Data\\NVSE\\Plugins\\scripts\\ln_CBDredux.txt") ? 1u : 0u);
    nvo::log::Write("FLIGHT_PREVIEW_READY session=%u profiles=%u max_matches=%u config=NVOFlightPreview.ini donor_units_per_metre=%.6g unit_scale_verified=0 temperature_k=288.15 preview_writes=0 damage_writes=0",
        session, gProfileCount, gMaxShots, gUnitsPerMetre);
    for (unsigned i = 0; i < gProfileCount; ++i) {
        const auto& p = gProfiles[i];
        nvo::log::Write("FLIGHT_PROFILE session=%u profile=%s weapon=%08X ammo=%08X projectile_base=%08X maximum_mps=%.6g barrel_in=%.6g peak_travel_in=%.6g muzzle_preview_mps=%.6g source_projectile=%08X select_on_fire=%u flight_enabled=%u drag_model=G%u bc=%.9g live_match=pending",
            session, p.name, p.weapon.resolved, p.ammo.resolved, p.projectile.resolved, p.maximum, p.barrel, p.peak, p.muzzle,
            p.original.resolved,p.selectOnFire?1u:0u,p.flightEnabled?1u:0u,p.dragModel,p.bc);
    }
    const bool kitReady = kitCleared && WriteKitFile(true);
    nvo::log::Write("FLIGHT_PILOT_KIT session=%u ready=%u file=NVOFlightPilot.txt command=bat_NVOFlightPilot auto_grant=0 preview_writes=0 isolated_record_flight=1 damage_replacement=0",
        session, kitReady ? 1u : 0u);
    if (kitReady && !gKitNotified) { gKitNotified = true; gKitNoticePending.store(true); }
    nvo::timing::BeginCapture(session); nvo::physics::BeginCapture(session);
    gSelectorReady=selectorReady && nvo::physics::Ready(gUnitsPerMetre);
    nvo::log::Write("FLIGHT_SELECTOR_READY session=%u ready=%u event_bound=%u thread=%u method=ShowOff_OnPreProjectileCreate shared_record_writes=0 stock_record_overrides=0 damage_replacement=0",
        session,gSelectorReady?1u:0u,selectorReady?1u:0u,gCaptureThread);
    if (!gSelectorReady && !gWarned) { gWarned=true; gNoticePending.store(true); }
}
nvo::observer::FormResult* nvo::flight::SelectProjectile(void* actor,void* projectileBase,void* weapon) noexcept
{
    const ErrorGuard guard;
    if (!gActive || !gSelectorReady) return nullptr;
    // xNVSE's result slot is shared. Only return a form on the capture/main
    // thread; callbacks elsewhere retain the caller's original projectile.
    if (GetCurrentThreadId()!=gCaptureThread) { ++gSelectionOtherThread; return nullptr; }
    nvo::hit::Form w{},a{},b{};
    if (!nvo::hit::ReadForm(weapon,w) || w.type!=0x28) return nullptr;
    bool known=false;
    for (unsigned i=0;i<gProfileCount;++i)
        if (gProfiles[i].selectOnFire && gProfiles[i].flightEnabled && gProfiles[i].weapon.resolved==w.id) known=true;
    if (!known) return nullptr;
    U32 ammo{};
    if (!nvo::hit::ReadForm(actor,a) || (a.type!=0x3B && a.type!=0x3C)
        || !nvo::hit::ReadForm(projectileBase,b) || b.type!=0x33 || !EquippedAmmo(actor,weapon,ammo)) {
        SelectionSkip("equipped_ammo_unavailable",w.id,ammo); return nullptr;
    }
    for (unsigned i=0;i<gProfileCount;++i) {
        auto& p=gProfiles[i];
        if (!p.selectOnFire || !p.flightEnabled || w.id!=p.weapon.resolved || ammo!=p.ammo.resolved
            || b.id!=p.original.resolved || projectileBase!=p.originalPointer) continue;
        unsigned char current[84]{},replacement[84]{}; nvo::hit::Form r{};
        if (!nvo::physics::Ready(gUnitsPerMetre) || !nvo::hit::ReadForm(p.result.form,r)
            || r.type!=0x33 || r.id!=p.projectile.resolved || !ReadAt(projectileBase,0x60,current)
            || !ReadAt(p.result.form,0x60,replacement) || std::memcmp(current,p.originalData,84)
            || std::memcmp(replacement,p.replacementData,84)) {
            SelectionSkip("profile_changed_or_physics_unavailable",w.id,ammo); return nullptr;
        }
        ++gSelected;
        if (gSelected<=32) nvo::log::Write("FLIGHT_SELECT session=%u selection=%u profile=%s source=%08X weapon=%08X ammo=%08X original=%08X replacement=%08X shared_record_writes=0 result_consumed=unverified",
            gSession,gSelected,p.name,a.id,w.id,ammo,b.id,r.id);
        return &p.result;
    }
    SelectionSkip("ammo_or_projectile_not_profiled",w.id,ammo);
    return nullptr;
}
void nvo::flight::EmitNotice(const nvse::ConsolePrefix* console) noexcept
{
    const ErrorGuard guard;
    nvo::timing::EmitNotice(console);
    if (gNoticePending.exchange(false) && console && console->version >= 2 && console->RunScriptLine)
        console->RunScriptLine("PrintC \"[NVO] Flight preview unavailable. See NVOCombatCore.log.\"", nullptr);
    if (gKitNoticePending.exchange(false) && console && console->version >= 2 && console->RunScriptLine)
        console->RunScriptLine("PrintC \"[NVO] Flight test kit: bat NVOFlightKit\"", nullptr);
}
void nvo::flight::Suspend(const char* reason) noexcept
{
    const ErrorGuard guard;
    if (gActive) nvo::log::Write("FLIGHT_SELECTION_SUMMARY session=%u reason=%s selected=%u skipped=%u other_thread_unchanged=%u shared_record_writes=0 damage_replacement=0",
        gSession,reason,gSelected,gSelectionSkipped,gSelectionOtherThread);
    gSelectorReady=false;
    nvo::physics::Suspend(reason);
    nvo::timing::Suspend(reason);
    if (gActive) {
        unsigned open = 0;
        for (const auto& s : gShots) if (s.serial) ++open;
        nvo::log::Write("FLIGHT_PREVIEW_SUMMARY session=%u reason=%s seen=%u matched=%u skipped=%u read_failures=%u identity_mismatches=%u create_rows=%u impact_rows=%u destroy_rows=%u open_samples=%u preview_writes=0 damage_writes=0",
            gSession, reason, gSeen, gMatched, gSkipped, gReadFailures, gMismatch, gCreateRows, gImpactRows, gDestroyRows, open);
        nvo::log::Write("FLIGHT_RANGE_SUMMARY session=%u reason=%s observation_rows=%u optional_read_failures=%u log_write_failures=%u max_lifetimes=%u max_rows_per_lifetime=3 range_offset=00D4 sound_range_014C_excluded=1 observer_writes=0",
            gSession, reason, gRangeRows, gRangeReadFailures, gRangeLogFailures, gMaxShots);
    }
    gActive = false;
    for (auto& s : gShots) s = {};
}
void nvo::flight::Create(void* projectile, U32 source, U32 weapon, U32 ammo, unsigned long long lifetime, bool tracked) noexcept
{
    const ErrorGuard guard;
    if (!gActive) return;
    ++gSeen;
    bool weaponKnown = false;
    for (unsigned i = 0; i < gProfileCount; ++i) if (gProfiles[i].weapon.resolved == weapon) weaponKnown = true;
    if (!weaponKnown) { Skip("unprofiled_weapon", weapon, ammo, 0); return; }
    if (!tracked || !lifetime) { Skip("untracked_lifetime", weapon, ammo, 0); return; }
    Snapshot state{};
    if (!SnapshotOf(projectile, state)) { ++gReadFailures; Skip("unsupported_or_unreadable_snapshot", weapon, ammo, 0); return; }
    if (state.source != source || state.weapon != weapon) { ++gMismatch; Skip("callback_identity_mismatch", weapon, ammo, state.base); return; }
    unsigned profile = gProfileCount;
    for (unsigned i = 0; i < gProfileCount; ++i)
        if (gProfiles[i].weapon.resolved == weapon && gProfiles[i].ammo.resolved == ammo && gProfiles[i].projectile.resolved == state.base) { profile = i; break; }
    if (profile == gProfileCount) { Skip(ammo ? "ammo_or_projectile_not_profiled" : "ammo_unknown", weapon, ammo, state.base); return; }
    ++gMatched;
    const auto& p = gProfiles[profile];
    if (p.flightEnabled && nvo::physics::Ready(gUnitsPerMetre))
        nvo::physics::Track(projectile,lifetime,source,weapon,ammo,state.base,profile,p.dragModel,p.bc);
    // At most the first 32 matches per capture get cached samples/log rows.
    // Bookkeeping for existing samples continues after this cap.
    if (gCreateRows >= gMaxShots) return;
    Shot* slot = nullptr;
    for (auto& s : gShots) if (!s.serial) { slot = &s; break; }
    if (!slot) { Skip("sample_capacity", weapon, ammo, state.base); return; }
    *slot = {lifetime, profile, state, false};
    ++gCreateRows;
    // Timing uses the same exact profile match, with the existing sample cap.
    if (p.flightEnabled && nvo::physics::Ready(gUnitsPerMetre))
        nvo::timing::Track(projectile, lifetime, state.ref, source, weapon, ammo, state.base, state.time, state.distance);
    const double settingSpeed = static_cast<double>(state.speed) * state.mult;
    nvo::log::Write("FLIGHT_PREVIEW session=%u lifetime=%llu profile=%s phase=create projectile=%08X source=%08X weapon=%08X ammo=%08X projectile_base=%08X base_flags=%04X hitscan=%u gravity_setting=%.6g range_setting=%.6g base_speed_setting=%.6g speed_multiplier=%.6g speed_setting_units_per_s=%.6g speed_setting_mps_assuming_donor_scale=%.6g muzzle_preview_mps=%.6g life_s=%.6g travel_units=%.6g preview_writes=0",
        gSession, lifetime, p.name, state.ref, source, weapon, ammo, state.base, static_cast<unsigned>(state.flags), state.flags & 1 ? 1u : 0u,
        static_cast<double>(state.gravity), static_cast<double>(state.range), static_cast<double>(state.speed), static_cast<double>(state.mult),
        settingSpeed, settingSpeed / gUnitsPerMetre, p.muzzle, static_cast<double>(state.time), static_cast<double>(state.distance));
    slot->launchRange = ReadRange(projectile);
    LogRange(*slot, state, slot->launchRange, "create");
}
void nvo::flight::EndSample(void* projectile, unsigned long long lifetime, bool destroyed) noexcept
{
    const ErrorGuard guard;
    nvo::physics::Event(projectile, lifetime, destroyed);
    nvo::timing::Event(projectile, lifetime, destroyed);
    if (!gActive || !lifetime) return;
    Shot* shot = nullptr;
    for (auto& s : gShots) if (s.serial == lifetime) { shot = &s; break; }
    if (!shot || (!destroyed && shot->impacted)) return;
    Snapshot state{};
    if (!SnapshotOf(projectile, state)) {
        ++gReadFailures;
        Skip("end_snapshot_unavailable", shot->start.weapon, gProfiles[shot->profile].ammo.resolved, shot->start.base);
    } else if (state.ref != shot->start.ref || state.base != shot->start.base || state.source != shot->start.source || state.weapon != shot->start.weapon) {
        ++gMismatch;
        Skip("end_identity_changed", state.weapon, 0, state.base);
    } else {
        const double dt = static_cast<double>(state.time) - shot->start.time;
        const double ds = static_cast<double>(state.distance) - shot->start.distance;
        const bool valid = !(state.flags & 1) && dt > 0.00001 && ds >= 0 && std::isfinite(ds / dt);
        const double mean = valid ? ds / dt : -1;
        nvo::log::Write("FLIGHT_TRAVEL session=%u lifetime=%llu profile=%s phase=%s life_delta_s=%.6g travel_delta_units=%.6g hitscan=%u mean_speed_valid=%u mean_travel_units_per_s=%.6g mean_travel_mps_assuming_donor_scale=%.6g source=engine_counters not_muzzle_measurement=1 preview_writes=0",
            gSession, lifetime, gProfiles[shot->profile].name, destroyed ? "destroy" : "impact", dt, ds, state.flags & 1 ? 1u : 0u,
            valid ? 1u : 0u, mean, valid ? mean / gUnitsPerMetre : -1);
        const auto range = ReadRange(projectile);
        LogRange(*shot, state, range, destroyed ? "destroy" : "impact");
        if (destroyed) ++gDestroyRows; else ++gImpactRows;
    }
    if (destroyed) *shot = {}; else shot->impacted = true;
}

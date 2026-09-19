#include "CopyCapture.hpp"
#include "ArmourSnapshot.hpp"
#include "ArmourSnapshotReader.hpp"
#include "ArmourCoverage.hpp"
#include "CurrentHit.hpp"
#include "HitTransaction.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <array>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

// Standalone x86 checks of production ArmourSnapshot.cpp. Only registered
// synthetic memory is readable; reader traversal and coverage are test doubles.
namespace {
using nvo::capture::ArmourReceipt;
using nvo::capture::ArmourStatus;
using nvo::armour::reader::Code;
using nvo::armour::reader::Snapshot;
unsigned checks{}, failures{}, readerCalls{}, coverageCalls{};
std::vector<std::string> logs;
std::array<unsigned char, 0x100> source{}, target{}, carrier{}, weapon{};
int process{};
nvo::hit::Data data{};
nvo::transaction::CopyScope scope{};
Snapshot answer{};
ArmourReceipt nested{};
enum class Action { None, MutateBoundary, ChangeLifecycle, Reenter };
Action action{};
bool readFailure{};

void Check(bool pass, const char* name)
{
    ++checks;
    if (!pass) { ++failures; std::printf("FAIL %s\n", name); }
}
bool Inside(const void* from, std::size_t size, const void* start, std::size_t length)
{
    const auto a = reinterpret_cast<std::uintptr_t>(from);
    const auto b = reinterpret_cast<std::uintptr_t>(start);
    return a >= b && size <= length && a - b <= length - size;
}
void Form(std::array<unsigned char, 0x100>& bytes, std::uint32_t id, unsigned char type)
{
    bytes.fill(0);
    std::memcpy(bytes.data(), &id, sizeof(id));
    bytes[4] = type;
}
bool NoPayload(const ArmourReceipt& r)
{ return r.items == 0 && !r.enumerationComplete && !r.stableDoubleRead; }
void Reset(unsigned session = 1)
{
    nvo::armour::Suspend("fixture_reset");
    logs.clear();
    readerCalls = coverageCalls = 0;
    readFailure = false; action = Action::None; nested = {};
    Form(source, 0x1234, 0x3B); Form(target, 0x2345, 0x3B);
    Form(carrier, 0x3456, 0x40); Form(weapon, 0x4567, 0x28);
    void* owner = &process;
    std::memcpy(target.data() + 0x68, &owner, sizeof(owner));
    data = {};
    data.source = source.data(); data.target = target.data();
    data.carrier = carrier.data(); data.weapon = weapon.data();
    data.region = 1; data.health = 15; data.flags = 0x20;
    scope = {};
    scope.generation = 7; scope.id = 101; scope.copyOrdinal = 3;
    scope.lifetime = 17; scope.session = session;
    scope.source = 0x1234; scope.target = 0x2345;
    scope.carrier = 0x3456; scope.weapon = 0x4567; scope.ammo = 0x5678;
    scope.region = data.region; scope.flags = data.flags;
    scope.thread = GetCurrentThreadId();
    scope.exactInput = scope.identityMatch = scope.processMatch = true;
    scope.mainThread = scope.valid = true;
    answer = {};
    answer.code = Code::CompleteWithArmour; answer.targetId = scope.target;
    answer.itemCount = 1; answer.enumerationComplete = answer.stableDoubleRead = true;
    answer.items[0].instanceToken = 0xABC; answer.items[0].formId = 0x123456;
    nvo::armour::QueueCapture(session); nvo::armour::Tick();
}
ArmourReceipt Observe()
{ return nvo::armour::Observe(&data, &process, scope); }
}

namespace nvo::hit {
bool ReadBytes(const void* from, void* to, std::size_t size) noexcept
{
    if (readFailure || !from || !to) return false;
    bool safe = Inside(from, size, &data, sizeof(data));
    for (const auto* block : {&source, &target, &carrier, &weapon})
        safe = safe || Inside(from, size, block->data(), block->size());
    if (!safe) return false;
    std::memcpy(to, from, size); return true;
}
bool ReadForm(void* form, Form& result) noexcept
{
    result = {};
    if (!form) return true;
    unsigned char bytes[5]{};
    if (!ReadBytes(form, bytes, sizeof(bytes))) return false;
    std::memcpy(&result.id, bytes, sizeof(result.id)); result.type = bytes[4];
    return result.id != 0;
}
}
namespace nvo::log {
bool Write(const char* format, ...) noexcept
{
    char line[4096]{};
    va_list args; va_start(args, format);
    const int result = vsnprintf_s(line, sizeof(line), _TRUNCATE, format, args);
    va_end(args);
    if (result < 0) return false;
    logs.emplace_back(line); return true;
}
}
namespace nvo::armour::reader {
Snapshot CaptureStable(const Memory&, const void*, std::uint32_t) noexcept
{
    ++readerCalls;
    const Action chosen = action; action = Action::None;
    if (chosen == Action::MutateBoundary) data.position[0] += 1;
    if (chosen == Action::ChangeLifecycle) {
        nvo::armour::Suspend("fixture_reload");
        nvo::armour::QueueCapture(scope.session + 1); nvo::armour::Tick();
    }
    if (chosen == Action::Reenter) {
        auto innerScope = scope; ++innerScope.copyOrdinal;
        nested = nvo::armour::Observe(&data, &process, innerScope);
    }
    return answer;
}
const char* Name(Code code) noexcept
{
    switch (code) {
    case Code::CompleteWithArmour: return "complete_with_armour";
    case Code::CompleteNoArmourObserved: return "complete_no_armour_observed";
    case Code::Unstable: return "unstable";
    default: return "fixture_reader_rejected";
    }
}
bool Complete(Code code) noexcept
{ return code == Code::CompleteWithArmour || code == Code::CompleteNoArmourObserved; }
}
namespace nvo::armour::coverage_log {
void Begin(unsigned) noexcept {}
void Suspend(const char*) noexcept {}
void Observe(unsigned, unsigned, std::uint64_t, const reader::Snapshot&) noexcept
{ ++coverageCalls; }
}

int main()
{
    using namespace nvo::capture;
    static_assert(!nvo::armour::kGameplayWrites && !nvo::armour::kSnapshotAuthority
        && !nvo::armour::kArmourPreview);
    const Key key{7, 101, 3, 1};
    Check(Complete(key) && Same(key, key), "complete diagnostic key compares equal");
    Check(!Complete({}) && !Same({}, {}), "empty keys never match");
    for (unsigned field = 0; field < 4; ++field) {
        auto missing = key, different = key;
        switch (field) {
        case 0: missing.generation = 0; ++different.generation; break;
        case 1: missing.transaction = 0; ++different.transaction; break;
        case 2: missing.copy = 0; ++different.copy; break;
        default: missing.session = 0; ++different.session; break;
        }
        Check(!Complete(missing) && !Same(key, missing), "each missing key field rejects");
        Check(!Same(key, different), "each different key field rejects");
    }
    std::uint64_t counter{};
    Check(Advance(counter) && counter == 1, "zero advances to first identity");
    counter = (std::numeric_limits<std::uint64_t>::max)() - 1;
    Check(Advance(counter) && counter == (std::numeric_limits<std::uint64_t>::max)(),
        "last unique identity can be assigned");
    Check(!Advance(counter) && counter == (std::numeric_limits<std::uint64_t>::max)(),
        "saturated counter cannot wrap or reuse identity");
    ArmourReceipt receipt{}; receipt.key = key; receipt.status = ArmourStatus::ReaderRejected;
    Check(Joined(key, true, receipt), "same-copy rejection receipt is still joinable diagnostic evidence");
    Check(!Joined(key, false, receipt), "invalidated current scope rejects receipt");
    auto other = key; ++other.copy;
    Check(!Joined(other, true, receipt), "next copy cannot reuse previous receipt");
    Check(!Joined(key, true, {}), "absent receipt cannot join");
    Check(std::strcmp(Name(static_cast<ArmourStatus>(999)), "invalid_receipt") == 0,
        "unknown status remains explicit");

    nvo::armour::Initialize(); Reset();
    const auto before = data;
    SetLastError(0x654321);
    const auto complete = Observe();
    Check(GetLastError() == 0x654321, "production observation preserves host error value");
    Check(complete.status == ArmourStatus::Complete && complete.items == 1
        && complete.enumerationComplete && complete.stableDoubleRead,
        "complete reader receipt retains bounded metadata");
    Check(Same(complete.key, nvo::transaction::CaptureKey(scope))
        && complete.readerEpoch != 0 && complete.sequence == 1,
        "production receipt carries exact originating diagnostic scope");
    Check(readerCalls == 1 && coverageCalls == 1
        && std::memcmp(&before, &data, sizeof(data)) == 0,
        "production observation forwards complete snapshot and does not mutate hit");
    ++scope.copyOrdinal;
    const auto next = Observe();
    Check(next.sequence == 2 && Same(next.key, nvo::transaction::CaptureKey(scope))
        && !Joined(nvo::transaction::CaptureKey(scope), true, complete),
        "repeated provider copy has a distinct receipt");

    Reset(); answer.code = Code::CompleteNoArmourObserved; answer.itemCount = 0;
    const auto empty = Observe();
    Check(empty.status == ArmourStatus::Complete && empty.items == 0
        && empty.enumerationComplete && empty.stableDoubleRead,
        "complete empty traversal means no observed armour, not verified bare skin");
    Reset(); answer = {}; answer.code = Code::ReadFailure;
    const auto failed = Observe();
    Check(failed.status == ArmourStatus::ReaderRejected && NoPayload(failed)
        && coverageCalls == 0 && Joined(nvo::transaction::CaptureKey(scope), true, failed),
        "reader failure returns same-copy hold with no snapshot payload");
    Reset(); scope.valid = false;
    Check(Observe().status == ArmourStatus::ScopeRejected && readerCalls == 0,
        "invalid transaction scope does not traverse");
    Reset(); scope.tainted = true;
    Check(Observe().status == ArmourStatus::ScopeRejected && readerCalls == 0,
        "tainted transaction scope does not traverse");
    Reset(); scope.mainThread = false;
    Check(Observe().status == ArmourStatus::ScopeRejected && readerCalls == 0,
        "scope without main-thread evidence does not traverse");
    Reset(); ++scope.session;
    Check(Observe().status == ArmourStatus::ScopeRejected && readerCalls == 0,
        "different capture session does not traverse");
    Reset(); scope.copyOrdinal = 0;
    Check(Observe().status == ArmourStatus::ScopeRejected && readerCalls == 0,
        "incomplete copy key does not traverse");
    Reset(); nvo::armour::Suspend("fixture_inactive");
    Check(Observe().status == ArmourStatus::ScopeRejected && readerCalls == 0,
        "suspended capture does not reuse prior eligibility");
    Reset(); ++scope.source;
    const auto boundary = Observe();
    Check(boundary.status == ArmourStatus::BoundaryRejected && NoPayload(boundary)
        && readerCalls == 0, "source identity mismatch rejects before reader");
    Reset(); readFailure = true;
    Check(Observe().status == ArmourStatus::BoundaryRejected && readerCalls == 0,
        "unreadable current hit rejects before reader");
    Reset(); void* wrongOwner = nullptr;
    std::memcpy(target.data() + 0x68, &wrongOwner, sizeof(wrongOwner));
    Check(Observe().status == ArmourStatus::BoundaryRejected && readerCalls == 0,
        "target owner-process mismatch rejects before reader");
    Reset(); target[4] = 0x3C;
    const auto unsupported = Observe();
    Check(unsupported.status == ArmourStatus::UnsupportedTarget && NoPayload(unsupported)
        && readerCalls == 0, "creature target never becomes a no-armour success");
    Reset(); ++scope.thread;
    Check(Observe().status == ArmourStatus::ForeignThread && readerCalls == 0,
        "actual calling thread must match recorded thread");
    Reset(); action = Action::MutateBoundary;
    const auto unstable = Observe();
    Check(unstable.status == ArmourStatus::ReaderRejected && NoPayload(unstable)
        && coverageCalls == 0, "changed hit boundary discards successful reader payload");
    Reset(); action = Action::Reenter;
    const auto recursive = Observe();
    Check(nested.status == ArmourStatus::Reentrant && NoPayload(nested) && readerCalls == 1,
        "nested observation returns explicit hold without another traversal");
    Check(recursive.status == ArmourStatus::ReaderRejected && NoPayload(recursive)
        && coverageCalls == 0, "reentrancy taints outer snapshot receipt");
    Reset(); action = Action::ChangeLifecycle;
    const auto stale = Observe();
    Check(stale.status == ArmourStatus::Stale && NoPayload(stale) && coverageCalls == 0,
        "reload during traversal discards former-generation receipt payload");
    Reset(2); const auto fresh = Observe();
    Check(fresh.status == ArmourStatus::Complete && fresh.sequence == 1
        && fresh.readerEpoch != complete.readerEpoch,
        "fresh capture generation restarts bounded sequence but not reader epoch");
    Reset();
    bool allAdmitted = true;
    for (unsigned i = 0; i < 64; ++i) {
        scope.copyOrdinal = i + 1;
        const auto item = Observe();
        allAdmitted = allAdmitted && item.status == ArmourStatus::Complete
            && item.sequence == i + 1;
    }
    ++scope.copyOrdinal;
    const auto exhausted = Observe();
    Check(allAdmitted && readerCalls == 64 && coverageCalls == 64,
        "reader diagnostic capacity admits exactly sixty-four attempts");
    Check(exhausted.status == ArmourStatus::LimitReached && NoPayload(exhausted),
        "capacity exhaustion never reuses latest successful snapshot");
    bool allDisabled = true;
    for (const auto& line : logs)
        allDisabled = allDisabled && line.find("snapshot_authority=1") == std::string::npos
            && line.find("gameplay_writes=1") == std::string::npos
            && line.find("armour_preview=1") == std::string::npos;
    Check(allDisabled, "production observations keep diagnostic authority disabled");
    nvo::armour::Suspend("fixture_finished");
    std::printf("RESULT checks=%u failures=%u\n", checks, failures);
    return failures ? 1 : 0;
}

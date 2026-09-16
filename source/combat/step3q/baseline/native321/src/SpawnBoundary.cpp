#include "SpawnBoundary.hpp"
#include "SpawnCall.hpp"
#include "CurrentHit.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <intrin.h>
#include <cstring>
#include <limits>

namespace {
using namespace nvo::spawn;
using U64 = unsigned long long;
constexpr std::uintptr_t kEngine = 0x009BCA60;
constexpr unsigned kHandlerRva=0x94870, kSlotRva=0x102924;
constexpr unsigned kReturnRva=0x9490A, kCreateRva=0x94850;
constexpr unsigned kDepthLimit=8, kDetailLimit=16;
SRWLOCK gLock=SRWLOCK_INIT;
struct Lock { Lock() noexcept { AcquireSRWLockExclusive(&gLock); } ~Lock() { ReleaseSRWLockExclusive(&gLock); } };
struct ErrorGuard { DWORD value=GetLastError(); ~ErrorGuard() { SetLastError(value); } };
HMODULE gProvider{};
Function gOriginal{}; // Set before the atomic publication, never cleared.
bool gAttempted{}, gInstalled{}, gActive{};
const char* gGuardReason="not_checked";
unsigned gSession{};
DWORD gCaptureThread{};
U64 gEpoch{}, gNextCall{};
struct Counters { U64 calls{}, paired{}, nullReturns{}, mismatched{}, nested{}, overflow{}, foreignThread{}, stale{}, unscoped{}, rows{}, logFailures{}; } gCounts;
struct Scope {
    Scope* parent{};
    U64 epoch{}, call{};
    unsigned depth{};
    bool observed{};
    Word base{}, source{}, weapon{};
    Receipt receipt{};
};
thread_local Scope* gScope{}; // Always stack-owned; never retained after return.
thread_local bool gAmbiguousChain{};

template<class T> bool Read(const void* p, unsigned offset, T& out) noexcept {
    return p && nvo::hit::ReadBytes(static_cast<const char*>(p)+offset,&out,sizeof(out));
}
U64 Hash(const unsigned char* p, unsigned size) noexcept {
    U64 h=14695981039346656037ull;
    for (unsigned i=0;i<size;++i) h=(h^p[i])*1099511628211ull;
    return h;
}
bool Image(const void* p, HMODULE module, bool executable) noexcept {
    MEMORY_BASIC_INFORMATION info{};
    if (!VirtualQuery(p,&info,sizeof(info)) || info.State!=MEM_COMMIT || info.Type!=MEM_IMAGE
        || info.AllocationBase!=module || (info.Protect&(PAGE_NOACCESS|PAGE_GUARD))) return false;
    return executable ? (info.Protect&(PAGE_EXECUTE|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY))!=0
        : (info.Protect&(PAGE_READWRITE|PAGE_WRITECOPY))!=0;
}
bool Branch(std::uintptr_t site, unsigned char opcode, std::uintptr_t target) noexcept {
    unsigned char b[5]{}; Word displacement{};
    if (!nvo::hit::ReadBytes(reinterpret_cast<void*>(site),b,5) || b[0]!=opcode) return false;
    std::memcpy(&displacement,b+1,4);
    return static_cast<Word>(site+5+displacement)==target;
}
bool ProviderCode() noexcept {
    gGuardReason="provider_metadata";
    IMAGE_DOS_HEADER dos{}; IMAGE_NT_HEADERS32 nt{};
    if (!gProvider || !Read(gProvider,0,dos) || dos.e_magic!=IMAGE_DOS_SIGNATURE
        || dos.e_lfanew<0x40 || dos.e_lfanew>0x1000 || !Read(gProvider,dos.e_lfanew,nt)
        || nt.Signature!=IMAGE_NT_SIGNATURE || nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_I386
        || nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR32_MAGIC
        || nt.FileHeader.TimeDateStamp!=0x69C84C9B || nt.OptionalHeader.SizeOfImage!=0x110000) return false;
    const auto base=reinterpret_cast<std::uintptr_t>(gProvider);
    gGuardReason="provider_handler_read";
    unsigned char code[159]{}, engine[64]{};
    if (!Image(reinterpret_cast<void*>(base+kHandlerRva),gProvider,true)
        || !Image(reinterpret_cast<void*>(base+kHandlerRva+158),gProvider,true)
        || !nvo::hit::ReadBytes(reinterpret_cast<void*>(base+kHandlerRva),code,sizeof(code))) return false;
    // Exactly the four HIGHLOW relocations in the complete inspected handler.
    for (unsigned offset : {0x11u,0x16u,0x1Bu,0x2Du}) {
        Word value{}; std::memcpy(&value,code+offset,4);
        value-=static_cast<Word>(base)-0x10000000u;
        std::memcpy(code+offset,&value,4);
    }
    gGuardReason="provider_handler_hash";
    if (Hash(code,sizeof(code))!=0x349CE445DFD63A6Eull) return false;
    gGuardReason="provider_firing_call";
    if (!Branch(0x5245BD,0xE8,base+kHandlerRva)) return false;
    gGuardReason="provider_create_hook";
    if (!Branch(0x9BD51D,0xE9,base+kCreateRva)) return false;
    gGuardReason="engine_entry_hash";
    if (!Image(reinterpret_cast<void*>(kEngine),GetModuleHandleW(nullptr),true)
        || !nvo::hit::ReadBytes(reinterpret_cast<void*>(kEngine),engine,sizeof(engine))
        || Hash(engine,sizeof(engine))!=0x1CE93E2A04BF00C2ull) return false;
    gGuardReason="passed";
    return true;
}

void Begin(Scope& s, const Arguments& a, void* caller) noexcept {
    const ErrorGuard error; const Lock lock;
    if (!gActive) return;
    if (s.depth>kDepthLimit) { gAmbiguousChain=true; ++gCounts.overflow; return; }
    if (reinterpret_cast<std::uintptr_t>(caller)!=reinterpret_cast<std::uintptr_t>(gProvider)+kReturnRva) return;
    if (gNextCall==(std::numeric_limits<U64>::max)()) { gActive=false; return; }
    s.epoch=gEpoch; s.call=++gNextCall; s.observed=true;
    ++gCounts.calls;
    if (s.depth>1) ++gCounts.nested;
    if (GetCurrentThreadId()!=gCaptureThread) ++gCounts.foreignThread;
    nvo::hit::Form b{}, actor{}, weapon{};
    nvo::hit::ReadForm(reinterpret_cast<void*>(a[0]),b);
    nvo::hit::ReadForm(reinterpret_cast<void*>(a[1]),actor);
    nvo::hit::ReadForm(reinterpret_cast<void*>(a[3]),weapon);
    s.base=b.id; s.source=actor.id; s.weapon=weapon.id;
}
void End(Scope& s, void* result) noexcept {
    const ErrorGuard error; const Lock lock;
    if (!s.observed) return;
    if (!gActive || s.epoch!=gEpoch) { ++gCounts.stale; return; }
    nvo::hit::Form form{}, base{}; void* basePointer{};
    // Do not dereference a returned address already reported destroyed, or an
    // ambiguous/unobserved object. Pointer equality alone is not proof of life.
    const bool readable=!gAmbiguousChain && result && s.receipt.creates==1 && !s.receipt.destroys
        && s.receipt.created==reinterpret_cast<std::uintptr_t>(result)
        && nvo::hit::ReadForm(result,form)
        && Read(result,0x20,basePointer) && nvo::hit::ReadForm(basePointer,base);
    const bool paired=readable && s.base && base.id==s.base
        && s.receipt.Matches(reinterpret_cast<std::uintptr_t>(result),form.id,s.source,s.weapon);
    if (!result) ++gCounts.nullReturns;
    else if (paired) ++gCounts.paired;
    else ++gCounts.mismatched;
    if (gCounts.rows<kDetailLimit) {
        ++gCounts.rows;
        if (!nvo::log::Write("SPAWN_BOUNDARY session=%u call=%llu depth=%u source=%08X weapon=%08X supplied_base=%08X returned_ref=%08X returned_base=%08X create_events=%u destroyed_inside=%u paired=%u returned_null=%u argument_writes=0 reservation_enabled=0 damage_replacement=0",
            gSession,s.call,s.depth,s.source,s.weapon,s.base,form.id,base.id,s.receipt.creates,s.receipt.destroys,paired?1u:0u,result?0u:1u)) ++gCounts.logFailures;
    }
}

// Ordinary, verified x86 cdecl ABI, not a naked detour. The provider supplies
// 64 stack bytes and cleans them after this returns. Forward them once, bitwise.
void* __cdecl Wrapper(Word a0,Word a1,Word a2,Word a3,Word a4,Word a5,Word a6,Word a7,
    Word a8,Word a9,Word a10,Word a11,Word a12,Word a13,Word a14,Word a15) {
    const Arguments a={a0,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15};
    Scope s{}; s.parent=gScope; s.depth=s.parent?s.parent->depth+1:1;
    if (!s.parent) gAmbiguousChain=false;
    // An unobserved/over-depth nested scope still hides its parent's receipt.
    gScope=&s;
    void* result{};
    __try {
        Begin(s,a,_ReturnAddress());
        result=Forward(gOriginal,a);
        End(s,result);
    } __finally {
        // Restore only our stack bookkeeping on normal or exceptional exit.
        // Exceptions are not caught or converted into a successful spawn.
        gScope=s.parent;
    }
    return result;
}
bool InstalledSlot() noexcept {
    Function value{};
    gGuardReason="continuation_ownership";
    return gInstalled && Read(gProvider,kSlotRva,value) && value==Wrapper && ProviderCode();
}
bool Install() noexcept {
    if (gAttempted) return InstalledSlot();
    gAttempted=true; gProvider=GetModuleHandleW(L"ShowOffNVSE.dll");
    if (!ProviderCode()) return false;
    gGuardReason="continuation_slot_or_target";
    auto* slot=reinterpret_cast<void* volatile*>(reinterpret_cast<char*>(gProvider)+kSlotRva);
    if ((reinterpret_cast<std::uintptr_t>(slot)&3) || !Image(const_cast<void**>(slot),gProvider,false)) return false;
    Function previous{};
    if (!Read(gProvider,kSlotRva,previous) || reinterpret_cast<std::uintptr_t>(previous)!=kEngine) return false;
    gOriginal=previous; // Publish immutable continuation before our wrapper.
    gGuardReason="continuation_publish_race";
    if (InterlockedCompareExchangePointer(slot,reinterpret_cast<void*>(Wrapper),reinterpret_cast<void*>(previous))
        !=reinterpret_cast<void*>(previous)) return false;
    gInstalled=true;
    if (InstalledSlot()) return true;
    // Restore only if we still own it; never overwrite a foreign replacement.
    InterlockedCompareExchangePointer(slot,reinterpret_cast<void*>(previous),reinterpret_cast<void*>(Wrapper));
    gInstalled=false;
    return false;
}
}

void nvo::spawn::BeginCapture(unsigned session,bool layoutReady) noexcept {
    const ErrorGuard error; const Lock lock;
    gActive=false; gSession=session; gCounts={}; gCaptureThread=GetCurrentThreadId();
    if (gEpoch==(std::numeric_limits<U64>::max)()) return;
    ++gEpoch;
    if (!layoutReady || !Install()) {
        nvo::log::Write("SPAWN_BOUNDARY_DISABLED session=%u reason=%s existing_flight_unchanged=1 damage_replacement=0",session,layoutReady?gGuardReason:"projectile_layout"); return;
    }
    gActive=true;
    nvo::log::Write("SPAWN_BOUNDARY_READY session=%u provider=ShowOff184 boundary=post_selection_pre_engine forwarded_stack_words=16 saved_target=009BCA60 depth_limit=8 detail_limit=16 execution_observed=0 reservation_enabled=0 damage_replacement=0",session);
}
void nvo::spawn::Suspend(const char* reason) noexcept {
    const ErrorGuard error; const Lock lock;
    if (gActive) nvo::log::Write("SPAWN_BOUNDARY_SUMMARY session=%u reason=%s calls=%llu paired=%llu null_returns=%llu mismatched=%llu nested=%llu depth_overflow=%llu other_thread=%llu stale_returns=%llu unscoped_creates=%llu detail_rows=%llu log_failures=%llu reservation_enabled=0 damage_replacement=0",
        gSession,reason,gCounts.calls,gCounts.paired,gCounts.nullReturns,gCounts.mismatched,gCounts.nested,gCounts.overflow,gCounts.foreignThread,gCounts.stale,gCounts.unscoped,gCounts.rows,gCounts.logFailures);
    gActive=false;
}
void nvo::spawn::Created(void* p,Word ref,Word source,Word weapon) noexcept {
    const ErrorGuard error; const Lock lock;
    if (!gActive) return;
    if (!gScope || !gScope->observed || gScope->epoch!=gEpoch) { ++gCounts.unscoped; return; }
    gScope->receipt.Create(reinterpret_cast<std::uintptr_t>(p),ref,source,weapon);
}
void nvo::spawn::Destroyed(void* p) noexcept {
    const ErrorGuard error; const Lock lock;
    if (!gActive) return;
    // A nested callback can destroy its parent's pending projectile. Inspect
    // at most eight stack-owned receipts, not the game world or retained refs.
    unsigned n=0;
    for (auto* s=gScope;s && n<kDepthLimit;s=s->parent,++n)
        if (s->observed && s->epoch==gEpoch) s->receipt.Destroy(reinterpret_cast<std::uintptr_t>(p));
}

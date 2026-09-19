#include "ActorValueObserver.hpp"
#include "CurrentHit.hpp"
#include "HitTransaction.hpp"
#include "NativeLog.hpp"
#include "DamageAttribution.hpp"
#include <Windows.h>
#include <atomic>
#include <cmath>
#include <cstring>

namespace {
using U32=std::uint32_t;
using U64=unsigned long long;
#include "ActorValueGuards.inl"
constexpr unsigned kDepth=16, kDetails=96;
SRWLOCK gLock=SRWLOCK_INIT;
struct Lock { Lock() noexcept { AcquireSRWLockExclusive(&gLock); } ~Lock(){ ReleaseSRWLockExclusive(&gLock); } };
struct ErrorGuard { DWORD value=GetLastError(); ~ErrorGuard(){ SetLastError(value); } };
struct Values {
    U32 id{}, table{}, owner{}, effective{};
    void* process{};
    float current{}, damage{};
    bool valid{};
};
struct Frame {
    std::uintptr_t caller{};
    void* receiver{};
    void* source{};
    U32 av{}, sourceId{};
    float requested{};
    U64 id{}, parent{}, generation{};
    unsigned session{}, nested{}, healthEvents{}, healthMismatches{};
    Values before{};
    nvo::transaction::Scope scope{};
    nvo::attribution::Route route{};
    nvo::attribution::Witness routeWitness{};
    bool detail{}, tainted{};
};
// Continuations must survive suspend/load boundaries until their own return.
__declspec(thread) Frame gFrames[kDepth];
__declspec(thread) unsigned gDepth;
__declspec(thread) bool gReading, gReadTainted;
void* gOriginal{};
DWORD gMainThread{};
bool gAttempted{}, gInstalled{}, gActive{}, gPending{};
bool gEpochValid{};
unsigned gSession{}, gRequestedSession{};
U64 gNextId{},gEntries{},gReturns{},gOpen{},gInvalid{},gOverflow{},gNested{},gDetailed{},gLogFailures{};
U64 gGeneration{},gScoped{},gUnscoped{},gRouteVerified{},gRouteUnresolved{},gHealthEvents{},gHealthMismatches{},gUnscopedHealth{};
std::atomic<U64> gOtherThread{0};

bool Watched(U32 av) noexcept { return av==16 || (av>=25 && av<=31); }
const ClassSpec* Class(U32 table) noexcept {
    for(const auto& c:kClasses) if(c.table==table)return &c;
    return nullptr;
}
// Only these public read interfaces are invoked, never a damage setter. The
// creature's own getter/remapper maps a requested condition to its actual AV.
[[maybe_unused]] bool ReadValuesRaw(void* actor,U32 av,Values& v) noexcept {
    __try {
        nvo::hit::Form form{};
        if(!nvo::hit::ReadForm(actor,form) || !form.id || (form.type!=0x3B && form.type!=0x3C)
            || !nvo::hit::ReadBytes(actor,&v.table,4))return false;
        const auto* c=Class(v.table);if(!c)return false;
        auto* owner=static_cast<char*>(actor)+0xA4;
        U32 getter{},modifier{};
        if(!nvo::hit::ReadBytes(owner,&v.owner,4) || v.owner!=c->owner
            || !nvo::hit::ReadBytes(reinterpret_cast<void*>(v.owner+0xC),&getter,4) || getter!=c->get
            || !nvo::hit::ReadBytes(reinterpret_cast<void*>(v.owner+0x14),&modifier,4) || modifier!=c->damage
            || !nvo::hit::ReadBytes(static_cast<char*>(actor)+0x68,&v.process,4) || !v.process)return false;
        v.id=form.id;v.effective=av;
        if(v.table==kClasses[1].table)
            v.effective=reinterpret_cast<U32(__thiscall*)(void*,U32)>(0x8D4A80)(actor,av);
        // 45 is the verified creature remapper's shared condition result.
        if(v.effective!=av && v.effective!=45)return false;
        using Getter=float(__thiscall*)(void*,U32);
        v.current=reinterpret_cast<Getter>(getter)(owner,av);
        v.damage=reinterpret_cast<Getter>(modifier)(owner,v.effective);
        return std::isfinite(v.current) && std::isfinite(v.damage);
    } __except(GetExceptionCode()==EXCEPTION_ACCESS_VIOLATION ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) {
        return false;
    }
}
#ifdef NVO_AV_OFFLINE_PROBE
// The standalone probe supplies an engine-read mock. This branch is not
// present in the DLL; its actual assembly bridges are compared separately.
bool ProbeReadValues(void*,U32,Values&) noexcept;
#endif
Values ReadValues(void* actor,U32 av) noexcept {
    Values v{};gReading=true;gReadTainted=false;
#ifdef NVO_AV_OFFLINE_PROBE
    v.valid=ProbeReadValues(actor,av,v);
#else
    v.valid=ReadValuesRaw(actor,av,v);
#endif
    v.valid=v.valid && !gReadTainted;
    gReading=false;return v;
}
bool Same(const Values& a,const Values& b) noexcept {
    return a.valid && b.valid && a.id==b.id && a.table==b.table && a.owner==b.owner
        && a.effective==b.effective && a.process==b.process;
}
struct RouteObservation {
    nvo::attribution::Route route{};
    nvo::attribution::Witness witness{};
};
RouteObservation ReadRoute(std::uintptr_t caller,U32 av) noexcept {
    using namespace nvo::attribution;
    for(const auto& site:kSites) {
        if(caller!=site.caller)continue;
        if((site.route==Route::HealthHelper && av!=16)
            || (site.route==Route::HitCondition && (av<25 || av>31)))
            return {Route::Unclassified,Witness::ArgumentMismatch};
        unsigned char bytes[41]{};
        if(!nvo::hit::ReadBytes(reinterpret_cast<void*>(site.begin),bytes,site.size))
            return {Route::Unclassified,Witness::BytesUnavailable};
        if(nvo::attribution::Hash(bytes,site.size)!=site.hash)
            return {Route::Unclassified,Witness::BytesMismatch};
        return {site.route,Witness::Verified};
    }
    return {};
}
void Summary(const char* reason) noexcept {
    nvo::log::Write("AV_APPLY_SUMMARY session=%u reason=%s entries=%llu returns=%llu open=%llu invalid=%llu depth_overflow=%llu nested_calls=%llu other_thread_passthrough=%llu detailed=%llu log_failures=%llu measurement=net_over_provider_call single_storage_write=unverified damage_replacement=0",
        gSession,reason,gEntries,gReturns,gOpen,gInvalid,gOverflow,gNested,gOtherThread.load(),gDetailed,gLogFailures);
    nvo::log::Write("AV_ATTRIBUTION_SUMMARY session=%u generation=%llu scoped=%llu unscoped=%llu route_verified=%llu route_unresolved=%llu health_callbacks=%llu callback_mismatches=%llu unscoped_health_callbacks=%llu component_verified=0 application_verified=0 additive_net=0 damage_replacement=0",
        gSession,gGeneration,gScoped,gUnscoped,gRouteVerified,gRouteUnresolved,gHealthEvents,gHealthMismatches,gUnscopedHealth);
}
bool __cdecl Before(void* receiver,U32 av,float delta,void* source,std::uintptr_t caller) noexcept {
    const ErrorGuard error;
    if(GetCurrentThreadId()!=gMainThread) { ++gOtherThread;return false; }
    unsigned session{};U64 generation{};
    {
        const Lock lock;
        if(!gActive || !gEpochValid)return false;
        // Flag every nested dispatch, even when the nested AV is not sampled.
        // Old continuations still unwind, but cannot become a new epoch's parents.
        bool nested{};
        for(unsigned i=0;i<gDepth;++i)if(gFrames[i].generation==gGeneration) {
            ++gFrames[i].nested;nested=true;
        }
        if(nested)++gNested;
        if(gReading) { gReadTainted=true;return false; }
        if(!Watched(av) || !std::isfinite(delta) || delta>=0)return false;
        if(gDepth>=kDepth) {
            ++gOverflow;for(auto& f:gFrames)f.tainted=true;return false;
        }
        session=gSession;generation=gGeneration;
    }
    // No observer lock while acquiring the transaction lock.
    const auto scope=nvo::transaction::MatchScope(receiver,source);
    const auto route=ReadRoute(caller,av);
    nvo::hit::Form sourceForm{};
    const bool sourceValid=nvo::hit::ReadForm(source,sourceForm);
    {
        const Lock lock;
        if(!gActive || !gEpochValid || session!=gSession || generation!=gGeneration)return false;
        if(!nvo::capture::Advance(gNextId)) {
            ++gInvalid;if(gDepth && gFrames[gDepth-1].generation==generation)gFrames[gDepth-1].tainted=true;return false;
        }
        auto& f=gFrames[gDepth];f={};
        f.id=gNextId;f.parent=gDepth && gFrames[gDepth-1].generation==generation ? gFrames[gDepth-1].id : 0;
        f.caller=caller;f.receiver=receiver;f.source=source;f.av=av;f.requested=delta;
        f.sourceId=sourceForm.id;f.session=session;f.generation=generation;f.scope=scope;
        f.route=route.route;f.routeWitness=route.witness;
        f.tainted=!sourceValid || (gDepth && gFrames[gDepth-1].generation==generation && gFrames[gDepth-1].tainted);
        f.detail=gDetailed<kDetails;if(f.detail)++gDetailed;
        ++gDepth;++gEntries;++gOpen;
        if(scope.matched)++gScoped;else ++gUnscoped;
        if(route.witness==nvo::attribution::Witness::Verified)++gRouteVerified;else ++gRouteUnresolved;
    }
    const auto before=ReadValues(receiver,av); // Engine getters outside locks.
    const Lock lock;
    auto& f=gFrames[gDepth-1];f.before=before;
    if(!gActive || !gEpochValid || session!=gSession || generation!=gGeneration) {
        f.tainted=true;return true; // The installed continuation must still unwind.
    }
    if(f.detail && !nvo::log::Write("AV_APPLY_BEGIN session=%u call=%llu parent=%llu tx=%llu scope_match=%u receiver=%08X source=%08X av=%u effective_av=%u requested=%.9g current_before=%.9g damage_before=%.9g read_valid=%u caller=%08X phase=before_itr observer_value_writes=0",
        session,f.id,f.parent,scope.matched?scope.id:0,scope.matched?1u:0u,before.id,f.sourceId,av,before.effective,
        static_cast<double>(delta),before.valid?static_cast<double>(before.current):0,
        before.valid?static_cast<double>(before.damage):0,before.valid?1u:0u,static_cast<U32>(caller)))++gLogFailures;
    if(f.detail && !nvo::log::Write("AV_ATTRIBUTION_BEGIN session=%u generation=%llu call=%llu tx=%llu tx_generation=%llu copies_seen=%llu lifetime=%llu carrier=%08X carrier_type=%02X carrier_kind=%s weapon=%08X ammo=%08X hit_flags=%08X hit_metadata_available=%u explosion_flag=%s critical_effect=%s context=%s route=%s route_witness=%s component_verified=0 application_verified=0 primary_or_secondary=unresolved observer_writes=0",
        session,generation,f.id,scope.matched?scope.id:0,scope.generation,scope.copiesObserved,scope.lifetime,
        scope.carrier,static_cast<unsigned>(scope.carrierType),scope.matched?nvo::attribution::Carrier(scope.carrierPresent,scope.carrier,scope.carrierType):"unresolved",
        scope.weapon,scope.ammo,scope.flags,scope.matched?1u:0u,
        !scope.matched?"unknown":nvo::attribution::ExplosionFlag(scope.flags)?"present":"absent",
        !scope.matched?"unknown":scope.criticalEffectPresent?"reference_present":"reference_absent",
        scope.matched?"matching_hit_scope":"no_matching_hit_scope",nvo::attribution::Name(f.route),nvo::attribution::Name(f.routeWitness)))++gLogFailures;
    return true;
}
std::uintptr_t __cdecl After() noexcept {
    const ErrorGuard error;
    auto& active=gFrames[gDepth-1];
    bool observe{};
    { const Lock lock;observe=gActive && gEpochValid && active.session==gSession && active.generation==gGeneration && !active.tainted; }
    Values after{};
    // First check raw identity without invoking a method on a changed object.
    if(observe) {
        nvo::hit::Form form{};U32 table{},owner{};void* process{};
        observe=active.before.valid && nvo::hit::ReadForm(active.receiver,form) && form.id==active.before.id
            && nvo::hit::ReadBytes(active.receiver,&table,4) && table==active.before.table
            && nvo::hit::ReadBytes(static_cast<char*>(active.receiver)+0xA4,&owner,4) && owner==active.before.owner
            && nvo::hit::ReadBytes(static_cast<char*>(active.receiver)+0x68,&process,4) && process==active.before.process;
        if(observe)after=ReadValues(active.receiver,active.av);
    }
    const auto scope=nvo::transaction::MatchScope(active.receiver,active.source);
    const Frame f=active;--gDepth;
    const Lock lock;
    if(gActive && gEpochValid && f.session==gSession && f.generation==gGeneration) {
        ++gReturns;--gOpen;
        const bool valid=!f.tainted && Same(f.before,after);
        const bool linked=f.scope.matched && scope.matched && f.scope.session==scope.session && f.scope.id==scope.id
            && f.scope.generation==scope.generation;
        if(!valid)++gInvalid;
        if(f.detail && !nvo::log::Write("AV_APPLY_END session=%u call=%llu tx=%llu scope_match=%u receiver=%08X av=%u effective_av=%u current_after=%.9g damage_after=%.9g net_current=%.9g net_damage=%.9g valid=%u nested=%u tainted=%u measurement=net_over_provider_call single_storage_write=unverified damage_replacement=0",
            f.session,f.id,linked?scope.id:0,linked?1u:0u,f.before.id,f.av,f.before.effective,
            valid?static_cast<double>(after.current):0,valid?static_cast<double>(after.damage):0,
            valid?static_cast<double>(after.current)-f.before.current:0,
            valid?static_cast<double>(after.damage)-f.before.damage:0,valid?1u:0u,f.nested,f.tainted?1u:0u))++gLogFailures;
        if(f.detail && !nvo::log::Write("AV_ATTRIBUTION_END session=%u generation=%llu call=%llu tx=%llu tx_generation=%llu scope_retained=%u copies_at_begin=%llu copies_at_end=%llu route=%s route_witness=%s health_callbacks=%u callback_mismatches=%u nested=%u valid=%u net_kind=%s additive_net=0 component_verified=0 application_verified=0 primary_or_secondary=unresolved single_storage_write=unverified observer_writes=0",
            f.session,f.generation,f.id,linked?scope.id:0,linked?scope.generation:0,linked?1u:0u,f.scope.copiesObserved,scope.copiesObserved,
            nvo::attribution::Name(f.route),nvo::attribution::Name(f.routeWitness),f.healthEvents,f.healthMismatches,f.nested,valid?1u:0u,
            f.nested?"inclusive_nested_window":"observed_call_window"))++gLogFailures;
    }
    return f.caller;
}
__declspec(naked) void ReturnBridge() {
    __asm {
        push 0
        pushfd
        pushad
        mov ebx,esp
        sub esp,528
        and esp,-16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp,4
        call After
        mov [ebx+36],eax
        fxrstor [esp]
        mov esp,ebx
        popad
        popfd
        ret
    }
}
__declspec(naked) void EntryBridge() {
    __asm {
        pushfd
        pushad
        mov ebx,esp
        sub esp,528
        and esp,-16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp,4
        push dword ptr [ebx+36]
        push dword ptr [ebx+48]
        push dword ptr [ebx+44]
        push dword ptr [ebx+40]
        push dword ptr [ebx+24]
        call Before
        add esp,20
        test al,al
        jz passthrough
        mov dword ptr [ebx+36],offset ReturnBridge
    passthrough:
        fxrstor [esp]
        mov esp,ebx
        popad
        popfd
        jmp dword ptr [gOriginal]
    }
}
bool Image(HMODULE module,U32 stamp,U32 size) noexcept {
    IMAGE_DOS_HEADER dos{};IMAGE_NT_HEADERS32 nt{};
    return module && nvo::hit::ReadBytes(module,&dos,sizeof(dos)) && dos.e_magic==IMAGE_DOS_SIGNATURE
        && dos.e_lfanew>=0x40 && dos.e_lfanew<=0x1000
        && nvo::hit::ReadBytes(reinterpret_cast<char*>(module)+dos.e_lfanew,&nt,sizeof(nt))
        && nt.Signature==IMAGE_NT_SIGNATURE && nt.FileHeader.Machine==IMAGE_FILE_MACHINE_I386
        && nt.OptionalHeader.Magic==IMAGE_NT_OPTIONAL_HDR32_MAGIC
        && nt.FileHeader.TimeDateStamp==stamp && nt.OptionalHeader.SizeOfImage==size;
}
bool Executable(const void* address,HMODULE module) noexcept {
    MEMORY_BASIC_INFORMATION info{};
    return VirtualQuery(address,&info,sizeof(info)) && info.State==MEM_COMMIT && info.Type==MEM_IMAGE
        && info.AllocationBase==module && !(info.Protect&(PAGE_GUARD|PAGE_NOACCESS))
        && (info.Protect&(PAGE_EXECUTE|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY));
}
U64 Hash(const unsigned char* bytes,unsigned size) noexcept {
    U64 hash=14695981039346656037ull;
    for(unsigned i=0;i<size;++i)hash=(hash^bytes[i])*1099511628211ull;
    return hash;
}
bool Guards(HMODULE itr,bool installed) noexcept {
    const auto game=GetModuleHandleW(nullptr);
    if(reinterpret_cast<U32>(game)!=0x400000 || !Image(game,0x4E0D50ED,0x107B000)
        || !Image(itr,0x6A948FDD,0xB3000))return false;
    const U32 base=reinterpret_cast<U32>(itr);
    unsigned char body[421]{};
    auto* provider=reinterpret_cast<char*>(itr)+0x34C1B;
    if(!Executable(provider,itr) || !Executable(provider+420,itr)
        || !nvo::hit::ReadBytes(provider,body,sizeof(body)))return false;
    for(unsigned offset:kProviderRelocations) {
        U32 value{};std::memcpy(&value,body+offset,4);value-=base-0x10000000;
        std::memcpy(body+offset,&value,4);
    }
    if(Hash(body,sizeof(body))!=kProviderHash)return false;
    for(const auto& c:kClasses) {
        U32 original{},dispatch{},getter{},modifier{};
        if(!nvo::hit::ReadBytes(reinterpret_cast<char*>(itr)+c.originalRva,&original,4) || original!=c.original
            || !nvo::hit::ReadBytes(reinterpret_cast<void*>(c.table+0x3AC),&dispatch,4)
            || dispatch!=(installed?reinterpret_cast<U32>(EntryBridge):base+0x34C1B)
            || !nvo::hit::ReadBytes(reinterpret_cast<void*>(c.owner+0xC),&getter,4) || getter!=c.get
            || !nvo::hit::ReadBytes(reinterpret_cast<void*>(c.owner+0x14),&modifier,4) || modifier!=c.damage)return false;
    }
    for(const auto& spec:kCode) {
        unsigned char code[128]{};
        if(spec.size>sizeof(code) || !Executable(reinterpret_cast<void*>(spec.address),game)
            || !Executable(reinterpret_cast<void*>(spec.address+spec.size-1),game)
            || !nvo::hit::ReadBytes(reinterpret_cast<void*>(spec.address),code,spec.size)
            || Hash(code,spec.size)!=spec.hash)return false;
    }
    return true;
}
void Disabled(const char* reason) noexcept {
    nvo::log::Write("AV_APPLY_DISABLED reason=%s damage_replacement=0",reason);
}
void Install() noexcept {
    if(gAttempted)return;gAttempted=true;
    const auto itr=GetModuleHandleW(L"itr-nvse.dll");
    if(!Guards(itr,false)){Disabled("unsupported_provider_or_method_guard");return;}
    gOriginal=reinterpret_cast<char*>(itr)+0x34C1B;MemoryBarrier();
    DWORD protection[3]{};unsigned protectedCount{},changed{};
    for(;protectedCount<3;++protectedCount)
        if(!VirtualProtect(reinterpret_cast<void*>(kClasses[protectedCount].table+0x3AC),4,PAGE_READWRITE,&protection[protectedCount]))break;
    bool ok=protectedCount==3 && Guards(itr,false);
    if(ok)for(;changed<3;++changed) {
        auto* slot=reinterpret_cast<PVOID volatile*>(kClasses[changed].table+0x3AC);
        if(InterlockedCompareExchangePointer(slot,reinterpret_cast<void*>(EntryBridge),gOriginal)!=gOriginal){ok=false;break;}
    }
    if(!ok)for(unsigned i=0;i<changed;++i)
        InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(kClasses[i].table+0x3AC),gOriginal,reinterpret_cast<void*>(EntryBridge));
    while(protectedCount) {
        unsigned i=--protectedCount;DWORD ignored{};
        if(!VirtualProtect(reinterpret_cast<void*>(kClasses[i].table+0x3AC),4,protection[i],&ignored))
            nvo::log::Write("AV_APPLY_PROTECTION_RESTORE_FAILED table=%08X",kClasses[i].table);
    }
    gInstalled=ok && Guards(itr,true);
    if(!gInstalled){Disabled("install_failed");return;}
    nvo::log::Write("AV_APPLY_HOOK_READY provider=ITR20202 tables=3 installed_at=deferred_init original_chain_calls=1 read_getters=1 gameplay_value_writes=0 damage_replacement=0");
}
} // namespace

void nvo::avobserve::Initialize() noexcept { const ErrorGuard error;gMainThread=GetCurrentThreadId();Install(); }
void nvo::avobserve::QueueCapture(unsigned session) noexcept {
    const Lock lock;gActive=false;gEpochValid=nvo::capture::Advance(gGeneration);gPending=gEpochValid;gRequestedSession=session;
}
void nvo::avobserve::Suspend(const char* reason) noexcept {
    const Lock lock;gPending=false;if(gActive)Summary(reason);gActive=false;gEpochValid=false;nvo::capture::Advance(gGeneration);
}
void nvo::avobserve::Tick() noexcept {
    const ErrorGuard error;unsigned session{};U64 generation{};
    { const Lock lock;if(!gPending)return;gPending=false;session=gRequestedSession;generation=gGeneration; }
    if(!gInstalled || !Guards(GetModuleHandleW(L"itr-nvse.dll"),true)){Disabled("capture_guard_failed");return;}
    const Lock lock;if(!gEpochValid || generation!=gGeneration)return;
    if(!nvo::capture::Advance(gGeneration)) {gEpochValid=false;return;}
    gSession=session;gEntries=gReturns=gOpen=gInvalid=gOverflow=gNested=gDetailed=gLogFailures=0;
    gScoped=gUnscoped=gRouteVerified=gRouteUnresolved=gHealthEvents=gHealthMismatches=gUnscopedHealth=0;
    gOtherThread=0;gActive=true;
    nvo::log::Write("AV_APPLY_READY session=%u generation=%llu main_thread=%lu max_depth=16 max_detail_calls=96 max_rows_per_detail=4 health_av=16 conditions=25..31 creature_remap=1 ids_independent_of_logging=1 measurement=net_over_provider_call damage_replacement=0",session,gGeneration,gMainThread);
}
void nvo::avobserve::HealthEvent(void* receiver,void* params) noexcept {
    const ErrorGuard error;
    if(GetCurrentThreadId()!=gMainThread)return;
    const Lock lock;if(!gActive || !gEpochValid)return;
    if(!gDepth || gFrames[gDepth-1].session!=gSession || gFrames[gDepth-1].generation!=gGeneration) {++gUnscopedHealth;return;}
    auto& f=gFrames[gDepth-1];
    // Only three immutable argument slots. The fourth is a mutable multiplier.
    void* args[3]{};float delta{};
    const bool read=nvo::hit::ReadBytes(params,args,sizeof(args));
    const auto bits=reinterpret_cast<std::uintptr_t>(args[2]);
    static_assert(sizeof(bits)==sizeof(delta));std::memcpy(&delta,&bits,sizeof(delta));
    const bool matched=read && !f.tainted && f.av==16 && receiver==f.receiver && args[0]==receiver
        && args[1]==f.source && std::isfinite(delta) && delta<0 && delta==f.requested;
    if(matched) {++f.healthEvents;++gHealthEvents;}
    else {++f.healthMismatches;++gHealthMismatches;}
}

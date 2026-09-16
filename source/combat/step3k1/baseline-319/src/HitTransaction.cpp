#include "HitTransaction.hpp"
#include "NativeObserver.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <cmath>
#include <cstring>

namespace {
using U32 = std::uint32_t;
using U64 = unsigned long long;
#include "HitTransactionGuards.inl"
constexpr unsigned kDepth = 16, kDetailCalls = 64, kStageRows = 8;
constexpr U32 kEngineHitMe = 0x89A760;
SRWLOCK gLock = SRWLOCK_INIT;
struct Lock {
    Lock() noexcept { AcquireSRWLockExclusive(&gLock); }
    ~Lock() { ReleaseSRWLockExclusive(&gLock); }
};
struct ErrorGuard {
    DWORD previous = GetLastError();
    ~ErrorGuard() { SetLastError(previous); }
};
struct Snapshot {
    nvo::hit::Data data{};
    nvo::hit::Form source{}, target{}, carrier{}, weapon{};
    U32 ammo{};
    unsigned reads{};
    bool valid{}, processPresent{};
};
struct Frame {
    std::uintptr_t caller{}, input{};
    void* receiver{}; // Identity only after entry; never dereferenced on return.
    U64 id{}, parent{}, lifetime{};
    unsigned session{}, site{}, stages{}, hitEvents{}, copies{}, healthEvents{};
    DWORD thread{};
    Snapshot before{};
    bool detail{}, tainted{};
};
// Do not reset TLS on a save load. Installed continuations must always pop
// their own frames, including returns after suspend/session changes.
__declspec(thread) Frame gFrames[kDepth];
__declspec(thread) unsigned gDepth;
void* gOriginal[6]{};
bool gAttempted{}, gInstalled{}, gActive{}, gPending{};
unsigned gSession{}, gRequestedSession{};
DWORD gMainThread{};
U64 gNextId{}, gEntries{}, gReturns{}, gOpen{}, gInvalid{}, gOverflow{}, gUnscoped{};
U64 gHitStages{}, gCopyStages{}, gHealthStages{}, gOmittedStages{}, gLogFailures{}, gDetailed{};

bool Actor(const nvo::hit::Form& f) noexcept
{ return f.id && (f.type == 0x3B || f.type == 0x3C); }

Snapshot ReadSnapshot(void* receiver, const nvo::hit::Data* input) noexcept
{
    Snapshot s{};
    s.valid = nvo::hit::ReadBytes(input, &s.data, sizeof(s.data))
        && s.data.target == receiver
        && nvo::hit::ReadForm(s.data.target, s.target) && Actor(s.target)
        && nvo::hit::ReadForm(s.data.source, s.source)
        && nvo::hit::ReadForm(s.data.carrier, s.carrier)
        && nvo::hit::ReadForm(s.data.weapon, s.weapon)
        && (!s.data.weapon || s.weapon.type == 0x28);
    if (!s.valid) return s;
    const float values[] = {s.data.health,s.data.base,s.data.limb,s.data.fatigue,
        s.data.armor,s.data.weaponDamage,s.data.blockDT,s.data.condition,s.data.multiplier};
    for (float f : values) if (!std::isfinite(f)) s.valid = false;
    void* process{};
    if (!nvo::hit::ReadBytes(static_cast<const char*>(receiver)+0x68,&process,sizeof(process)))
        s.valid = false;
    s.processPresent = process != nullptr;
    if (nvo::hit::IsProjectile(s.carrier.type))
        s.ammo = nvo::hit::ProjectileAmmo(s.data.carrier,s.reads);
    return s;
}
void Summary(const char* reason) noexcept
{
    nvo::log::Write("HIT_TX_SUMMARY session=%u reason=%s entries=%llu returns=%llu open=%llu invalid=%llu depth_overflow=%llu unscoped_stages=%llu pre_hit=%llu copy=%llu pre_health=%llu detailed_calls=%llu omitted_stage_rows=%llu log_failures=%llu max_detail_calls=64 max_stage_rows_per_call=8 damage_replacement=0 committed_loss=unverified",
        gSession,reason,gEntries,gReturns,gOpen,gInvalid,gOverflow,gUnscoped,
        gHitStages,gCopyStages,gHealthStages,gDetailed,gOmittedStages,gLogFailures);
}
// Called under gLock. Call identity and stage counts continue after log limits.
bool StageRow(Frame& f) noexcept
{
    if (!f.detail || f.stages >= kStageRows) { ++gOmittedStages; return false; }
    ++f.stages; return true;
}
Frame* Current() noexcept
{
    if (!gActive || !gDepth || gFrames[gDepth-1].session != gSession) {
        if (gActive) ++gUnscoped;
        return nullptr;
    }
    return &gFrames[gDepth-1];
}

bool __cdecl Before(void* receiver,const nvo::hit::Data* input,U32 attackClass,
    std::uintptr_t caller,unsigned site) noexcept
{
    const ErrorGuard error;
    unsigned session{};
    {
        const Lock lock;
        if (!gActive) return false;
        session=gSession;
        if (gDepth>=kDepth) {
            ++gOverflow;
            // This call gets no replacement return. Suppress attribution to
            // the enclosing frame until it unwinds; never reuse its identity.
            gFrames[gDepth-1].tainted=true;
            return false;
        }
    }
    Snapshot s=ReadSnapshot(receiver,input);
    // No transaction lock while taking the observer lock. Other routes can
    // enter transaction observation while holding observer/damage locks.
    nvo::observer::LifetimeIdentity life{};
    if (s.valid && nvo::hit::IsProjectile(s.carrier.type))
        life=nvo::observer::LookupLifetime(s.data.carrier,s.carrier.id,s.source.id,s.weapon.id);
    const Lock lock;
    if (!gActive || session!=gSession) return false;
    auto& f=gFrames[gDepth]; f={};
    f.parent=gDepth && gFrames[gDepth-1].session==session ? gFrames[gDepth-1].id : 0;
    f.tainted=gDepth && gFrames[gDepth-1].tainted;
    f.caller=caller; f.receiver=receiver; f.input=reinterpret_cast<std::uintptr_t>(input);
    f.session=session; f.site=site; f.id=++gNextId; f.thread=GetCurrentThreadId();
    f.before=s;
    const bool linked=life.session==session && life.lifetime && life.ammo==s.ammo && s.ammo;
    f.lifetime=linked ? life.lifetime : 0;
    f.detail=gDetailed<kDetailCalls;
    if (f.detail) ++gDetailed;
    ++gDepth; ++gEntries; ++gOpen;
    if (!s.valid || s.reads) ++gInvalid;
    if (f.detail) {
        if (!nvo::log::Write("HIT_TX_BEGIN session=%u tx=%llu parent=%llu depth=%u site=%08X phase=before_itr receiver=%08X source=%08X weapon=%08X carrier=%08X carrier_type=%02X ammo=%08X lifetime=%llu linked=%u valid=%u process_present=%u thread=%lu main_thread=%u attack_class=%u return_site_match=%u tainted=%u damage_replacement=0",
            session,f.id,f.parent,gDepth,kSpecs[site].site,s.target.id,s.source.id,s.weapon.id,
            s.carrier.id,static_cast<unsigned>(s.carrier.type),s.ammo,f.lifetime,linked?1u:0u,s.valid?1u:0u,
            s.processPresent?1u:0u,f.thread,f.thread==gMainThread?1u:0u,attackClass&0xffu,
            caller==kSpecs[site].site+5u?1u:0u,f.tainted?1u:0u)) ++gLogFailures;
        if (s.valid && !nvo::log::Write("HIT_TX_DATA session=%u tx=%llu phase=before_itr region=%d health=%.9g base=%.9g limb=%.9g fatigue=%.9g armor=%.9g weapon_damage=%.9g block_dt=%.9g condition=%.9g multiplier=%.9g flags=%08X weapon_av=%u health_applied=unverified observer_writes=0",
            session,f.id,s.data.region,static_cast<double>(s.data.health),static_cast<double>(s.data.base),
            static_cast<double>(s.data.limb),static_cast<double>(s.data.fatigue),static_cast<double>(s.data.armor),
            static_cast<double>(s.data.weaponDamage),static_cast<double>(s.data.blockDT),
            static_cast<double>(s.data.condition),static_cast<double>(s.data.multiplier),s.data.flags,s.data.weaponAV)) ++gLogFailures;
    }
    return true;
}
std::uintptr_t __cdecl After() noexcept
{
    const ErrorGuard error;
    const Frame f=gFrames[--gDepth];
    const Lock lock;
    if (gActive && f.session==gSession) {
        ++gReturns; --gOpen;
        if (f.detail && !nvo::log::Write("HIT_TX_RETURN session=%u tx=%llu parent=%llu depth=%u pre_hit=%u copies=%u pre_health=%u tainted=%u acknowledgement=provider_return committed_loss=unverified post_pointer_reads=0 damage_replacement=0",
            f.session,f.id,f.parent,gDepth+1,f.hitEvents,f.copies,f.healthEvents,f.tainted?1u:0u)) ++gLogFailures;
    }
    return f.caller;
}

__declspec(naked) void ReturnBridge()
{
    __asm {
        push 0
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
// Six entry stubs push only their immutable route index. This common wrapper
// replaces that slot with the original ITR target, then RET tail-dispatches.
// The original arguments/ECX/EDX/flags/FPU state reach ITR unchanged.
__declspec(naked) void EntryBridge()
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
        push dword ptr [ebx+36]
        push dword ptr [ebx+40]
        push dword ptr [ebx+48]
        push dword ptr [ebx+44]
        push dword ptr [ebx+24]
        call Before
        add esp, 20
        test al, al
        jz no_continuation
        mov dword ptr [ebx+40], offset ReturnBridge
    no_continuation:
        mov eax, [ebx+36]
        mov eax, dword ptr gOriginal[eax*4]
        mov [ebx+36], eax
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        ret
    }
}
#define NVO_HIT_ENTRY(N) __declspec(naked) void Entry##N() { __asm push N __asm jmp EntryBridge }
NVO_HIT_ENTRY(0) NVO_HIT_ENTRY(1) NVO_HIT_ENTRY(2)
NVO_HIT_ENTRY(3) NVO_HIT_ENTRY(4) NVO_HIT_ENTRY(5)
#undef NVO_HIT_ENTRY
void* const kEntries[]={reinterpret_cast<void*>(Entry0),reinterpret_cast<void*>(Entry1),
    reinterpret_cast<void*>(Entry2),reinterpret_cast<void*>(Entry3),reinterpret_cast<void*>(Entry4),reinterpret_cast<void*>(Entry5)};

bool Image(HMODULE module,U32 timestamp,U32 size) noexcept
{
    IMAGE_DOS_HEADER dos{}; IMAGE_NT_HEADERS32 nt{};
    return module && nvo::hit::ReadBytes(module,&dos,sizeof(dos)) && dos.e_magic==IMAGE_DOS_SIGNATURE
        && dos.e_lfanew>=0x40 && dos.e_lfanew<=0x1000
        && nvo::hit::ReadBytes(reinterpret_cast<char*>(module)+dos.e_lfanew,&nt,sizeof(nt))
        && nt.Signature==IMAGE_NT_SIGNATURE && nt.FileHeader.Machine==IMAGE_FILE_MACHINE_I386
        && nt.OptionalHeader.Magic==IMAGE_NT_OPTIONAL_HDR32_MAGIC
        && nt.FileHeader.TimeDateStamp==timestamp && nt.OptionalHeader.SizeOfImage==size;
}
bool Executable(const void* address,HMODULE module) noexcept
{
    MEMORY_BASIC_INFORMATION info{};
    return VirtualQuery(address,&info,sizeof(info)) && info.State==MEM_COMMIT && info.Type==MEM_IMAGE
        && info.AllocationBase==module && !(info.Protect&(PAGE_GUARD|PAGE_NOACCESS))
        && (info.Protect&(PAGE_EXECUTE|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY));
}
U32 CallTarget(U32 site) noexcept
{
    unsigned char bytes[5]{}; U32 delta{};
    if (!nvo::hit::ReadBytes(reinterpret_cast<void*>(site),bytes,5) || bytes[0]!=0xE8) return 0;
    std::memcpy(&delta,bytes+1,4);return site+5+delta;
}
bool Provider(HMODULE itr) noexcept
{
    if (!Image(itr,0x6A948FDD,0xB3000)) return false;
    const U32 base=static_cast<U32>(reinterpret_cast<std::uintptr_t>(itr));
    for (const auto& spec:kSpecs) {
        unsigned char body[127]{}; U32 original{},site{};
        const auto* address=reinterpret_cast<char*>(itr)+spec.rva;
        if (!Executable(address,itr) || !Executable(address+126,itr)
            || !nvo::hit::ReadBytes(address,body,sizeof(body))) return false;
        for (auto offset:kRelocations) {
            U32 value{}; std::memcpy(&value,body+offset,4); value-=base-0x10000000;
            std::memcpy(body+offset,&value,4);
        }
        U64 hash=14695981039346656037ull;
        for (auto b:body) hash=(hash^b)*1099511628211ull;
        if (hash!=spec.hash
            || !nvo::hit::ReadBytes(reinterpret_cast<char*>(itr)+spec.originalRva,&original,4)
            || !nvo::hit::ReadBytes(reinterpret_cast<char*>(itr)+spec.originalRva+4,&site,4)
            || original!=kEngineHitMe || site!=spec.site) return false;
    }
    return true;
}
bool OwnsCalls() noexcept
{
    for (unsigned i=0;i<6;++i)
        if (CallTarget(kSpecs[i].site)!=reinterpret_cast<U32>(kEntries[i])) return false;
    return true;
}
bool Disabled(const char* reason) noexcept
{
    nvo::log::Write("HIT_TX_DISABLED reason=%s damage_replacement=0",reason);return false;
}
bool Install() noexcept
{
    if (gAttempted) return gInstalled && OwnsCalls() && Provider(GetModuleHandleW(L"itr-nvse.dll"));
    gAttempted=true;
    auto game=GetModuleHandleW(nullptr),itr=GetModuleHandleW(L"itr-nvse.dll");
    if (reinterpret_cast<U32>(game)!=0x400000 || !Image(game,0x4E0D50ED,0x107B000))
        return Disabled("unsupported_game_image");
    if (!Provider(itr)) return Disabled("unsupported_itr_thunk_or_recorded_original");
    const U32 base=reinterpret_cast<U32>(itr);
    for (unsigned i=0;i<6;++i) {
        if (!Executable(reinterpret_cast<void*>(kSpecs[i].site),game)
            || !Executable(reinterpret_cast<void*>(kSpecs[i].site+4),game)
            || CallTarget(kSpecs[i].site)!=base+kSpecs[i].rva)
            return Disabled("hit_call_owned_by_other_implementation");
        gOriginal[i]=reinterpret_cast<void*>(base+kSpecs[i].rva);
    }
    MemoryBarrier(); // Publish every original target before any branch can enter.
    // Deferred initialization only, before gameplay. Acquire all page
    // protections first, recheck every call, then install or restore as a set.
    DWORD protection[6]{}; unsigned protectedCount{};
    for (;protectedCount<6;++protectedCount)
        if (!VirtualProtect(reinterpret_cast<void*>(kSpecs[protectedCount].site),5,PAGE_EXECUTE_READWRITE,&protection[protectedCount])) break;
    bool ok=protectedCount==6;
    if (ok) for (unsigned i=0;i<6;++i)
        if (CallTarget(kSpecs[i].site)!=reinterpret_cast<U32>(gOriginal[i])) ok=false;
    unsigned changed{};
    if (ok) for (;changed<6;++changed) {
        const U32 rel=reinterpret_cast<U32>(kEntries[changed])-kSpecs[changed].site-5;
        std::memcpy(reinterpret_cast<void*>(kSpecs[changed].site+1),&rel,4);
        if (!FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(kSpecs[changed].site),5)) { ++changed; ok=false;break; }
    }
    if (!ok) for (unsigned i=0;i<changed;++i) {
        if (CallTarget(kSpecs[i].site)==reinterpret_cast<U32>(kEntries[i])) {
            const U32 rel=reinterpret_cast<U32>(gOriginal[i])-kSpecs[i].site-5;
            std::memcpy(reinterpret_cast<void*>(kSpecs[i].site+1),&rel,4);
            FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(kSpecs[i].site),5);
        }
    }
    // Reverse order also restores correctly if two sites share a page.
    while (protectedCount) {
        const unsigned i=--protectedCount;DWORD ignored{};
        if (!VirtualProtect(reinterpret_cast<void*>(kSpecs[i].site),5,protection[i],&ignored))
            nvo::log::Write("HIT_TX_PROTECTION_RESTORE_FAILED site=%08X",kSpecs[i].site);
    }
    gInstalled=ok && OwnsCalls();
    if (!gInstalled) return Disabled("transaction_install_failed");
    nvo::log::Write("HIT_TX_HOOK_READY provider=ITR20202 sites=6 installed_at=deferred_init original_chain_calls=1 entry=before_itr return=provider_return gameplay_writes=0 damage_replacement=0");
    return true;
}
float FloatSlot(void* packed) noexcept
{
    U32 bits=reinterpret_cast<U32>(packed);float value{};
    std::memcpy(&value,&bits,4);return value;
}
} // namespace

void nvo::transaction::Initialize() noexcept
{
    const ErrorGuard error;gMainThread=GetCurrentThreadId();Install();
}
void nvo::transaction::QueueCapture(unsigned session) noexcept
{
    const Lock lock;gActive=false;gPending=true;gRequestedSession=session;
}
void nvo::transaction::Suspend(const char* reason) noexcept
{
    const Lock lock;gPending=false;if(gActive)Summary(reason);gActive=false;
}
void nvo::transaction::Tick() noexcept
{
    const ErrorGuard error;
    unsigned session{};
    { const Lock lock;if(!gPending)return;gPending=false;session=gRequestedSession; }
    if (!gInstalled || !OwnsCalls() || !Provider(GetModuleHandleW(L"itr-nvse.dll"))) {
        Disabled("capture_hook_guard_failed");return;
    }
    const Lock lock;
    gSession=session;gEntries=gReturns=gOpen=gInvalid=gOverflow=gUnscoped=0;
    gHitStages=gCopyStages=gHealthStages=gOmittedStages=gLogFailures=gDetailed=0;
    gActive=true;
    nvo::log::Write("HIT_TX_READY session=%u max_depth=16 max_detail_calls=64 stages_per_call=8 ids_independent_of_logging=1 committed_loss=unverified damage_replacement=0",session);
}
void nvo::transaction::CopyInput(const nvo::hit::Data* input,void* process) noexcept
{
    const ErrorGuard error;const Lock lock;
    auto* f=Current();if(!f)return;++f->copies;++gCopyStages;
    nvo::hit::Data d{};void* ownerProcess{};
    const bool read=nvo::hit::ReadBytes(input,&d,sizeof(d));
    const bool identity=read && d.target==f->receiver && d.source==f->before.data.source
        && d.carrier==f->before.data.carrier && d.weapon==f->before.data.weapon;
    const bool processMatches=identity && process && nvo::hit::ReadBytes(
        static_cast<const char*>(d.target)+0x68,&ownerProcess,sizeof(ownerProcess)) && process==ownerProcess;
    const bool exact=identity && reinterpret_cast<std::uintptr_t>(input)==f->input;
    if (StageRow(*f) && !nvo::log::Write("HIT_TX_STAGE session=%u tx=%llu stage=copy_input ordinal=%u pointer_equal=%u identity_match=%u process_match=%u tainted=%u read=%u region=%d health=%.9g limb=%.9g flags=%08X association=%s committed_loss=unverified observer_writes=0",
        f->session,f->id,f->stages,exact?1u:0u,identity?1u:0u,processMatches?1u:0u,f->tainted?1u:0u,read?1u:0u,
        read?d.region:-1,read&&std::isfinite(d.health)?static_cast<double>(d.health):0,
        read&&std::isfinite(d.limb)?static_cast<double>(d.limb):0,read?d.flags:0,
        !f->tainted && f->before.valid && exact && processMatches ? "exact_input_pointer" : "scope_only")) ++gLogFailures;
}
void nvo::transaction::HitEvent(void* thisObj,void* params) noexcept
{
    const ErrorGuard error;const Lock lock;
    auto* f=Current();if(!f)return;++f->hitEvents;++gHitStages;
    // Do not read the provider's mutable multiplier slot.
    void* a[5]{};const bool read=nvo::hit::ReadBytes(params,a,sizeof(a));
    const float value=FloatSlot(a[3]);
    const bool match=read && thisObj==f->receiver && a[0]==thisObj
        && a[1]==f->before.data.source && a[2]==f->before.data.weapon;
    if (StageRow(*f) && !nvo::log::Write("HIT_TX_STAGE session=%u tx=%llu stage=itr_pre_hit ordinal=%u identity_match=%u tainted=%u read=%u region=%d value_valid=%u input_damage=%.9g association=scope_only observer_writes=0",
        f->session,f->id,f->stages,match?1u:0u,f->tainted?1u:0u,read?1u:0u,
        read?static_cast<int>(reinterpret_cast<std::intptr_t>(a[4])):-1,
        read&&std::isfinite(value)?1u:0u,std::isfinite(value)?static_cast<double>(value):0)) ++gLogFailures;
}
void nvo::transaction::HealthEvent(void* thisObj,void* params) noexcept
{
    const ErrorGuard error;const Lock lock;
    auto* f=Current();if(!f)return;++f->healthEvents;++gHealthStages;
    void* a[3]{};const bool read=nvo::hit::ReadBytes(params,a,sizeof(a));
    const float value=FloatSlot(a[2]);
    const bool match=read && thisObj==f->receiver && a[0]==thisObj && a[1]==f->before.data.source;
    if (StageRow(*f) && !nvo::log::Write("HIT_TX_STAGE session=%u tx=%llu stage=itr_pre_health ordinal=%u identity_match=%u tainted=%u read=%u value_valid=%u delta=%.9g association=scope_only cause=unclassified committed_loss=unverified observer_writes=0",
        f->session,f->id,f->stages,match?1u:0u,f->tainted?1u:0u,read?1u:0u,
        read&&std::isfinite(value)?1u:0u,std::isfinite(value)?static_cast<double>(value):0)) ++gLogFailures;
}

nvo::transaction::Scope nvo::transaction::MatchScope(void* receiver,void* source) noexcept
{
    const ErrorGuard error;const Lock lock;
    if (!gActive || !gDepth) return {};
    const auto& f=gFrames[gDepth-1];
    if (f.session!=gSession || f.tainted || !f.before.valid
        || f.receiver!=receiver || f.before.data.source!=source) return {};
    return {f.id,f.session,true};
}

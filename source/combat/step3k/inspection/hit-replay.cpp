// Offline x86 call-contract probe. Includes the actual observer and bridges,
// with mock forms/provider/logging. Never loads the plugin DLL or game.
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <vector>
#include <string>
#include <thread>
#include <atomic>
#include "../../../../native/NVOCombatCore/src/HitTransaction.cpp"

alignas(16) unsigned char targetForm[128]{},sourceForm[128]{},carrierForm[128]{},weaponForm[128]{};
nvo::hit::Data testHit{};
std::vector<std::string> rows;
std::atomic<unsigned> providerCalls{};
bool failLog{},suspendInside{};
unsigned nestingGoal{};
__declspec(thread) unsigned mockDepth;

bool nvo::log::Write(const char* format,...) noexcept {
    if(failLog)return false;
    char b[1024];va_list a;va_start(a,format);vsnprintf(b,sizeof(b),format,a);va_end(a);
    rows.emplace_back(b);return true;
}
bool nvo::hit::ReadBytes(const void* p,void* d,std::size_t n) noexcept {
    if(!p)return false;std::memcpy(d,p,n);return true;
}
bool nvo::hit::ReadForm(void* p,nvo::hit::Form& f) noexcept {
    f={};if(!p)return true;f.type=static_cast<unsigned char*>(p)[4];std::memcpy(&f.id,static_cast<char*>(p)+12,4);return true;
}
bool nvo::hit::IsProjectile(unsigned char type) noexcept {return type==0x3D;}
U32 nvo::hit::ProjectileAmmo(void*,unsigned&) noexcept {return 0x6B53C;}
nvo::observer::LifetimeIdentity nvo::observer::LookupLifetime(void*,U32,U32,U32) noexcept {
    return {gSession,99,0x6B53C};
}
using Route=U32(__thiscall*)(void*,nvo::hit::Data*,U32);
void* FloatValue(float f) {U32 b{};std::memcpy(&b,&f,4);return reinterpret_cast<void*>(b);}
U32 __fastcall MockProvider(void* receiver,void*,nvo::hit::Data* hit,U32 attack) {
    ++providerCalls;++mockDepth;
    assert(receiver==targetForm && hit==&testHit && attack==0x7F1234A5);
    const auto scope=nvo::transaction::MatchScope(receiver,hit->source);
    if(mockDepth<16 && gActive)assert(scope.matched);
    assert(!nvo::transaction::MatchScope(sourceForm,receiver).matched);
    if(mockDepth<nestingGoal) {
        const auto result=reinterpret_cast<Route>(kEntries[mockDepth%6])(receiver,hit,attack);
        assert(result==0xD00DFEED);
    }
    void* hitArgs[]={receiver,hit->source,hit->weapon,FloatValue(hit->health),reinterpret_cast<void*>(hit->region)};
    void* healthArgs[]={receiver,hit->source,FloatValue(-2*hit->health)};
    nvo::transaction::HitEvent(receiver,hitArgs);
    nvo::transaction::CopyInput(hit,reinterpret_cast<void*>(0x1234));
    nvo::transaction::HealthEvent(receiver,healthArgs);
    if(suspendInside)nvo::transaction::Suspend("mock_load_boundary");
    --mockDepth;return 0xD00DFEED;
}
void Reset() {
    assert(!gDepth && !mockDepth);rows.clear();gActive=true;gSession++;
    gEntries=gReturns=gOpen=gInvalid=gOverflow=gUnscoped=0;
    gHitStages=gCopyStages=gHealthStages=gOmittedStages=gLogFailures=gDetailed=0;
    failLog=suspendInside=false;nestingGoal=0;providerCalls=0;
    for(auto& p:gOriginal)p=reinterpret_cast<void*>(MockProvider);
}

// A second naked provider/probe checks the actual bridge's machine-state
// preservation in both directions, including DF, x87, SSE/MXCSR and RET 8.
alignas(16) unsigned char expectedEntryFx[512]{},actualEntryFx[512]{},expectedExitFx[512]{},actualExitFx[512]{};
U32 entryFlags{},exitFlags{},entryEax{},entryEcx{},entryEdx{},entryArg{},entryInput{},entryEsp{};
U32 exitEax{},exitEcx{},exitEdx{},beforeEsp{},afterEsp{};
U32 savedRootSp{},savedRootFx{};
__declspec(naked) void AbiProvider() {
    __asm {
        fxsave actualEntryFx
        pushfd
        pop entryFlags
        mov entryEax,eax
        mov entryEcx,ecx
        mov entryEdx,edx
        mov entryEsp,esp
        mov eax,[esp+4]
        mov entryInput,eax
        mov eax,[esp+8]
        mov entryArg,eax
        cld
        fninit
        fldpi
        pxor xmm0,xmm0
        mov eax,0DEADBEEFh
        mov ecx,012345678h
        mov edx,087654321h
        fxsave expectedExitFx
        push 0247h
        popfd
        ret 8
    }
}
__declspec(naked) void AbiProbe() {
    __asm {
        pushfd
        pushad
        mov savedRootSp,esp
        sub esp,528
        and esp,-16
        mov savedRootFx,esp
        fxsave [esp]
        fninit
        fld1
        pcmpeqd xmm0,xmm0
        push 03F80h
        ldmxcsr [esp]
        add esp,4
        fxsave expectedEntryFx
        mov beforeEsp,esp
        push 07F1234A5h
        push offset testHit
        mov eax,013579BDFh
        mov ecx,offset targetForm
        mov edx,02468ACE0h
        push 0646h // DF=1, ZF=1, CF=0. Both must reach the provider.
        popfd
        call Entry0
        fxsave actualExitFx
        pushfd
        pop exitFlags
        mov exitEax,eax
        mov exitEcx,ecx
        mov exitEdx,edx
        mov afterEsp,esp
        cld
        mov eax,savedRootFx
        fxrstor [eax]
        mov esp,savedRootSp
        popad
        popfd
        ret
    }
}

int main() {
    auto form=[](unsigned char* p,U32 id,unsigned char type){p[4]=type;std::memcpy(p+12,&id,4);};
    form(targetForm,0xFF001978,0x3B);form(sourceForm,0x14,0x3B);
    form(carrierForm,0xFF001994,0x3D);form(weaponForm,0x4333,0x28);
    void* process=reinterpret_cast<void*>(0x1234);std::memcpy(targetForm+0x68,&process,4);
    testHit.target=targetForm;testHit.source=sourceForm;testHit.carrier=carrierForm;testHit.weapon=weaponForm;
    testHit.health=208;testHit.base=208;testHit.limb=29.3785f;testHit.region=0;testHit.multiplier=1;
    const auto initial=testHit;gMainThread=GetCurrentThreadId();
    Reset();
    for(auto p:kEntries)assert(reinterpret_cast<Route>(p)(targetForm,&testHit,0x7F1234A5)==0xD00DFEED);
    assert(gEntries==6 && gReturns==6 && !gOpen && !gDepth && providerCalls==6);
    assert(gHitStages==6 && gCopyStages==6 && gHealthStages==6);
    assert(std::memcmp(&testHit,&initial,sizeof(initial))==0);
    unsigned exact{};for(const auto& s:rows)if(s.find("association=exact_input_pointer")!=std::string::npos)++exact;
    assert(exact==6);puts("six_route_chain_identity_and_input_unchanged=pass");

    Reset();for(auto& p:gOriginal)p=reinterpret_cast<void*>(AbiProvider);AbiProbe();
    assert(entryEax==0x13579BDF && entryEcx==reinterpret_cast<U32>(targetForm) && entryEdx==0x2468ACE0);
    assert(entryInput==reinterpret_cast<U32>(&testHit) && entryArg==0x7F1234A5);
    assert(entryEsp==beforeEsp-12 && beforeEsp==afterEsp);
    assert((entryFlags&0xCD5)==(0x646&0xCD5));
    assert(exitEax==0xDEADBEEF && exitEcx==0x12345678 && exitEdx==0x87654321 && (exitFlags&0xCD5)==(0x247&0xCD5));
    assert(std::memcmp(expectedEntryFx,actualEntryFx,416)==0);
    assert(std::memcmp(expectedExitFx,actualExitFx,416)==0);
    assert(gEntries==1 && gReturns==1 && !gDepth && !gOpen);
    puts("actual_x86_bridge_stack_gpr_flags_df_x87_sse_mxcsr=pass");

    Reset();nestingGoal=20;reinterpret_cast<Route>(Entry0)(targetForm,&testHit,0x7F1234A5);
    assert(providerCalls==20 && gEntries==16 && gReturns==16 && gOverflow==4 && !gOpen && !gDepth);
    unsigned tainted{};for(const auto& s:rows)if(s.find("tainted=1")!=std::string::npos)++tainted;
    assert(tainted);puts("nested_depth_overflow_no_parent_attribution_or_bad_return=pass");

    Reset();failLog=true;
    for(unsigned i=0;i<300;++i)reinterpret_cast<Route>(Entry0)(targetForm,&testHit,0x7F1234A5);
    assert(providerCalls==300 && gEntries==300 && gReturns==300 && !gOpen && !gDepth);
    assert(gDetailed==64 && gHitStages==300 && gCopyStages==300 && gHealthStages==300 && gLogFailures>0);
    puts("call_identity_and_returns_survive_log_budget_and_sink_failure=pass");

    Reset();suspendInside=true;reinterpret_cast<Route>(Entry0)(targetForm,&testHit,0x7F1234A5);
    assert(!gActive && !gDepth && providerCalls==1);
    Reset();gActive=false;reinterpret_cast<Route>(Entry0)(targetForm,&testHit,0x7F1234A5);
    assert(!gEntries && !gDepth && providerCalls==1);puts("suspend_continuation_and_inactive_passthrough=pass");

    Reset();
    std::thread a([]{for(int i=0;i<40;++i)reinterpret_cast<Route>(Entry0)(targetForm,&testHit,0x7F1234A5);});
    std::thread b([]{for(int i=0;i<40;++i)reinterpret_cast<Route>(Entry1)(targetForm,&testHit,0x7F1234A5);});
    a.join();b.join();assert(gEntries==80 && gReturns==80 && providerCalls==80 && !gOpen);
    assert(std::memcmp(&testHit,&initial,sizeof(initial))==0);puts("two_thread_independent_scopes=pass");
    puts("game_or_plugin_dll_loaded=false");
}

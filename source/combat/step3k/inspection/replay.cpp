// Offline x86 probe of the actual source/bridges with mocked engine reads.
// Actual game getter semantics remain a separate runtime checkpoint.
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <vector>
#include <string>
#include <thread>
#include <limits>
#define NVO_AV_OFFLINE_PROBE
#include "../../../../native/NVOCombatCore/src/ActorValueObserver.cpp"

alignas(16) unsigned char targetForm[256]{},sourceForm[256]{};
float currentValues[64]{},damageValues[64]{};
std::vector<std::string> rows;
std::atomic<unsigned> providerCalls{},getterCalls{};
bool failLog{},suspendInside{},switchSession{},changeIdentity{},noChange{},readFailure{},nestedGetter{};
unsigned nestingGoal{},mockDepth{};
bool scopeMatch=true;
using Route=U32(__thiscall*)(void*,U32,float,void*);

bool nvo::log::Write(const char* format,...) noexcept {
    if(failLog)return false;
    char buffer[1024];va_list a;va_start(a,format);vsnprintf(buffer,sizeof(buffer),format,a);va_end(a);
    assert(std::strlen(buffer)<766);rows.emplace_back(buffer);return true;
}
bool nvo::hit::ReadBytes(const void* p,void* d,std::size_t n) noexcept {
    if(!p)return false;
    __try { std::memcpy(d,p,n);return true; }
    __except(EXCEPTION_EXECUTE_HANDLER) {return false;}
}
bool nvo::hit::ReadForm(void* p,nvo::hit::Form& f) noexcept {
    f={};if(!p)return true;
    unsigned char data[16];if(!ReadBytes(p,data,sizeof(data)))return false;
    f.type=data[4];std::memcpy(&f.id,data+12,4);return true;
}
nvo::transaction::Scope nvo::transaction::MatchScope(void*,void*) noexcept {
    return scopeMatch ? Scope{88,gSession,true} : Scope{};
}
namespace {
bool ProbeReadValues(void* actor,U32 av,Values& v) noexcept {
    getterCalls+=2;assert(actor==targetForm && av<64);
    if(readFailure)return false;
    if(nestedGetter) {nestedGetter=false;reinterpret_cast<Route>(EntryBridge)(targetForm,17,-1,sourceForm);}
    std::memcpy(&v.table,targetForm,4);std::memcpy(&v.owner,targetForm+0xA4,4);
    std::memcpy(&v.id,targetForm+12,4);std::memcpy(&v.process,targetForm+0x68,4);
    v.effective=v.table==kClasses[1].table && av==25 ? 45 : av;
    v.current=currentValues[v.effective];v.damage=damageValues[v.effective];return true;
}
}
U32 __fastcall MockProvider(void* actor,void*,U32 av,float delta,void* source) {
    ++providerCalls;++mockDepth;assert(actor==targetForm && source==sourceForm && av<64);
    if(mockDepth<nestingGoal) {
        assert(reinterpret_cast<Route>(EntryBridge)(actor,av,delta,source)==0xD00DFEED);
    }
    U32 table{};std::memcpy(&table,targetForm,4);
    const U32 effective=table==kClasses[1].table && av==25 ? 45 : av;
    if(!noChange && std::isfinite(delta)) {currentValues[effective]+=delta;damageValues[effective]+=delta;}
    if(changeIdentity){U32 changed=0xFFAB1234;std::memcpy(targetForm+12,&changed,4);}
    if(suspendInside)nvo::avobserve::Suspend("mock_reload");
    if(switchSession){++gSession;gEntries=gReturns=gOpen=0;}
    --mockDepth;return 0xD00DFEED;
}
void Reset(unsigned kind=0) {
    assert(!gDepth && !mockDepth);rows.clear();gActive=true;++gSession;scopeMatch=true;
    gEntries=gReturns=gOpen=gInvalid=gOverflow=gNested=gDetailed=gLogFailures=0;gOtherThread=0;
    providerCalls=getterCalls=0;nestingGoal=0;
    failLog=suspendInside=switchSession=changeIdentity=noChange=readFailure=nestedGetter=false;
    gOriginal=reinterpret_cast<void*>(MockProvider);
    for(unsigned i=0;i<64;++i){currentValues[i]=10000;damageValues[i]=0;}
    std::memcpy(targetForm,&kClasses[kind].table,4);std::memcpy(targetForm+0xA4,&kClasses[kind].owner,4);
    U32 id=0xFF001978;std::memcpy(targetForm+12,&id,4);targetForm[4]=kind==1?0x3C:0x3B;
    id=0x14;std::memcpy(sourceForm+12,&id,4);sourceForm[4]=0x3B;
    void* process=reinterpret_cast<void*>(0x1234);std::memcpy(targetForm+0x68,&process,4);
}
bool Has(const char* text) {for(const auto& row:rows)if(row.find(text)!=std::string::npos)return true;return false;}

alignas(16) unsigned char expectedEntryFx[512]{},actualEntryFx[512]{},expectedExitFx[512]{},actualExitFx[512]{};
U32 entrySource{};
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
        mov eax,[esp+12]
        mov entrySource,eax
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
        ret 12
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
        push offset sourceForm
        push 0C1480000h
        push 16
        mov eax,013579BDFh
        mov ecx,offset targetForm
        mov edx,02468ACE0h
        push 0646h // DF=1, ZF=1, CF=0. Both must reach the provider.
        popfd
        call EntryBridge
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
    gMainThread=GetCurrentThreadId();
    for(unsigned kind=0;kind<3;++kind) {
        Reset(kind);
        for(U32 av:{16u,25u,26u,27u,28u,29u,30u,31u}) {
            assert(reinterpret_cast<Route>(EntryBridge)(targetForm,av,-12.5f,sourceForm)==0xD00DFEED);
        }
        assert(gEntries==8 && gReturns==8 && !gDepth && !gOpen && !gInvalid && providerCalls==8);
        assert(Has("net_current=-12.5 net_damage=-12.5 valid=1") && Has("tx=88 scope_match=1"));
        if(kind==1)assert(Has("av=25 effective_av=45"));
    }
    puts("three_classes_health_conditions_creature_remap_and_exact_once=pass");
    Reset();noChange=true;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-12.5f,sourceForm);
    assert(Has("net_current=0 net_damage=0 valid=1"));
    Reset();scopeMatch=false;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-12.5f,sourceForm);
    assert(Has("tx=0 scope_match=0"));puts("zero_applied_change_and_unscoped_calls_not_invented=pass");
    Reset();nestingGoal=20;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);
    assert(providerCalls==20 && gEntries==16 && gReturns==16 && gOverflow==4 && !gDepth && !gOpen);
    assert(gInvalid==16 && Has("tainted=1"));
    Reset();nestingGoal=2;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);
    assert(Has("net_current=-2 net_damage=-2 valid=1 nested=1"));
    puts("nested_net_intervals_and_overflow_return_integrity=pass");
    Reset();failLog=true;for(unsigned i=0;i<300;++i)reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);
    assert(gEntries==300 && gReturns==300 && providerCalls==300 && gDetailed==96 && gLogFailures==192 && !gOpen && !gDepth);
    puts("ids_and_original_calls_survive_log_limits_and_sink_failure=pass");
    Reset();suspendInside=true;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);assert(!gActive && !gDepth && providerCalls==1);
    Reset();switchSession=true;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);assert(!gDepth && !gOpen && !gReturns);
    Reset();gActive=false;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);assert(!gDepth && !gEntries && !getterCalls);
    puts("suspend_changed_session_and_inactive_passthrough=pass");
    Reset();readFailure=true;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);assert(gInvalid==1 && providerCalls==1 && !gDepth);
    Reset();changeIdentity=true;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);assert(gInvalid==1 && getterCalls==2);
    Reset();nestedGetter=true;reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);assert(gInvalid==1 && providerCalls==2 && !gDepth);
    puts("read_failure_changed_identity_and_getter_reentrancy_rejected=pass");
    Reset();for(auto av:{17u,24u,32u})reinterpret_cast<Route>(EntryBridge)(targetForm,av,-1,sourceForm);
    reinterpret_cast<Route>(EntryBridge)(targetForm,16,0,sourceForm);
    reinterpret_cast<Route>(EntryBridge)(targetForm,16,1,sourceForm);
    reinterpret_cast<Route>(EntryBridge)(targetForm,16,std::numeric_limits<float>::quiet_NaN(),sourceForm);
    std::thread other([]{reinterpret_cast<Route>(EntryBridge)(targetForm,16,-1,sourceForm);});other.join();
    assert(providerCalls==7 && !getterCalls && !gEntries && gOtherThread==1);
    puts("unwatched_positive_nonfinite_and_other_thread_no_getters=pass");
    Reset();gOriginal=reinterpret_cast<void*>(AbiProvider);AbiProbe();
    assert(entryEax==0x13579BDF && entryEcx==reinterpret_cast<U32>(targetForm) && entryEdx==0x2468ACE0);
    assert(entryInput==16 && entryArg==0xC1480000 && entrySource==reinterpret_cast<U32>(sourceForm));
    assert(entryEsp==beforeEsp-16 && beforeEsp==afterEsp);
    assert((entryFlags&0xCD5)==(0x646&0xCD5));
    assert(exitEax==0xDEADBEEF && exitEcx==0x12345678 && exitEdx==0x87654321 && (exitFlags&0xCD5)==(0x247&0xCD5));
    assert(std::memcmp(expectedEntryFx,actualEntryFx,416)==0);
    assert(std::memcmp(expectedExitFx,actualExitFx,416)==0);
    assert(gEntries==1 && gReturns==1 && !gDepth && !gOpen);
    puts("actual_x86_bridge_stack_gpr_flags_df_x87_sse_mxcsr=pass");


    puts("game_or_plugin_dll_loaded=false");
}

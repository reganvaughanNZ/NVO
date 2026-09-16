#include "ArmourCoverage.hpp"
#include "ArmourCoverageConfig.hpp"
#include "ArmourOrigin.hpp"
#include "CurrentHit.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <cstring>
#include <cwchar>
#include <iterator>

namespace nvo::armour::coverage_log {
namespace {
origin::Table gMods;
config::Registry gRegistry;
char gFile[config::kMaxBytes+1]{};
bool gStarted{},gReady{};
DWORD gThread{};
unsigned gSession{},gSeen{},gClassified{},gHeld{},gOriginUnknown{},gLogFailures{};
const char* gReason="not_started";
struct ErrorGuard { DWORD saved=GetLastError(); ~ErrorGuard(){SetLastError(saved);} };
bool ReadMemory(void*,const void* from,void* to,std::size_t size) noexcept {return hit::ReadBytes(from,to,size);}
const char* LoadFile() noexcept {
    wchar_t path[32768]{};
    const auto len=GetModuleFileNameW(nullptr,path,static_cast<DWORD>(std::size(path)));
    if(!len || len>=std::size(path))return "game_path_unavailable";
    auto* slash=std::wcsrchr(path,L'\\');if(!slash)return "game_path_unavailable";slash[1]=0;
    if(wcscat_s(path,L"Data\\NVSE\\Plugins\\NVOArmourCoverage.tsv"))return "config_path_limit";
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)return "config_missing_or_unreadable";
    LARGE_INTEGER size{};DWORD got{};
    const bool ok=GetFileSizeEx(file,&size) && size.QuadPart>0 && size.QuadPart<=config::kMaxBytes
        && ReadFile(file,gFile,static_cast<DWORD>(size.QuadPart),&got,nullptr) && got==size.QuadPart;
    CloseHandle(file);
    if(!ok)return "config_size_or_read";
    if(!gRegistry.Load(std::string_view(gFile,got)))return gRegistry.Error();
    return nullptr;
}
const char* ExtentName(coverage::Extent value) noexcept {
    switch(value) {
    case coverage::Extent::None:return "none";
    case coverage::Extent::Partial:return "partial";
    case coverage::Extent::Full:return "full";
    case coverage::Extent::Unknown:return "unknown";
    }
    return "invalid";
}
}
void Begin(unsigned session) noexcept {
    const ErrorGuard error;
    if(gThread && GetCurrentThreadId()!=gThread)return;
    gThread=GetCurrentThreadId();
    gStarted=true;gReady=false;gSession=session;gSeen=gClassified=gHeld=gOriginUnknown=gLogFailures=0;
    gRegistry.Reset();gMods={};gReason="layout_unavailable";
    if(session && hit::ProjectileLayoutReady()) {
        const reader::Memory memory{nullptr,ReadMemory};
        if(!origin::CaptureStable(memory,0x11C3F2C,gMods))gReason="origin_table_unavailable";
        else if(const auto* reason=LoadFile())gReason=reason;
        else {gReady=true;gReason="ready";}
    }
    if(!log::Write("ARMOUR_COVERAGE_READY session=%u ready=%u reason=%s origin_mods=%u profiles=%u origin_double_read=1 config=NVOArmourCoverage.tsv max_snapshots=64 authored_classification_only=1 coverage_authority=0 material_response=0 stagger_writes=0 damage_replacement=0",
        session,gReady?1u:0u,gReason,gMods.count,static_cast<unsigned>(gRegistry.Catalog().Count())))++gLogFailures;
}
void Suspend(const char* reason) noexcept {
    const ErrorGuard error;
    if(!gStarted || GetCurrentThreadId()!=gThread)return;
    log::Write("ARMOUR_COVERAGE_SUMMARY session=%u reason=%s seen=%u classified=%u held=%u unresolved_origins=%u log_failures=%u coverage_authority=0 material_response=0 stagger_writes=0 damage_replacement=0",
        gSession,reason,gSeen,gClassified,gHeld,gOriginUnknown,gLogFailures);
    gStarted=gReady=false;gRegistry.Reset();gMods={};
}
void Observe(unsigned session,unsigned sequence,std::uint64_t transaction,const reader::Snapshot& snapshot) noexcept {
    const ErrorGuard error;
    if(!gStarted || session!=gSession || GetCurrentThreadId()!=gThread || gSeen>=64)return;
    ++gSeen;
    coverage::Result result;
    const char* reason=gReason;
    if(gReady && snapshot.enumerationComplete && snapshot.stableDoubleRead
        && reader::Complete(snapshot.code) && snapshot.itemCount<=reader::kMaxEquippedArmour) {
        coverage::Input input;
        input.target=coverage::Target::EquipmentCharacter;input.enumerationComplete=true;input.stableDoubleRead=true;
        input.count=snapshot.itemCount;
        for(unsigned i=0;i<snapshot.itemCount;++i) {
            const auto& item=snapshot.items[i]; const auto key=origin::Resolve(gMods,item.formId);
            const bool resolved=key.code==origin::Code::Resolved;
            if(!resolved)++gOriginUnknown;
            input.items[i]={item.instanceToken,key.key,resolved,item.partMask,item.conditionRatio};
            if(!log::Write("ARMOUR_ORIGIN session=%u seq=%u tx=%llu item=%u form=%08X status=%s plugin=\"%.*s\" local=%06X winning_override_verified=0",
                session,sequence,static_cast<unsigned long long>(transaction),i+1,item.formId,origin::Name(key.code),
                static_cast<int>(key.key.plugin.size()),resolved?key.key.plugin.data():"",key.key.localId))++gLogFailures;
        }
        result=coverage::Classify(input,gRegistry.Catalog());reason=coverage::ReasonName(result.reason);
    } else if(gReady)reason="raw_snapshot_incomplete";
    const bool classified=result.status==coverage::Status::ClassifiedOnly;
    if(classified)++gClassified;else ++gHeld;
    if(!log::Write("ARMOUR_COVERAGE session=%u seq=%u tx=%llu target=%08X classified=%u reason=%s item_count=%u coverage_authority=0 layer_order_verified=0 bare_region_verified=0 material_response=0 stagger_writes=0 damage_replacement=0",
        session,sequence,static_cast<unsigned long long>(transaction),snapshot.targetId,classified?1u:0u,reason,static_cast<unsigned>(result.count)))++gLogFailures;
    if(!classified)return;
    for(std::size_t i=0;i<result.count;++i) {
        const auto& row=result.items[i];const auto& ext=row.regions;
        if(!log::Write("ARMOUR_COVERAGE_ITEM session=%u seq=%u item=%u instance=%016llX plugin=\"%.*s\" local=%06X revision=%u condition=%.9g head=%s torso=%s left_arm=%s right_arm=%s left_leg=%s right_leg=%s partial_hit_surface=unresolved classification_only=1",
            session,sequence,static_cast<unsigned>(i+1),static_cast<unsigned long long>(row.instance),static_cast<int>(row.key.plugin.size()),row.key.plugin.data(),row.key.localId,row.profileRevision,row.condition,
            ExtentName(ext[0]),ExtentName(ext[1]),ExtentName(ext[2]),ExtentName(ext[3]),ExtentName(ext[4]),ExtentName(ext[5])))++gLogFailures;
    }
}
static_assert(!coverage::kGameplayWrites && !coverage::Result::regionCoverageAuthority);
}

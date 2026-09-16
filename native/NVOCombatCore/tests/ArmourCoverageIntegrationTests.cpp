#include "ArmourCoverage.hpp"
#include "CurrentHit.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <array>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {
unsigned checks{}; bool layout=true; bool readFail{};
std::array<unsigned char,0x618> handler{};
std::array<unsigned char,0x410> mods[3];
std::vector<std::string> logs;
void Check(bool pass,const char* name){if(!pass){std::printf("FAIL %s\n",name);std::exit(1);}++checks;}
void Setup(){
    handler.fill(0);std::uint32_t count=3;std::memcpy(handler.data()+0x218,&count,4);
    const char* names[]={"FalloutNV.esm","NVO.esm","Custom Power Armor + Extras.esp"};
    for(unsigned i=0;i<3;++i){mods[i].fill(0);strcpy_s(reinterpret_cast<char*>(mods[i].data()+0x20),260,names[i]);mods[i][0x40C]=static_cast<unsigned char>(i);
        auto p=reinterpret_cast<std::uint32_t>(mods[i].data());std::memcpy(handler.data()+0x21C+4*i,&p,4);}
}
bool Has(const char* text){for(const auto& line:logs)if(line.find(text)!=std::string::npos)return true;return false;}
unsigned Count(const char* prefix){unsigned n=0;for(const auto& line:logs)if(line.rfind(prefix,0)==0)++n;return n;}
std::wstring ConfigPath(){
    wchar_t path[32768]{};const auto n=GetModuleFileNameW(nullptr,path,32768);Check(n>0&&n<32768,"checker executable path");
    auto* slash=wcsrchr(path,L'\\');Check(slash!=nullptr,"checker folder");*slash=0;
    std::wstring root=path;
    // All files below this standalone checker's workspace output folder.
    for(const auto* part:{L"\\Data",L"\\Data\\NVSE",L"\\Data\\NVSE\\Plugins"}){
        const auto folder=root+part;if(!CreateDirectoryW(folder.c_str(),nullptr))Check(GetLastError()==ERROR_ALREADY_EXISTS,"test config directory");}
    return root+L"\\Data\\NVSE\\Plugins\\NVOArmourCoverage.tsv";
}
void Write(const std::wstring& path,const std::string& data){
    HANDLE f=CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);Check(f!=INVALID_HANDLE_VALUE,"write test-owned config");
    DWORD written{};const bool ok=WriteFile(f,data.data(),static_cast<DWORD>(data.size()),&written,nullptr)&&written==data.size();CloseHandle(f);Check(ok,"complete fixture write");
}
const std::string valid="NVO_ARMOUR_COVERAGE_V1\nFalloutNV.esm|020420|1|00000004|none|partial|partial|partial|partial|partial\nFalloutNV.esm|020426|1|00000602|partial|none|none|none|none|none\nNVO.esm|00ABCD|1|00000004|none|full|partial|partial|partial|partial\n";
nvo::armour::reader::Snapshot Snapshot(){
    using namespace nvo::armour::reader;nvo::armour::reader::Snapshot s;s.code=Code::CompleteWithArmour;s.targetId=0xFF001234;s.itemCount=2;s.enumerationComplete=s.stableDoubleRead=true;
    s.items[0].instanceToken=100;s.items[0].formId=0x20420;s.items[0].partMask=4;s.items[0].conditionRatio=0.5f;
    s.items[1].instanceToken=101;s.items[1].formId=0x20426;s.items[1].partMask=0x602;s.items[1].conditionRatio=1;return s;
}
DWORD WINAPI Foreign(void*){nvo::armour::coverage_log::Begin(100);nvo::armour::coverage_log::Observe(1,1,1,Snapshot());nvo::armour::coverage_log::Suspend("foreign");return 0;}
}
namespace nvo::hit {
bool ProjectileLayoutReady() noexcept {return layout;}
bool ReadBytes(const void* from,void* to,std::size_t size) noexcept {
    if(readFail)return false;
    if(from==reinterpret_cast<void*>(0x11C3F2C)&&size==4){const auto p=reinterpret_cast<std::uint32_t>(handler.data());std::memcpy(to,&p,4);return true;}
    const auto a=reinterpret_cast<std::uintptr_t>(from);
    auto inside=[&](const auto& block){const auto b=reinterpret_cast<std::uintptr_t>(block.data());return a>=b&&size<=block.size()&&a-b<=block.size()-size;};
    bool readable=inside(handler);for(const auto& m:mods)readable=readable||inside(m);
    if(!readable)return false;std::memcpy(to,from,size);return true;
}
}
namespace nvo::log {
bool Write(const char* format,...) noexcept {char line[4096]{};va_list args;va_start(args,format);const int n=vsnprintf_s(line,sizeof(line),_TRUNCATE,format,args);va_end(args);if(n<0)return false;logs.emplace_back(line);return true;}
}
int main(){
    using namespace nvo::armour::coverage_log;
    Setup();const auto path=ConfigPath();Write(path,valid);logs.clear();
    SetLastError(12345);Begin(1);Check(GetLastError()==12345,"activation preserves host error");
    Check(Has("ready=1 reason=ready origin_mods=3 profiles=3"),"production activation loads guarded origins and loose config");
    auto snapshot=Snapshot();Observe(1,1,1,snapshot);
    Check(Has("plugin=\"FalloutNV.esm\" local=020420")&&Has("head=partial torso=none"),"origin and authored extent rows");
    Check(Has("revision=1 condition=0.5"),"condition forwarded unchanged");
    const auto n=logs.size();Observe(999,2,2,snapshot);Check(logs.size()==n,"stale session ignored");
    HANDLE worker=CreateThread(nullptr,0,Foreign,nullptr,0,nullptr);Check(worker!=nullptr,"foreign-thread fixture");Check(WaitForSingleObject(worker,5000)==WAIT_OBJECT_0,"foreign fixture completed");CloseHandle(worker);Check(logs.size()==n,"foreign begin observe suspend cannot change active state");
    for(unsigned i=2;i<=70;++i)Observe(1,i,i,snapshot);
    Check(Count("ARMOUR_COVERAGE session=")==64&&Count("ARMOUR_COVERAGE_ITEM ")==128,"own64 snapshot cap bounded");
    Suspend("reload");Check(Has("seen=64 classified=64 held=0"),"bounded summary");
    logs.clear();Begin(2);Observe(2,1,71,snapshot);Check(Count("ARMOUR_COVERAGE_ITEM ")==2,"reload starts fresh classifications");
    snapshot.items[1].formId=0x20423;Observe(2,2,72,snapshot);
    Check(Has("reason=unknown_equipment item_count=0"),"unknown equipment emits no partial classification");
    snapshot.items[1].formId=0xFF001000;Observe(2,3,73,snapshot);
    Check(Has("status=dynamic_form_unmapped")&&Has("reason=origin_unresolved item_count=0"),"dynamic form is explicit hold");
    snapshot=Snapshot();snapshot.itemCount=1;snapshot.items[0].formId=0x0100ABCD;Observe(2,4,74,snapshot);
    Check(Has("plugin=\"NVO.esm\" local=00ABCD")&&Has("head=none torso=full"),"synthetic custom NVO profile runtime path");
    snapshot.enumerationComplete=false;Observe(2,5,75,snapshot);Check(Has("reason=raw_snapshot_incomplete item_count=0"),"incomplete raw snapshot not classified");
    Suspend("config_reload");Write(path,valid+"bad=data\n");logs.clear();Begin(3);Observe(3,1,76,Snapshot());
    Check(Has("ready=0")&&Count("ARMOUR_COVERAGE_ITEM ")==0&&!Has("classified=1"),"bad reload cannot reuse old profile state");
    Suspend("read_guard");Write(path,valid);logs.clear();readFail=true;Begin(4);Observe(4,1,77,Snapshot());
    Check(Has("reason=origin_table_unavailable")&&Count("ARMOUR_ORIGIN ")==0,"failed table read prevents identity claims");readFail=false;Suspend("layout");
    logs.clear();layout=false;Begin(5);Check(Has("reason=layout_unavailable"),"existing layout guard required before fixed-address read");layout=true;Suspend("missing_config");
    Check(DeleteFileW(path.c_str())!=0,"remove only test-owned fixture config");logs.clear();Begin(6);Observe(6,1,78,Snapshot());
    Check(Has("reason=config_missing_or_unreadable")&&Count("ARMOUR_COVERAGE_ITEM ")==0,"missing config stays disabled");Suspend("finished");
    for(const auto& line:logs)Check(line.find("damage_replacement=1")==std::string::npos&&line.find("stagger_writes=1")==std::string::npos,"no gameplay authority");
    std::printf("PASS %u production-integration fixture checks; no game launched\n",checks);
}

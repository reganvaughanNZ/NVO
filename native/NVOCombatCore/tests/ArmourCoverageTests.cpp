#include "ArmourCoverageConfig.hpp"
#include "ArmourOrigin.hpp"
#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <string>
#include <vector>
using namespace nvo;
namespace {
unsigned checks{};
void Check(bool pass,const char* name){if(!pass){std::printf("FAIL %s\n",name);std::exit(1);}++checks;}
struct ModBlob {std::array<unsigned char,0x410> data{};};
struct Fixture {
    std::uint32_t root{};
    std::array<unsigned char,0x618> handler{};
    ModBlob mods[3];
    unsigned calls{},failAt{},mutateAt{};
    Fixture(){Reset();}
    void Name(unsigned i,const char* name){std::memset(mods[i].data.data()+0x20,0,260);strcpy_s(reinterpret_cast<char*>(mods[i].data.data()+0x20),260,name);}
    void Count(std::uint32_t n){std::memcpy(handler.data()+0x218,&n,4);}
    void Reset(){
        calls=failAt=mutateAt=0;root=reinterpret_cast<std::uint32_t>(handler.data());handler.fill(0);Count(3);
        for(unsigned i=0;i<3;++i){mods[i].data.fill(0);mods[i].data[0x40C]=static_cast<unsigned char>(i);
            auto address=reinterpret_cast<std::uint32_t>(mods[i].data.data());std::memcpy(handler.data()+0x21C+4*i,&address,4);}
        Name(0,"FalloutNV.esm");Name(1,"NVO.esm");Name(2,"Custom Power Armor + Extras.esp");
    }
    static bool Read(void* context,const void* source,void* destination,std::size_t size) noexcept {
        auto& f=*static_cast<Fixture*>(context);++f.calls;
        if(f.failAt==f.calls)return false;
        if(f.mutateAt==f.calls)f.Name(1,"Changed.esp");
        const auto a=reinterpret_cast<std::uintptr_t>(source);
        auto inside=[&](const void* start,std::size_t length){const auto b=reinterpret_cast<std::uintptr_t>(start);return a>=b && size<=length && a-b<=length-size;};
        bool ok=inside(&f.root,4)||inside(f.handler.data(),f.handler.size());
        for(const auto& m:f.mods)ok=ok||inside(m.data.data(),m.data.size());
        if(!ok)return false;std::memcpy(destination,source,size);return true;
    }
    bool Capture(armour::origin::Table& out){return armour::origin::CaptureStable({this,Read},reinterpret_cast<std::uintptr_t>(&root),out);}
};
const char* header="NVO_ARMOUR_COVERAGE_V1\n";
const char* body="FalloutNV.esm|020420|1|00000004|none|partial|partial|partial|partial|partial\n";
const char* helmet="FalloutNV.esm|020426|1|00000602|partial|none|none|none|none|none\n";
const char* custom="NVO.esm|00ABCD|1|00000004|none|full|partial|partial|partial|partial\n";
coverage::Input Input(std::uint32_t id=0x20420){coverage::Input x;x.target=coverage::Target::EquipmentCharacter;x.enumerationComplete=x.stableDoubleRead=true;x.count=1;x.items[0]={1,{"FalloutNV.esm",id},true,4,1};return x;}
}
int main(){
    using namespace armour;
    Fixture f;origin::Table table;
    const auto before=f.handler;
    Check(f.Capture(table)&&table.stable&&table.count==3,"guarded double table read");
    const auto reads=f.calls;Check(before==f.handler,"table reader does not write source memory");
    auto key=origin::Resolve(table,0x0100ABCD);
    Check(key.code==origin::Code::Resolved&&coverage::SameKey(key.key,{"NVO.esm",0xABCD}),"NVO origin and local ID");
    key=origin::Resolve(table,0x0200ABCD);Check(key.code==origin::Code::Resolved&&key.key.plugin=="Custom Power Armor + Extras.esp","resource plugin with spaces and plus");
    Check(origin::Resolve(table,0x00020420).key.plugin=="FalloutNV.esm","override keeps original owning plugin");
    Check(origin::Resolve(table,0xFF002420).code==origin::Code::DynamicForm,"dynamic form is not a plugin record");
    Check(origin::Resolve(table,0x03002420).code==origin::Code::IndexUnavailable,"unknown index fails closed");
    Check(origin::Resolve(table,0x01000000).code==origin::Code::InvalidForm,"zero local form rejected");
    for(unsigned i=1;i<=reads;++i){f.Reset();f.failAt=i;Check(!f.Capture(table)&&!table.stable&&table.count==0,"failure at every guarded read clears whole table");}
    f.Reset();f.Count(0);Check(!f.Capture(table),"zero count rejected");
    f.Reset();f.Count(256);Check(!f.Capture(table),"count over255 rejected before traversal");
    f.Reset();f.root=1;Check(!f.Capture(table),"low misaligned pointer rejected");
    f.Reset();f.mods[1].data[0x40C]=2;Check(!f.Capture(table),"slot/index disagreement");
    f.Reset();f.Name(1,"FALLOUTNV.ESM");Check(!f.Capture(table),"duplicate mod name case insensitive");
    f.Reset();f.Name(0,"Wrong.esm");Check(!f.Capture(table),"base game must own index zero");
    f.Reset();std::memset(f.mods[1].data.data()+0x20,'x',260);Check(!f.Capture(table),"unterminated module name");
    f.Reset();f.Name(1,"../NVO.esm");Check(!f.Capture(table),"path-like module name refused");
    f.Reset();f.mutateAt=reads/2+1;Check(!f.Capture(table)&&!table.stable,"mutation between passes rejected");
    f.Reset();f.Name(1,"Custom Power Armor + Extras.esp");f.Name(2,"NVO.esm");Check(f.Capture(table),"reordered load table recaptured");
    key=origin::Resolve(table,0x0200ABCD);Check(coverage::SameKey(key.key,{"NVO.esm",0xABCD}),"same NVO record after index change");
    table.stable=false;Check(origin::Resolve(table,0x20420).code==origin::Code::TableUnavailable,"invalidated table cannot resolve");
    config::Registry registry;
    const std::string valid=std::string(header)+body+helmet+custom;
    Check(registry.Load(valid)&&registry.Catalog().Count()==3,"complete config with custom NVO profile");
    Check(coverage::Classify(Input(),registry.Catalog()).status==coverage::Status::ClassifiedOnly,"configured classification");
    auto input=Input(0xABCD);input.items[0].key.plugin="NVO.esm";
    auto result=coverage::Classify(input,registry.Catalog());Check(result.regions[1].full==1&&!result.regionCoverageAuthority,"custom full extent remains authored classification");
    Check(coverage::Classify(Input(0xAAAA),registry.Catalog()).reason==coverage::Reason::UnknownEquipment,"unknown armour retains native handling");
    input.items[0].observedEquipMask=0x602;Check(coverage::Classify(input,registry.Catalog()).reason==coverage::Reason::RecordMismatch,"custom record drift held");
    std::vector<std::string> invalid={"",std::string(body),std::string(header),std::string(header)+body+body,
        std::string(header)+"FalloutNV.esm|020420|1|00000004|none\n",
        std::string(header)+"FalloutNV.esm|020420|1|00000004|none|partial|partial|partial|partial|partial|extra\n",
        std::string(header)+"FalloutNV.esm|FF020420|1|00000004|none|partial|partial|partial|partial|partial\n",
        std::string(header)+"FalloutNV.esm|020420|4294967296|00000004|none|partial|partial|partial|partial|partial\n",
        std::string(header)+"FalloutNV.esm|020420|0|00000004|none|partial|partial|partial|partial|partial\n",
        std::string(header)+"FalloutNV.esm|020420|1|00100000|none|partial|partial|partial|partial|partial\n",
        std::string(header)+"FalloutNV.esm|020420|1|00000000|none|partial|partial|partial|partial|partial\n",
        std::string(header)+"FalloutNV.esm|020420|1|00000004|none|50%|partial|partial|partial|partial\n",
        valid+"unknown-setting=1\n",std::string(config::kMaxBytes+1,'x'),valid+std::string(1,'\0')};
    for(const auto& text:invalid){Check(registry.Load(valid),"valid state before failure");Check(!registry.Load(text)&&!registry.Catalog().Valid()&&registry.Catalog().Count()==0,"malformed reload disables old catalog rather than retaining stale rules");}
    Check(registry.Load(std::string("\xEF\xBB\xBF")+"# comment\r\nNVO_ARMOUR_COVERAGE_V1\r\n"+body),"BOM and CRLF accepted");
    registry.Reset();Check(!registry.Catalog().Valid(),"explicit lifecycle reset");
    std::string maxConfig=header;
    for(unsigned i=1;i<=256;++i){char row[180]{};std::snprintf(row,sizeof(row),"NVO.esm|%06X|1|00000004|none|partial|partial|partial|partial|partial\n",i);maxConfig+=row;}
    Check(registry.Load(maxConfig)&&registry.Catalog().Count()==256,"exact256 profile limit");
    Check(!registry.Load(maxConfig+custom),"257th profile rejected");
    Check(registry.Load(valid),"restore ready catalog");
    for(unsigned i=0;i<10000;++i){result=coverage::Classify(Input(),registry.Catalog());if(result.count!=1||result.regions[1].partial!=1)return 2;}
    Check(registry.Catalog().Valid(),"10000 prepared-catalog calls without per-hit parsing or registry validation");
    std::printf("PASS %u checks; %u guarded-read failure points; 10000 prepared classifications\n",checks,reads);
}

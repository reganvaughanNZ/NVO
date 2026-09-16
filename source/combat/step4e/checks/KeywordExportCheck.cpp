#include "ArmourCoverageConfig.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>

namespace {
unsigned checks{};
void Check(bool pass,const char* message) {
    if(!pass){std::printf("FAIL %s\n",message);std::exit(1);}++checks;
}
std::string Read(const char* path) {
    std::ifstream stream(path,std::ios::binary);
    Check(stream.is_open(),"generated config readable");
    return std::string(std::istreambuf_iterator<char>(stream),std::istreambuf_iterator<char>());
}
nvo::coverage::Input MakeInput() {
    nvo::coverage::Input input;
    input.target=nvo::coverage::Target::EquipmentCharacter;
    input.enumerationComplete=input.stableDoubleRead=true;
    return input;
}
}
int main(int argc,char** argv) {
    using namespace nvo::coverage;
    Check(argc==3,"two generated fixture paths required");
    nvo::armour::config::Registry registry;
    Check(registry.Load(Read(argv[1])),"production327 parser accepts shared-profile export");
    Check(registry.Catalog().Count()==2,"base export contains only the two tested records");
    auto input=MakeInput();input.count=2;
    input.items[0]={1,{"FalloutNV.esm",0x20420},true,4,0.375};
    input.items[1]={2,{"FalloutNV.esm",0x20426},true,0x602,1};
    auto result=Classify(input,registry.Catalog());
    Check(result.status==Status::ClassifiedOnly && result.count==2,"base classifier accepts exact identities");
    Check(result.items[0].condition==0.375,"instance condition remains separate from template");
    Check(result.items[0].regions[0]==Extent::None && result.items[0].regions[1]==Extent::Partial,"body regions preserved");
    Check(result.items[1].regions[0]==Extent::Partial && result.items[1].regions[1]==Extent::None,"helmet regions preserved");
    input.items[0].observedEquipMask=8;
    Check(Classify(input,registry.Catalog()).reason==Reason::RecordMismatch,"record drift guard retained");
    input.items[0].observedEquipMask=4;input.items[0].key.localId=0x1234;
    Check(Classify(input,registry.Catalog()).reason==Reason::UnknownEquipment,"unknown record still held");
    Check(registry.Load(Read(argv[2])),"production327 parser accepts synthetic custom records");
    Check(registry.Catalog().Count()==3,"synthetic fixture has three records");
    input=MakeInput();input.count=3;
    input.items[0]={1,{"nvo.ESM",0xAB01},true,4,1};
    input.items[1]={2,{"NVO.esm",0xAB02},true,4,0.5};
    input.items[2]={3,{"Custom + Armor.esp",0xAB03},true,0x602,1};
    result=Classify(input,registry.Catalog());
    Check(result.status==Status::ClassifiedOnly && result.count==3,"custom origin names accepted independent of tag representation");
    Check(result.items[0].regions[1]==Extent::Partial && result.items[0].profileRevision==1,"shared default retained on first record");
    Check(result.items[1].regions[1]==Extent::Unknown && result.items[1].regions[2]==Extent::None && result.items[1].profileRevision==2,"exact exception applied only to second record");
    Check(result.items[2].regions[0]==Extent::Partial && result.items[2].regions[1]==Extent::None,"custom helmet independent of suits");
    input.items[1].key.localId=0xAB04;
    result=Classify(input,registry.Catalog());
    Check(result.reason==Reason::UnknownEquipment && result.count==0,"unmapped custom gear cannot acquire a shared default automatically");
    Check(!Result::regionCoverageAuthority && !Result::gameplayWrites && !Result::armourPreview && !Result::bareRegionVerified,"no authority promoted by profile selection");
    std::printf("PASS %u checks through production327 parser/classifier; standalone x86; no game launch\n",checks);
}

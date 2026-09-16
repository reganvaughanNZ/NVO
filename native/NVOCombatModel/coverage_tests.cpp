#include "CoverageProfiles.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <utility>
using namespace nvo::coverage;
namespace {
unsigned checks{};
void Check(bool ok, const char* name) {
    if (!ok) { std::printf("FAIL %s\n", name); std::exit(1); }
    ++checks; std::printf("PASS %s\n", name);
}
#include "CoverageFixtures.inl"
bool Withheld(const Result& r) {
    return !r.gameplayWrites && !r.regionCoverageAuthority && !r.impactSnapshotAuthority
        && !r.layerOrderVerified && !r.bareRegionVerified && !r.armourPreview;
}
bool Empty(const Result& r) {
    if (r.count) return false;
    for (const auto& item : r.items) if (item.instance) return false;
    for (const auto& s : r.regions) if (s.full || s.partial || s.unknown) return false;
    return Withheld(r);
}
Input Ready() {
    Input in;
    in.target=Target::EquipmentCharacter; in.enumerationComplete=true; in.stableDoubleRead=true; in.count=2;
    in.items[0]={100,{"FalloutNV.esm",0x20420},true,4,1};
    in.items[1]={101,{"FalloutNV.esm",0x20426},true,0x602,1};
    return in;
}
void Expect(const Input& in, const std::vector<Profile>& cat, Status status, Reason reason, const char* name) {
    const auto r=Classify(in,cat); Check(r.status==status && r.reason==reason && Empty(r),name);
}
}
int main() {
    const auto catalog=AuthoredProfiles(); const auto ready=Ready();
    Check(ValidCatalog(catalog),"authored catalog valid");
    auto r=Classify(ready,catalog);
    Check(r.status==Status::ClassifiedOnly && r.count==2 && Withheld(r),"body and helmet classify without authority");
    Check(r.regions[0].partial==1 && r.regions[1].partial==1,"separate head and torso potential coverage");
    Check(r.items[0].regions[0]==Extent::None && r.items[1].regions[1]==Extent::None,"body never protects head and helmet never torso");
    Check(r.regions[0].full==0 && !r.bareRegionVerified,"partial head never promoted to full or bare");
    auto in=ready; in.items[0].condition=0.5; r=Classify(in,catalog);
    Check(r.items[0].condition==0.5 && r.regions[1].partial==1,"condition retained without converting extent or strength");
    in=ready; in.items[0].condition=0; r=Classify(in,catalog);
    Check(r.count==2 && r.items[0].condition==0,"zero-condition item retained for future material policy");
    in=ready; in.count=1; r=Classify(in,catalog);
    Check(r.status==Status::ClassifiedOnly && r.regions[0].partial==0 && r.regions[1].partial==1 && !r.bareRegionVerified,"helmet removal does not certify bare head");
    in=ready; in.items[0]=in.items[1]; in.count=1; r=Classify(in,catalog);
    Check(r.regions[0].partial==1 && r.regions[1].partial==0,"helmet alone only maps head");
    in=ready; in.count=0; r=Classify(in,catalog);
    Check(r.status==Status::ClassifiedOnly && Empty(r),"no inventory armour is not verified bare or no inherent protection");
    in=ready; std::swap(in.items[0],in.items[1]); r=Classify(in,catalog);
    Check(r.regions[0].partial==1 && r.regions[1].partial==1 && r.items[0].instance==101 && !r.layerOrderVerified,"inventory order is not layer order");
    in=ready; in.items[1]=in.items[0]; in.items[1].instance=102; r=Classify(in,catalog);
    Check(r.count==2 && r.regions[1].partial==2 && !r.layerOrderVerified,"distinct same-form instances retained without layer ordering");
    in=ready; in.items[0].key.plugin="fAlLoUtNv.EsM";
    Check(Classify(in,catalog).status==Status::ClassifiedOnly,"plugin identity case insensitive");
    in=ready; in.items[1].key.plugin="Other.esp";
    Expect(in,catalog,Status::WaitingForEvidence,Reason::UnknownEquipment,"same local ID in another plugin is not the same item");
    in=ready; in.items[1].key.localId=0x999999;
    Expect(in,catalog,Status::WaitingForEvidence,Reason::UnknownEquipment,"unknown item rejects whole classification including prior valid item");
    in=ready; in.items[1].originResolved=false;
    Expect(in,catalog,Status::WaitingForEvidence,Reason::OriginUnresolved,"unresolved load index not guessed");
    in=ready; in.items[1].key.localId=0x0B020426;
    Expect(in,catalog,Status::InvalidInput,Reason::InvalidItem,"runtime ID cannot masquerade as local ID");
    in=ready; in.items[1].observedEquipMask=4;
    Expect(in,catalog,Status::WaitingForEvidence,Reason::RecordMismatch,"equipment record drift blocked");
    in=ready; in.items[1].instance=in.items[0].instance;
    Expect(in,catalog,Status::InvalidInput,Reason::DuplicateInstance,"duplicate instance rejects entire result");
    for (const double bad : {-0.1,1.1,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}) {
        in=ready; in.items[1].condition=bad;
        Expect(in,catalog,Status::InvalidInput,Reason::InvalidItem,"invalid condition fails closed");
    }
    in=ready; in.items[1].instance=0; Expect(in,catalog,Status::InvalidInput,Reason::InvalidItem,"zero instance rejected");
    in=ready; in.items[1].observedEquipMask=0; Expect(in,catalog,Status::InvalidInput,Reason::InvalidItem,"zero raw mask rejected");
    in=ready; in.items[1].observedEquipMask=0x100000; Expect(in,catalog,Status::InvalidInput,Reason::InvalidItem,"unknown raw slot bits rejected");
    in=ready; in.count=kMaxItems+1; Expect(in,catalog,Status::InvalidInput,Reason::InvalidItem,"count bound checked before array access");
    in=ready; in.count=kMaxItems;
    for (std::size_t i=0;i<kMaxItems;++i) {in.items[i]=ready.items[0];in.items[i].instance=200+i;}
    Check(Classify(in,catalog).count==kMaxItems,"exact item bound accepted");
    in=ready; in.enumerationComplete=false; Expect(in,catalog,Status::WaitingForEvidence,Reason::SnapshotIncomplete,"partial inventory rejected");
    in=ready; in.stableDoubleRead=false; Expect(in,catalog,Status::WaitingForEvidence,Reason::SnapshotIncomplete,"unstable inventory rejected");
    in=ready; in.target=Target::Unknown; Expect(in,catalog,Status::WaitingForEvidence,Reason::TargetUnknown,"unknown actor kind remains unknown");
    in=ready; in.target=Target::Creature; Expect(in,catalog,Status::Unsupported,Reason::CreatureProfileRequired,"creature never interpreted as humanoid armour");
    in.count=0; Expect(in,catalog,Status::Unsupported,Reason::CreatureProfileRequired,"empty creature inventory cannot become bare");
    auto cat=catalog; cat.push_back(cat[0]); cat.back().key.plugin="FALLOUTNV.ESM";
    Expect(ready,cat,Status::InvalidInput,Reason::InvalidCatalog,"duplicate catalog keys rejected case insensitively");
    cat=catalog; cat[0].regions[0]=static_cast<Extent>(99);
    Expect(ready,cat,Status::InvalidInput,Reason::InvalidCatalog,"invalid coverage enum rejected");
    cat=catalog; cat[0].revision=0; Expect(ready,cat,Status::InvalidInput,Reason::InvalidCatalog,"unversioned profile rejected");
    cat=catalog; cat[0].expectedEquipMask=0; Expect(ready,cat,Status::InvalidInput,Reason::InvalidCatalog,"catalog mask validated");
    cat.clear(); Expect(ready,cat,Status::InvalidInput,Reason::InvalidCatalog,"empty catalog rejected");
    cat.assign(kMaxProfiles+1,catalog[0]); Expect(ready,cat,Status::InvalidInput,Reason::InvalidCatalog,"catalog bound enforced");
    for (const auto name : {"", "../FalloutNV.esm", "C:\\FalloutNV.esm", "FalloutNV.esm ", "Bad\n.esm", "Thing.esl"})
        Check(!ValidKey({name,1}),"unsafe or unsupported plugin key rejected");
    Check(!ValidKey({"FalloutNV.esm",0}),"zero local ID rejected");
    cat=catalog; cat[0].regions[1]=Extent::Full; r=Classify(ready,cat);
    Check(r.regions[1].full==1 && !r.regionCoverageAuthority,"synthetic full coverage still no hit authority");
    cat=catalog; cat[0].regions[1]=Extent::Unknown; r=Classify(ready,cat);
    Check(r.regions[1].unknown==1 && r.regions[1].full==0,"authored regional uncertainty retained");
    cat=catalog; cat[0].regions.fill(Extent::None); r=Classify(ready,cat);
    Check(r.count==2 && r.regions[1].partial==0 && !r.bareRegionVerified,"explicit no-cover item retained without bare inference");
    cat=catalog; cat[0].regions[0]=Extent::Partial; r=Classify(ready,cat);
    Check(r.regions[0].partial==2 && !r.layerOrderVerified,"overlapping authoring never invents layer order");
    const auto fixtures=CapturedFixtures(); Check(fixtures.size()==76,"76 captured live snapshots available");
    unsigned replays{};
    for (const auto& f : fixtures) {
        r=Classify(f.input,catalog);
        if (r.status!=Status::ClassifiedOnly || r.count!=f.input.count || !Withheld(r)
            || r.regions[0].partial!=f.headPartial || r.regions[1].partial!=f.torsoPartial) {
            std::printf("FAIL capture replay %u\n",replays);return 1;
        }
        for (std::size_t i=0;i<r.count;++i)
            if (r.items[i].instance!=f.input.items[i].instance || r.items[i].condition!=f.input.items[i].condition) return 2;
        ++replays;
    }
    Check(replays==76,"live body/helmet/removal/condition/reload/stress snapshots classify");
    in=ready;
    for(unsigned i=0;i<10000;++i) {
        r=Classify(in,catalog);
        if(r.status!=Status::ClassifiedOnly || r.count!=2 || r.regions[0].partial!=1 || !Withheld(r)) return 3;
    }
    Check(in.items[0].instance==100 && in.items[0].condition==1 && in.count==2,"repeated calls do not mutate caller input");
    std::printf("PASS %u checks; %u captured snapshots; 10000 deterministic repetitions\n",checks,replays);
    return 0;
}

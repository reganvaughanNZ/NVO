#include "ArmourCoverageConfig.hpp"
#include <cstring>
#include <limits>

namespace nvo::armour::config {
namespace {
using U32=std::uint32_t;
std::string_view Trim(std::string_view s) noexcept {
    while(!s.empty() && (s.front()==' ' || s.front()=='\t' || s.front()=='\r')) s.remove_prefix(1);
    while(!s.empty() && (s.back()==' ' || s.back()=='\t' || s.back()=='\r')) s.remove_suffix(1);
    return s;
}
bool Number(std::string_view s,unsigned base,std::size_t exact,U32& out) noexcept {
    out=0;if(s.empty() || (exact && s.size()!=exact))return false;
    for(char c:s) {
        unsigned d=c>='0' && c<='9'? static_cast<unsigned>(c-'0') :
            c>='A' && c<='F'?static_cast<unsigned>(c-'A'+10):c>='a' && c<='f'?static_cast<unsigned>(c-'a'+10):16;
        if(d>=base || out>(UINT32_MAX-d)/base)return false;
        out=out*base+d;
    }
    return true;
}
bool Extent(std::string_view s,coverage::Extent& out) noexcept {
    if(s=="none")out=coverage::Extent::None;
    else if(s=="partial")out=coverage::Extent::Partial;
    else if(s=="full")out=coverage::Extent::Full;
    else if(s=="unknown")out=coverage::Extent::Unknown;
    else return false;
    return true;
}
}
bool Registry::Load(std::string_view text) noexcept {
    Reset();
    if(text.empty() || text.size()>kMaxBytes || text.find('\0')!=text.npos)return Fail("config_size_or_nul");
    if(text.substr(0,3)==std::string_view("\xEF\xBB\xBF",3))text.remove_prefix(3);
    bool header=false;
    while(!text.empty()) {
        const auto end=text.find('\n');
        auto line=Trim(text.substr(0,end));
        if(end==text.npos)text={};else text.remove_prefix(end+1);
        if(line.empty() || line.front()=='#')continue;
        if(!header) {if(line!="NVO_ARMOUR_COVERAGE_V1")return Fail("config_schema");header=true;continue;}
        if(count_==coverage::kMaxProfiles)return Fail("config_profile_limit");
        std::string_view fields[10]{};
        for(unsigned i=0;i<10;++i) {
            const auto split=line.find('|');
            if((i<9 && split==line.npos) || (i==9 && split!=line.npos))return Fail("config_field_count");
            fields[i]=Trim(line.substr(0,split));
            if(i<9)line.remove_prefix(split+1);
        }
        auto& owned=rows_[count_]; owned={}; auto& p=owned.profile;
        U32 local{};
        if(fields[0].size()>128 || !Number(fields[1],16,6,local) || !coverage::ValidKey({fields[0],local}))return Fail("config_form_key");
        std::memcpy(owned.plugin,fields[0].data(),fields[0].size());
        p.key={std::string_view(owned.plugin,fields[0].size()),local};
        if(!Number(fields[2],10,0,p.revision) || !p.revision || !Number(fields[3],16,8,p.expectedEquipMask))return Fail("config_revision_or_mask");
        for(unsigned i=0;i<6;++i)if(!Extent(fields[4+i],p.regions[i]))return Fail("config_extent");
        ++count_;
    }
    if(!header || !count_)return Fail("config_empty");
    std::array<coverage::Profile,coverage::kMaxProfiles> profiles{};
    for(std::size_t i=0;i<count_;++i)profiles[i]=rows_[i].profile;
    if(!catalog_.Prepare(profiles.data(),count_))return Fail("config_invalid_or_duplicate_catalog");
    error_="ready";return true;
}
}

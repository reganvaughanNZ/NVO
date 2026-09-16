#include "ArmourOrigin.hpp"
#include <cstring>
#include <limits>

namespace nvo::armour::origin {
namespace {
using U32=std::uint32_t;
bool Address(std::uintptr_t p) noexcept { return p>=0x10000 && !(p&3u); }
bool Read(const reader::Memory& m,std::uintptr_t base,std::size_t offset,void* out,std::size_t size) noexcept {
    if (!m.read || !Address(base) || offset>UINT32_MAX-base || size>UINT32_MAX-(base+offset)) return false;
    return m.read(m.context,reinterpret_cast<const void*>(base+offset),out,size);
}
struct Pass { Table table; U32 handler{}; U32 tokens[kMaxMods]{}; };
bool Once(const reader::Memory& memory,std::uintptr_t slot,Pass& out) noexcept {
    if (!Read(memory,slot,0,&out.handler,4) || !Address(out.handler)
        || !Read(memory,out.handler,0x218,&out.table.count,4)
        || !out.table.count || out.table.count>kMaxMods) return false;
    for(unsigned i=0;i<out.table.count;++i) {
        auto& mod=out.table.mods[i]; char name[260]{};
        if(!Read(memory,out.handler,0x21C+4*i,&out.tokens[i],4) || !Address(out.tokens[i])
            || !Read(memory,out.tokens[i],0x20,name,sizeof(name))
            || !Read(memory,out.tokens[i],0x40C,&mod.index,1) || mod.index!=i) return false;
        const auto* end=static_cast<const char*>(std::memchr(name,0,sizeof(name)));
        if(!end || end-name>128 || !coverage::ValidKey({std::string_view(name,static_cast<std::size_t>(end-name)),1})) return false;
        std::memcpy(mod.name,name,static_cast<std::size_t>(end-name)+1);
        for(unsigned j=0;j<i;++j) if(coverage::SameKey({mod.name,1},{out.table.mods[j].name,1})) return false;
    }
    return coverage::SameKey({out.table.mods[0].name,1},{"FalloutNV.esm",1});
}
}
bool CaptureStable(const reader::Memory& memory,std::uintptr_t slot,Table& output) noexcept {
    output={}; Pass first{},second{};
    if(!Once(memory,slot,first) || !Once(memory,slot,second)
        || first.handler!=second.handler || first.table.count!=second.table.count) return false;
    for(unsigned i=0;i<first.table.count;++i)
        if(first.tokens[i]!=second.tokens[i] || first.table.mods[i].index!=second.table.mods[i].index
            || std::strcmp(first.table.mods[i].name,second.table.mods[i].name)) return false;
    output=first.table; output.stable=true; return true;
}
Key Resolve(const Table& table,U32 form) noexcept {
    if(!table.stable || !table.count || table.count>kMaxMods) return {};
    const U32 index=form>>24, local=form&0xFFFFFF;
    if(index==0xFF) return {Code::DynamicForm,{}};
    if(!local) return {Code::InvalidForm,{}};
    if(index>=table.count || table.mods[index].index!=index) return {Code::IndexUnavailable,{}};
    const auto& mod=table.mods[index];
    const auto* end=static_cast<const char*>(std::memchr(mod.name,0,sizeof(mod.name)));
    if(!end || !coverage::ValidKey({std::string_view(mod.name,static_cast<std::size_t>(end-mod.name)),local})) return {};
    return {Code::Resolved,{std::string_view(mod.name,static_cast<std::size_t>(end-mod.name)),local}};
}
const char* Name(Code code) noexcept {
    switch(code) {
    case Code::Resolved:return "resolved_origin";
    case Code::TableUnavailable:return "origin_table_unavailable";
    case Code::InvalidForm:return "invalid_form";
    case Code::DynamicForm:return "dynamic_form_unmapped";
    case Code::IndexUnavailable:return "origin_index_unavailable";
    }
    return "invalid_origin_code";
}
static_assert(sizeof(void*)==4,"Origin reader requires FNV x86 layout.");
}

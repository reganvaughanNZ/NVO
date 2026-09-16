#include "SpawnCall.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
using namespace nvo::spawn;
static_assert(sizeof(void*)==4,"Run the fixture with the x86 toolchain.");
namespace {
unsigned checks{}, calls{};
Arguments received{};
void* result=reinterpret_cast<void*>(0x12345678u);
void Check(bool ok,const char* name) {
    ++checks;
    if (!ok) { std::printf("FAIL %s\n",name); std::exit(1); }
}
__declspec(noinline) void* __cdecl Fake(Word a0,Word a1,Word a2,Word a3,Word a4,Word a5,Word a6,Word a7,
    Word a8,Word a9,Word a10,Word a11,Word a12,Word a13,Word a14,Word a15) {
    ++calls; received={a0,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15}; return result;
}
}
int main() {
    Arguments args{};
    for (unsigned i=0;i<16;++i) args[i]=0x12345000u+i;
    args[4]=0x80000000u; args[5]=0x7FC12345u; args[6]=0x3F800000u;
    args[11]=0xAABBCC01u; args[12]=0xDDCCBB00u;
    Check(Forward(Fake,args)==result,"cdecl return pointer unchanged");
    Check(calls==1,"exactly one continuation call");
    Check(args==received,"all sixteen words preserve bits including float and padded char slots");
    result=nullptr;
    Check(Forward(Fake,args)==nullptr && calls==2,"null creation result unchanged");
    for (unsigned i=0;i<10000;++i) {
        args[15]=i;
        if (Forward(Fake,args)!=nullptr || args!=received) return 2;
    }
    Check(calls==10002,"ten thousand stack round trips without extra calls");
    Receipt r{};
    Check(!r.Matches(1,2,3,4),"no event does not pair");
    r.Create(1,2,3,4);
    Check(r.Matches(1,2,3,4),"one exact creation pairs");
    Check(!r.Matches(0,2,3,4),"null return does not pair");
    Check(!r.Matches(1,0,3,4),"missing form identity does not pair");
    Check(!r.Matches(2,2,3,4),"different returned object does not pair");
    Check(!r.Matches(1,9,3,4),"same address new form identity does not pair");
    Check(!r.Matches(1,2,9,4),"wrong source does not pair");
    Check(!r.Matches(1,2,3,9),"wrong weapon does not pair");
    r.Destroy(8);
    Check(r.Matches(1,2,3,4),"unrelated destroy preserves receipt");
    r.Destroy(1);
    Check(!r.Matches(1,2,3,4),"destroy inside call prevents pairing");
    r={}; r.Create(1,2,3,4); r.Create(1,2,3,4);
    Check(!r.Matches(1,2,3,4),"duplicate create fails closed");
    Receipt parent{}, child{};
    parent.Create(1,2,3,4); child.Create(10,20,30,40);
    Check(parent.Matches(1,2,3,4) && child.Matches(10,20,30,40),"separate nested receipts");
    parent.Create(10,20,30,40);
    Check(!parent.Matches(1,2,3,4),"unscoped nested create makes parent ambiguous");
    r={}; r.creates=(std::numeric_limits<unsigned>::max)(); r.Create(1,2,3,4);
    Check(r.creates==(std::numeric_limits<unsigned>::max)() && !r.Matches(1,2,3,4),"creation count cannot wrap to valid");
    std::printf("PASS %u checks; x86 ABI/receipt fixture only, no game or DLL execution.\n",checks);
}

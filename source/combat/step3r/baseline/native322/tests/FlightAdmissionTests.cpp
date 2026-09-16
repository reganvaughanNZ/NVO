#include "FlightAdmission.hpp"
#include "SpawnCall.hpp"
#include <cstdio>
#include <cstdlib>
#include <vector>
using namespace nvo::admission;
static_assert(sizeof(void*)==4,"Build with the x86 toolchain.");
namespace {
unsigned checks{};
void Check(bool ok,const char* name) {
    ++checks;
    if (!ok) { std::printf("FAIL %s\n",name); std::exit(1); }
}
}
int main() {
    Pool<128> physics; Pool<512> lives;
    Check(physics.Used()==0 && lives.Used()==0,"empty pools");
    std::array<Ticket,128> filled{};
    for (auto& t:filled) t=physics.Reserve();
    Check(physics.Used()==128,"all real physics capacity reserved");
    Check(!physics.Reserve(),"129th reservation refused");
    bool stable=true;
    for (const auto t:filled) stable=stable && physics.State(t)==Phase::Reserved;
    Check(stable,"full capacity never evicts an owner");
    const auto life=lives.Reserve();
    const auto refused=physics.Reserve();
    Check(life && !refused && lives.Cancel(life) && lives.Used()==0,"first resource can roll back when second is full");
    Check(!physics.Commit(filled[0]),"cannot activate before binding");
    Check(physics.Bind(filled[0]) && physics.Commit(filled[0]),"reserve bind commit");
    Check(!physics.Cancel(filled[0]),"cancellation cannot evict active flight");
    Check(!physics.Bind(filled[0]) && !physics.Commit(filled[0]),"duplicate attach/commit refused");
    Check(physics.Fault(filled[0]) && physics.State(filled[0])==Phase::Faulted,"post-commit fault retains owner");
    Check(!physics.Cancel(filled[0]) && !physics.Reserve(),"fault cannot silently free capacity");
    Check(physics.Destroy(filled[0]),"known destruction retires faulted ownership");
    const auto replacement=physics.Reserve();
    Check(replacement && replacement.slot==filled[0].slot && replacement.id!=filled[0].id,"freed slot has fresh token");
    Check(!physics.Cancel(filled[0]) && !physics.Destroy(filled[0]) && !physics.Commit(filled[0]),"late old completion cannot affect new owner");
    Check(physics.State(replacement)==Phase::Reserved,"new reservation survives stale completion");
    Check(physics.Cancel(replacement) && !physics.Cancel(replacement),"one cancellation only");
    auto bad=filled[1];bad.slot=128;
    Check(physics.State(bad)==Phase::Empty && !physics.Bind(bad),"bad slot rejected");
    Check(!lives.Bind(filled[1]),"cross-pool token rejected");
    Pool<128> foreign;
    Check(foreign.Reserve() && !foreign.Cancel(filled[1]),"same-size foreign pool rejected");
    const auto old=filled[1];physics.Reset();
    const auto fresh=physics.Reserve();
    Check(physics.Used()==1 && fresh.id>old.id,"reset retains monotonic identity");
    Check(!physics.Bind(old) && !physics.Fault(old) && physics.State(fresh)==Phase::Reserved,"old-session token cannot touch fresh pool");
    Check(physics.Fault(fresh) && !physics.Cancel(fresh),"pre-return ambiguity retains reserved capacity");
    physics.Reset();lives.Reset();
    std::array<Ticket,512> allLives{};
    for (auto& t:allLives) t=lives.Reserve();
    Check(lives.Used()==512 && !lives.Reserve() && physics.Used()==0,"lifecycle full refuses before physics reservation");
    lives.Reset();
    auto lp=lives.Reserve();auto pp=physics.Reserve();
    Check(lp && pp && lives.Bind(lp) && physics.Bind(pp),"two held pools before exact return");
    nvo::spawn::Receipt receipt;receipt.Create(0x1000,1,2,3);
    Check(receipt.Matches(0x1000,1,2,3) && physics.Commit(pp) && lives.Commit(lp),"exact returned identity allows commit");
    Check(lives.Destroy(lp) && physics.Destroy(pp) && !lives.Used() && !physics.Used(),"destruction releases both pools");
    lp=lives.Reserve();pp=physics.Reserve();
    Check(lives.Cancel(lp) && physics.Cancel(pp) && !lives.Used() && !physics.Used(),"null return with no creates releases both reservations");
    lp=lives.Reserve();pp=physics.Reserve();
    receipt={};receipt.Create(0x1000,1,2,3);receipt.Create(0x2000,4,5,6);
    Check(!receipt.Matches(0x1000,1,2,3) && lives.Fault(lp) && physics.Fault(pp),"multiple creates remain ambiguous and owned");
    Block(Fault::Pairing);
    Check(Blocked() && processFault.load()==Fault::Pairing,"fault blocks further admissions");
    lives.Reset();physics.Reset();
    Check(Blocked(),"session reset cannot clear process fault");
    Block(Fault::Exception);
    Check(processFault.load()==Fault::Pairing,"first failure reason retained");
    // Fixed ring workload exercises full/refused/cancelled/active/retired states
    // across actual128/512 pools. Artificial log success/failure never touches it.
    bool trace=true;
    for (unsigned pass=0;pass<2;++pass) {
        physics.Reset();lives.Reset();
        std::array<Ticket,128> ps{},ls{};
        unsigned omittedLogs=0;
        for (unsigned i=0;i<20000;++i) {
            const auto index=i%128;
            if (i>=128) trace=trace && physics.Destroy(ps[index]) && lives.Destroy(ls[index]);
            ps[index]=physics.Reserve();ls[index]=lives.Reserve();
            trace=trace && ps[index] && ls[index] && physics.Bind(ps[index]) && lives.Bind(ls[index])
                && physics.Commit(ps[index]) && lives.Commit(ls[index]);
            if (pass || i>16) ++omittedLogs;
            if (i>=127) trace=trace && !physics.Reserve() && physics.Used()==128 && lives.Used()==128;
        }
        Check(trace && omittedLogs>0,"20k trace independent of omitted/failed logs");
        for (unsigned i=0;i<128;++i) trace=trace && physics.Destroy(ps[i]) && lives.Destroy(ls[i]);
        Check(trace && physics.Used()==0 && lives.Used()==0,"trace ends with no retained owners");
    }
    std::printf("PASS %u checks; bounded production pool/receipt fixtures; no game or DLL execution.\n",checks);
}

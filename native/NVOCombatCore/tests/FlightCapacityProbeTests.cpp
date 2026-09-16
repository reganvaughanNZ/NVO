#include "FlightCapacityProbe.hpp"
#include <cstdio>
#include <cstdlib>
using namespace nvo::admission;
static_assert(sizeof(void*)==4);
namespace {
unsigned checks{};
void Check(bool ok,const char* what) {
    ++checks; if (!ok) { std::printf("FAIL %s\n",what); std::exit(1); }
}
}
int main() {
    Pool<128> pool;
    CapacityProbe<128> probe;
    Check(probe.Arm(pool) && probe.Held()==127 && pool.Used()==127,"arm real pool with127 inert reservations");
    Check(probe.Consumed() && !probe.Arm(pool),"cannot arm twice");
    const auto active=pool.Reserve(); probe.Note(active);
    Check(active && pool.Bind(active) && pool.Commit(active) && pool.Used()==128,"real flight commits into final slot");
    Check(!pool.Reserve() && pool.State(active)==Phase::Active,"real full-pool refusal preserves flight");
    const auto r=probe.Release(pool);
    Check(r.ok && r.held==127 && r.released==127 && r.before==128 && r.after==1,"only synthetic reservations released");
    Check(r.survivor.id==active.id && r.survivorBefore==Phase::Active && r.survivorAfter==Phase::Active,"same active owner survives release");
    Check(!probe.Held() && probe.Attempts()==1,"probe disarmed after one release");
    std::array<Ticket,127> next{};
    for (auto& t:next) t=pool.Reserve();
    Check(next.back() && pool.Used()==128 && !pool.Reserve(),"all127 released slots reusable alongside survivor");
    const auto again=probe.Release(pool);
    Check(again.ok && again.released==0 && pool.Used()==128,"double release cannot evict new occupants");
    for (const auto t:next) pool.Cancel(t);
    Check(pool.Destroy(active) && pool.Used()==0,"real flight retires normally");
    pool.Reset();
    Check(!probe.Arm(pool),"reload never rearms consumed probe");

    CapacityProbe<128> deferred;
    auto prior=pool.Reserve();pool.Bind(prior);pool.Commit(prior);
    Check(!deferred.Arm(pool) && !deferred.Consumed() && pool.State(prior)==Phase::Active,"existing flight prevents arming without consuming attempt");
    pool.Destroy(prior);
    Check(deferred.Arm(pool),"can arm after prior flight retires");
    auto flight=pool.Reserve();deferred.Note(flight);pool.Bind(flight);pool.Commit(flight);pool.Destroy(flight);
    Check(pool.Used()==127 && deferred.Held()==127,"inert reservations survive early real retirement");
    flight=pool.Reserve();deferred.Note(flight);pool.Bind(flight);pool.Commit(flight);
    const auto second=deferred.Release(pool);
    Check(second.ok && second.survivor.id==flight.id && second.survivorAfter==Phase::Active,"latest actual owner is checked after slot reuse");
    pool.Reset();

    CapacityProbe<128> cancelled;
    Check(cancelled.Arm(pool),"cancellation scenario arms");
    const auto abort=cancelled.Release(pool);
    Check(abort.ok && abort.after==0 && !cancelled.Arm(pool),"session cancellation releases all and stays consumed");
    pool.Reset();
    CapacityProbe<128> stale;
    stale.Arm(pool);pool.Reset();auto fresh=pool.Reserve();
    const auto late=stale.Release(pool);
    Check(!late.ok && late.released==0 && pool.State(fresh)==Phase::Reserved,"unexpected stale reset fails without cancelling fresh owner");
    std::printf("PASS %u checks; real pool capacity-probe ownership; no game or DLL execution.\n",checks);
}

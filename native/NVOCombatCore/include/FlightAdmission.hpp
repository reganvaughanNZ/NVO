#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <limits>

namespace nvo::admission {
using U64=unsigned long long;
struct Ticket { U64 id{}; unsigned slot{}; std::uintptr_t owner{}; explicit operator bool() const noexcept { return id!=0; } };
enum class Phase : unsigned char { Empty, Reserved, Bound, Active, Faulted };
// No allocation/eviction, no dependency on diagnostic limits. Callers serialize
// access. IDs survive Reset so a completion from an old session cannot release
// a new occupant. Exhaustion refuses admission instead of wrapping identity.
template<unsigned Capacity> class Pool {
    struct Entry { U64 id{}; Phase phase{}; };
    std::array<Entry,Capacity> entries_{};
    U64 next_{};
public:
    Pool()=default;
    Pool(const Pool&)=delete;
    Pool& operator=(const Pool&)=delete;
    Ticket Reserve() noexcept {
        if (next_==(std::numeric_limits<U64>::max)()) return {};
        for (unsigned i=0;i<Capacity;++i) if (!entries_[i].id) {
            entries_[i]={++next_,Phase::Reserved}; return {next_,i,reinterpret_cast<std::uintptr_t>(this)};
        }
        return {};
    }
    Phase State(Ticket t) const noexcept {
        return t && t.owner==reinterpret_cast<std::uintptr_t>(this) && t.slot<Capacity
            && entries_[t.slot].id==t.id ? entries_[t.slot].phase : Phase::Empty;
    }
    bool Bind(Ticket t) noexcept {
        if (State(t)!=Phase::Reserved) return false;
        entries_[t.slot].phase=Phase::Bound; return true;
    }
    bool Commit(Ticket t) noexcept {
        if (State(t)!=Phase::Bound) return false;
        entries_[t.slot].phase=Phase::Active; return true;
    }
    bool Cancel(Ticket t) noexcept {
        if (State(t)!=Phase::Reserved) return false;
        entries_[t.slot]={}; return true;
    }
    bool Destroy(Ticket t) noexcept {
        const auto s=State(t);
        if (s!=Phase::Bound && s!=Phase::Active && s!=Phase::Faulted) return false;
        entries_[t.slot]={}; return true;
    }
    bool Fault(Ticket t) noexcept {
        if (State(t)==Phase::Empty) return false;
        entries_[t.slot].phase=Phase::Faulted; return true;
    }
    void Reset() noexcept { for (auto& e:entries_) e={}; }
    unsigned Used() const noexcept { unsigned n=0; for (const auto& e:entries_) if(e.id) ++n; return n; }
};
enum class Fault : unsigned { None, Physics, Pairing, Binding, Exception, StaleSession, Lifetime, UnexpectedMovement };
inline std::atomic<Fault> processFault{Fault::None};
static_assert(std::atomic<Fault>::is_always_lock_free);
inline void Block(Fault reason) noexcept {
    auto expected=Fault::None;
    processFault.compare_exchange_strong(expected,reason,std::memory_order_acq_rel);
}
inline bool Blocked() noexcept { return processFault.load(std::memory_order_acquire)!=Fault::None; }
// A process fault intentionally survives new-game/reload/menu transitions.
// No health/flight repair is implied. Only a process restart resets this latch.
struct Profile {
    void* actor{}; void* weaponPointer{}; void* projectile{};
    std::uint32_t source{},weapon{},ammo{},base{},original{};
    unsigned index{},dragModel{}; double bc{};
    bool changesBase{};
};
struct Reservation {
    Ticket life{},physics{};
    U64 serial{}; unsigned session{};
    Profile profile{};
    explicit operator bool() const noexcept { return life && physics && serial; }
};
}

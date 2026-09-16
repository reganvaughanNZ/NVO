#pragma once
#include "FlightAdmission.hpp"

namespace nvo::admission {
// Test-only inert reservations in the real pool. No fake game objects or
// capacity override. Calls are serialized by the existing physics lock.
template<unsigned Capacity> class CapacityProbe {
    static_assert(Capacity > 1);
    std::array<Ticket,Capacity-1> held_{};
    Ticket latest_{};
    bool consumed_{};
    unsigned attempts_{};
public:
    struct ReleaseResult {
        unsigned held{},released{},before{},after{};
        Ticket survivor{};
        Phase survivorBefore{Phase::Empty},survivorAfter{Phase::Empty};
        bool ok{};
    };
    bool Consumed() const noexcept { return consumed_; }
    unsigned Attempts() const noexcept { return attempts_; }
    unsigned Held() const noexcept {
        unsigned n=0; for (const auto t:held_) if(t) ++n; return n;
    }
    bool Arm(Pool<Capacity>& pool) noexcept {
        if (consumed_ || pool.Used()) return false;
        consumed_=true;
        for (auto& t:held_) {
            t=pool.Reserve();
            if (!t) { Release(pool); return false; }
        }
        return true;
    }
    void Note(Ticket actual) noexcept {
        if (Held() && actual) { latest_=actual; ++attempts_; }
    }
    ReleaseResult Release(Pool<Capacity>& pool) noexcept {
        ReleaseResult r{};
        r.held=Held(); r.before=pool.Used(); r.survivor=latest_;
        r.survivorBefore=pool.State(latest_);
        for (auto& t:held_) if (t && pool.Cancel(t)) { t={}; ++r.released; }
        r.after=pool.Used(); r.survivorAfter=pool.State(latest_);
        r.ok=r.released==r.held && r.before>=r.released
            && r.after==r.before-r.released && r.survivorBefore==r.survivorAfter;
        return r;
    }
};
}

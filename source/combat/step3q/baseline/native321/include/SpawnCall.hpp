#pragma once
#include <array>
#include <cstdint>
#include <limits>

// The inspected provider calls a cdecl function with sixteen 32-bit stack
// words. Preserve float bits and the full padded char slots without conversion.
namespace nvo::spawn {
using Word = std::uint32_t;
using Arguments = std::array<Word, 16>;
using Function = void* (__cdecl*)(Word, Word, Word, Word, Word, Word, Word, Word,
    Word, Word, Word, Word, Word, Word, Word, Word);
inline void* Forward(Function fn, const Arguments& a) {
    return fn(a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7],
        a[8], a[9], a[10], a[11], a[12], a[13], a[14], a[15]);
}
struct Receipt {
    std::uintptr_t created{};
    Word ref{}, source{}, weapon{};
    unsigned creates{}, destroys{};
    void Create(std::uintptr_t p, Word id, Word s, Word w) noexcept {
        if (!creates) { created=p; ref=id; source=s; weapon=w; }
        if (creates != (std::numeric_limits<unsigned>::max)()) ++creates;
    }
    void Destroy(std::uintptr_t p) noexcept {
        if (p && p==created && destroys != (std::numeric_limits<unsigned>::max)()) ++destroys;
    }
    bool Matches(std::uintptr_t returned, Word id, Word s, Word w) const noexcept {
        return returned && id && creates==1 && !destroys && returned==created
            && id==ref && source==s && weapon==w;
    }
};
}

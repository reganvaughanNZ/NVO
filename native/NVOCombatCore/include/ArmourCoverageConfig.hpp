#pragma once
#include "CoverageProfiles.hpp"
#include <array>
#include <string_view>

namespace nvo::armour::config {
constexpr std::size_t kMaxBytes=131072;
class Registry {
public:
    Registry()=default;
    Registry(const Registry&)=delete;
    Registry& operator=(const Registry&)=delete;
    bool Load(std::string_view text) noexcept;
    void Reset() noexcept { catalog_.Reset(); count_=0; error_="not_loaded"; }
    const coverage::PreparedCatalog& Catalog() const noexcept { return catalog_; }
    const char* Error() const noexcept { return error_; }
private:
    struct Owned { char plugin[129]{}; coverage::Profile profile{}; };
    std::array<Owned,coverage::kMaxProfiles> rows_{};
    std::size_t count_{};
    const char* error_{"not_loaded"};
    coverage::PreparedCatalog catalog_;
    bool Fail(const char* reason) noexcept { Reset(); error_=reason; return false; }
};
}

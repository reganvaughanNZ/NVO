#include "ImpactBinding.hpp"
#include <cstdio>
#include <initializer_list>
#include <string>

// Independently authored, wholly synthetic evidence. Reserved producer values
// exercise the offline contract only; no current runtime provider is certified.
namespace {
namespace b = nvo::binding;
namespace s = nvo::shadow;
namespace m = nvo::model;
unsigned checks{}, failures{};
struct Fixture {
    s::IdentityEvidence identity{12, 16, 17, 18, 21, 22, 23, 24, 25, true, true};
    s::ModeEvidence mode{m::Mode::RealTime, true};
    int region{42};
    b::Evidence evidence;
};
Fixture Ready() {
    Fixture f;
    f.evidence.expected = {11, 12, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25, 42, m::Mode::RealTime};
    f.evidence.contact = f.evidence.snapshot = f.evidence.expected;
    f.evidence.contactProducer = b::ContactProducer::VerifiedExactContact;
    f.evidence.snapshotProducer = b::SnapshotProducer::VerifiedAtImpact;
    f.evidence.exactCopyScopeVerified = f.evidence.contactPositionAssociated = true;
    return f;
}
void Expect(const Fixture& f, b::Reason reason, const std::string& name) {
    ++checks;
    const auto result = b::Validate(f.identity, f.mode, f.region, f.evidence);
    if (result.ready != (reason == b::Reason::None) || result.reason != reason) {
        ++failures;
        std::printf("FAIL %s: ready=%u reason=%s expected=%s\n", name.c_str(),
            static_cast<unsigned>(result.ready), b::ReasonName(result.reason), b::ReasonName(reason));
    }
}
struct StampEdit { const char* name; void (*different)(b::Stamp&); void (*missing)(b::Stamp&); };
const StampEdit stampEdits[] = {
    {"generation", [](b::Stamp& x) { ++x.generation; }, [](b::Stamp& x) { x.generation = 0; }},
    {"session", [](b::Stamp& x) { ++x.session; }, [](b::Stamp& x) { x.session = 0; }},
    {"transaction", [](b::Stamp& x) { ++x.transaction; }, [](b::Stamp& x) { x.transaction = 0; }},
    {"copy ordinal", [](b::Stamp& x) { ++x.copyOrdinal; }, [](b::Stamp& x) { x.copyOrdinal = 0; }},
    {"lifetime", [](b::Stamp& x) { ++x.lifetime; }, [](b::Stamp& x) { x.lifetime = 0; }},
    {"component", [](b::Stamp& x) { ++x.component; }, [](b::Stamp& x) { x.component = 0; }},
    {"application", [](b::Stamp& x) { ++x.application; }, [](b::Stamp& x) { x.application = 0; }},
    {"profile", [](b::Stamp& x) { ++x.profile; }, [](b::Stamp& x) { x.profile = 0; }},
    {"source", [](b::Stamp& x) { ++x.source; }, [](b::Stamp& x) { x.source = 0; }},
    {"target", [](b::Stamp& x) { ++x.target; }, [](b::Stamp& x) { x.target = 0; }},
    {"carrier", [](b::Stamp& x) { ++x.carrier; }, [](b::Stamp& x) { x.carrier = 0; }},
    {"weapon", [](b::Stamp& x) { ++x.weapon; }, [](b::Stamp& x) { x.weapon = 0; }},
    {"ammo", [](b::Stamp& x) { ++x.ammo; }, [](b::Stamp& x) { x.ammo = 0; }},
    {"region", [](b::Stamp& x) { ++x.region; }, [](b::Stamp& x) { x.region = -1; }},
    {"mode", [](b::Stamp& x) { x.mode = m::Mode::Vats; }, [](b::Stamp& x) { x.mode = m::Mode::Unknown; }}
};
struct ConsumerEdit { const char* name; void (*edit)(Fixture&); };
const ConsumerEdit consumerEdits[] = {
    {"session", [](Fixture& f) { ++f.identity.session; }},
    {"component", [](Fixture& f) { ++f.identity.component; }},
    {"application", [](Fixture& f) { ++f.identity.application; }},
    {"profile", [](Fixture& f) { ++f.identity.profile; }},
    {"source", [](Fixture& f) { ++f.identity.source; }},
    {"target", [](Fixture& f) { ++f.identity.target; }},
    {"carrier", [](Fixture& f) { ++f.identity.carrier; }},
    {"weapon", [](Fixture& f) { ++f.identity.weapon; }},
    {"ammo", [](Fixture& f) { ++f.identity.ammo; }},
    {"region", [](Fixture& f) { ++f.region; }},
    {"mode", [](Fixture& f) { f.mode.value = m::Mode::Vats; }}
};
} // namespace

int main() {
    static_assert(sizeof(void*) == 4, "Use the x86 standalone runner");
    static_assert(!b::kGameplayWrites && !b::kRuntimeIntegrated);
    Expect(Ready(), b::Reason::None, "matched synthetic evidence qualifies offline only");
    for (const auto& edit : stampEdits) {
        auto f = Ready(); edit.different(f.evidence.contact);
        Expect(f, b::Reason::ContactScopeMismatch, std::string("independent contact ") + edit.name);
        f = Ready(); edit.different(f.evidence.snapshot);
        Expect(f, b::Reason::SnapshotScopeMismatch, std::string("independent snapshot ") + edit.name);
        f = Ready(); edit.missing(f.evidence.expected);
        Expect(f, b::Reason::ExpectedScopeMissing, std::string("missing expected ") + edit.name);
    }
    for (const auto& edit : consumerEdits) {
        auto f = Ready(); edit.edit(f);
        Expect(f, b::Reason::ExpectedIdentityMismatch, std::string("consumer changed ") + edit.name);
    }
    auto f = Ready(); f.evidence.expected = {};
    Expect(f, b::Reason::ExpectedScopeMissing, "absent consumer stamp");
    f = Ready(); f.evidence.contact = {};
    Expect(f, b::Reason::ContactScopeMissing, "absent contact stamp");
    f = Ready(); f.evidence.snapshot = {};
    Expect(f, b::Reason::SnapshotScopeMissing, "absent snapshot stamp");
    for (const auto producer : {b::ContactProducer::Unknown, b::ContactProducer::OwnedStepInterval,
         b::ContactProducer::EngineSegmentMean, b::ContactProducer::PointModelEstimate,
         b::ContactProducer::MuzzleEstimate, static_cast<b::ContactProducer>(255)}) {
        f = Ready(); f.evidence.contactProducer = producer;
        Expect(f, b::Reason::ContactProducerUnqualified,
            "unqualified contact producer " + std::to_string(static_cast<unsigned>(producer)));
    }
    for (const auto producer : {b::SnapshotProducer::Unknown, b::SnapshotProducer::StableCopyInput,
         static_cast<b::SnapshotProducer>(255)}) {
        f = Ready(); f.evidence.snapshotProducer = producer;
        Expect(f, b::Reason::SnapshotProducerUnqualified,
            "unqualified snapshot producer " + std::to_string(static_cast<unsigned>(producer)));
    }
    f = Ready(); f.evidence.exactCopyScopeVerified = false;
    Expect(f, b::Reason::CopyScopeUnverified, "matching stamps do not prove exact copy scope");
    f = Ready(); f.evidence.contactPositionAssociated = false;
    Expect(f, b::Reason::ContactPositionUnverified, "matching stamps do not prove contact position association");
    f = Ready(); ++f.evidence.contact.copyOrdinal; ++f.evidence.snapshot.copyOrdinal;
    Expect(f, b::Reason::ContactScopeMismatch, "same target and agreeing cached producers from different copy");
    f = Ready(); ++f.evidence.contact.application; ++f.evidence.snapshot.application;
    Expect(f, b::Reason::ContactScopeMismatch, "same target and agreeing cached producers from different application");
    f = Ready(); f.evidence.contact.mode = static_cast<m::Mode>(255);
    Expect(f, b::Reason::ContactScopeMissing, "invalid contact mode cannot qualify");
    f = Ready(); f.evidence.snapshot.region = 256;
    Expect(f, b::Reason::SnapshotScopeMissing, "out of range snapshot region cannot qualify");
    for (const int region : {0, 255}) {
        f = Ready(); f.region = region;
        f.evidence.expected.region = f.evidence.contact.region = f.evidence.snapshot.region = region;
        Expect(f, b::Reason::None, "supported literal region boundary " + std::to_string(region));
    }
    f = Ready(); f.mode.value = m::Mode::Vats;
    f.evidence.expected.mode = f.evidence.contact.mode = f.evidence.snapshot.mode = m::Mode::Vats;
    Expect(f, b::Reason::None, "matching VATS scope qualifies offline only");
    f = Ready(); f.evidence.contact.profile = 0;
    Expect(f, b::Reason::ContactScopeMissing, "partially missing contact identity");
    f = Ready(); f.evidence.snapshot.session = 0;
    Expect(f, b::Reason::SnapshotScopeMissing, "partially missing snapshot identity");
    std::printf("RESULT checks=%u failures=%u suite=impact_binding\n", checks, failures);
    return failures ? 1 : 0;
}

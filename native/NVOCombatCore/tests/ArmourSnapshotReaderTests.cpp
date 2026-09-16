#include "ArmourSnapshotReader.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <vector>

using nvo::armour::reader::Code;
using nvo::armour::reader::Memory;
using nvo::armour::reader::Snapshot;
using U8 = std::uint8_t;
using U16 = std::uint16_t;
using U32 = std::uint32_t;

namespace {
constexpr auto kVtable = static_cast<std::uintptr_t>(0x101000u);
constexpr U32 kActorId = 0xFF001234u;
unsigned gChecks{};

struct Form { void* vt; U8 type; U8 pad[3]; U32 flags; U32 id; };
struct Extra { void* vt; U8 type; U8 pad[3]; Extra* next; };
struct Xcc { Extra base; void* data; };
struct HealthExtra { Extra base; float health; };
struct ExtraList { void* vt; Extra* head; U8 presence[0x13]; U8 after; void* tail; };
struct Container { void* list; void* owner; };
struct Node { void* data; Node* next; };
struct Entry { Node* extend; std::int32_t count; void* form; };

static_assert(sizeof(Form) == 0x10 && sizeof(Extra) == 0x0C);
static_assert(sizeof(Xcc) == 0x10 && sizeof(HealthExtra) == 0x10);
static_assert(sizeof(ExtraList) == 0x20 && sizeof(Node) == 8 && sizeof(Entry) == 0x0C);

void Check(bool ok, const char* name)
{
    ++gChecks;
    if (!ok) { std::printf("FAIL %s\n", name); std::exit(1); }
}

void Presence(ExtraList& list, U8 type, bool present = true)
{
    const U8 bit = static_cast<U8>(1u << (type & 7));
    if (present) list.presence[type >> 3] |= bit;
    else list.presence[type >> 3] &= static_cast<U8>(~bit);
}

template <class T, std::size_t N>
void Put(unsigned char (&bytes)[N], std::size_t offset, const T& value)
{
    Check(offset + sizeof(value) <= N, "fixture write stays in bounds");
    std::memcpy(bytes + offset, &value, sizeof(value));
}

struct ReadContext {
    unsigned calls{};
    unsigned failAt{};
    const void* mutateAddress{};
    void* mutateLocation{};
    const void* mutateValue{};
    std::size_t mutateSize{};
    unsigned mutateAtOccurrence{};
    unsigned mutateOccurrences{};
};

bool ReadMemory(void* opaque, const void* source, void* destination, std::size_t size) noexcept
{
    auto& context = *static_cast<ReadContext*>(opaque);
    ++context.calls;
    if (context.failAt && context.calls == context.failAt) return false;
    if (source == context.mutateAddress) {
        ++context.mutateOccurrences;
        if (context.mutateLocation && context.mutateValue && context.mutateSize
            && context.mutateOccurrences == context.mutateAtOccurrence)
            std::memcpy(context.mutateLocation, context.mutateValue, context.mutateSize);
    }
    std::memcpy(destination, source, size);
    return true;
}

struct Fixture {
    alignas(4) unsigned char actor[0x100]{};
    alignas(4) unsigned char armour[0x190]{};
    Xcc xcc{};
    Container container{};
    Node entryHead{};
    Entry entry{};
    Node instanceHead{};
    ExtraList instance{};
    Extra worn{};
    HealthExtra health{};

    Fixture() { Reset(false, 100.0f); }

    void Reset(bool explicitHealth, float healthValue)
    {
        std::memset(this, 0, sizeof(*this));
        Form actorForm{reinterpret_cast<void*>(kVtable), 0x3B, {}, 0, kActorId};
        std::memcpy(actor, &actorForm, sizeof(actorForm));
        auto& actorExtras = *reinterpret_cast<ExtraList*>(actor + 0x44);
        actorExtras.vt = reinterpret_cast<void*>(kVtable);
        actorExtras.head = &xcc.base;
        Presence(actorExtras, 0x15);

        xcc.base = {reinterpret_cast<void*>(kVtable), 0x15, {}, nullptr};
        xcc.data = &container;
        container = {&entryHead, actor};
        entryHead = {&entry, nullptr};
        entry = {&instanceHead, 1, armour};
        instanceHead = {&instance, nullptr};
        instance.vt = reinterpret_cast<void*>(kVtable);
        instance.head = &worn;
        Presence(instance, 0x16);
        worn = {reinterpret_cast<void*>(kVtable), 0x16, {}, nullptr};
        health.base = {reinterpret_cast<void*>(kVtable), 0x25, {}, nullptr};
        health.health = healthValue;
        if (explicitHealth) {
            worn.next = &health.base;
            Presence(instance, 0x25);
        }

        Form armourForm{reinterpret_cast<void*>(kVtable), 0x18, {}, 0, 0x000A1001u};
        std::memcpy(armour, &armourForm, sizeof(armourForm));
        const U32 baseHealth = 100, partMask = 4;
        const U32 bipedFlags = 0xA5B6C7D8u;
        const U8 armourFlags = 1;
        const U16 rating = 25;
        const float threshold = 8.0f;
        Put(armour, 0x6C, baseHealth); Put(armour, 0x74, partMask);
        Put(armour, 0x78, bipedFlags); Put(armour, 0x178, rating);
        Put(armour, 0x17C, threshold); Put(armour, 0x180, armourFlags);
    }

    ExtraList& ActorExtras() { return *reinterpret_cast<ExtraList*>(actor + 0x44); }
};

Snapshot Run(Fixture& fixture, ReadContext& context)
{
    const Memory memory{&context, ReadMemory};
    return nvo::armour::reader::CaptureStable(memory, fixture.actor, kActorId);
}

void ExpectRejected(const Snapshot& result, Code code, const char* name)
{
    Check(result.code == code, name);
    Check(!result.enumerationComplete && !result.stableDoubleRead && result.itemCount == 0,
        "rejection publishes no partial armour");
    Check(!result.regionCoverageComplete && !result.layerOrderVerified
        && !result.impactSnapshotVerified && !result.bareRegionVerified,
        "rejection publishes no Step 4A authority");
}
} // namespace

int main()
{
    static_assert(!nvo::armour::reader::kGameplayWrites);
    static_assert(!nvo::armour::reader::kSnapshotAuthority);
    static_assert(!nvo::armour::reader::kCallsShadowAdapter);

    Fixture f;
    ReadContext read{};
    unsigned char pristine[sizeof(Fixture)]{};
    std::memcpy(pristine, &f, sizeof(f));
    auto result = Run(f, read);
    Check(result.code == Code::CompleteWithArmour && result.itemCount == 1,
        "one implicit-full worn armour captured");
    Check(result.stableDoubleRead && result.enumerationComplete,
        "success requires stable double traversal");
    const auto expectedToken = (static_cast<std::uint64_t>(kActorId) << 32)
        | static_cast<U32>(reinterpret_cast<std::uintptr_t>(&f.instance));
    Check(result.targetId == kActorId && result.items[0].instanceToken == expectedToken,
        "target and exact instance identity preserved");
    Check(result.items[0].formId == 0x000A1001u && result.items[0].partMask == 4
        && result.items[0].bipedFlags == 0xA5B6C7D8u
        && result.items[0].armourRating == 25 && result.items[0].damageThreshold == 8.0f
        && result.items[0].armourFlags == 1,
        "every raw armour record field preserved");
    Check(result.items[0].baseHealth == 100 && result.items[0].currentHealth == 100.0f
        && result.items[0].conditionRatio == 1.0f && !result.items[0].explicitHealth,
        "missing ExtraHealth means raw full base health");
    Check(!result.regionCoverageComplete && !result.layerOrderVerified
        && !result.impactSnapshotVerified && !result.bareRegionVerified,
        "raw success does not claim semantic armour authority");
    Check(std::memcmp(pristine, &f, sizeof(f)) == 0,
        "successful capture does not modify source memory");

    f.Reset(true, 35.0f); read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteWithArmour && result.items[0].explicitHealth
        && result.items[0].currentHealth == 35.0f && result.items[0].conditionRatio == 0.35f,
        "exact damaged instance health preserved");
    f.Reset(true, 0.0f); read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteWithArmour && result.items[0].currentHealth == 0.0f,
        "broken worn armour is retained");

    f.Reset(false, 0); alignas(4) unsigned char helmet[0x190]{};
    std::memcpy(helmet, f.armour, sizeof(helmet));
    reinterpret_cast<Form*>(helmet)->id = 0x000A1002u;
    const U32 headMask = 1; Put(helmet, 0x74, headMask);
    Node secondEntryNode{}, secondInstanceNode{}; Entry secondEntry{};
    ExtraList secondInstance{}; Extra secondItemWorn{};
    f.entryHead.next = &secondEntryNode; secondEntryNode.data = &secondEntry;
    secondEntry = {&secondInstanceNode, 1, helmet};
    secondInstanceNode.data = &secondInstance;
    secondInstance.vt = reinterpret_cast<void*>(kVtable);
    secondInstance.head = &secondItemWorn; Presence(secondInstance, 0x16);
    secondItemWorn = {reinterpret_cast<void*>(kVtable), 0x16, {}, nullptr};
    read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteWithArmour && result.itemCount == 2
        && result.items[0].instanceToken != result.items[1].instanceToken,
        "body and helmet keep distinct exact-instance identities");
    Check(!result.layerOrderVerified && !result.regionCoverageComplete,
        "two raw equip masks do not invent layer or anatomy semantics");

    f.Reset(false, 0); secondEntryNode = {}; secondInstanceNode = {};
    secondEntry = {}; secondInstance = {}; secondItemWorn = {};
    f.entryHead.next = &secondEntryNode; secondEntryNode.data = &secondEntry;
    secondEntry = {&secondInstanceNode, 1, f.armour};
    secondInstanceNode.data = &secondInstance;
    secondInstance.vt = reinterpret_cast<void*>(kVtable);
    secondInstance.head = &secondItemWorn; Presence(secondInstance, 0x16);
    secondItemWorn = {reinterpret_cast<void*>(kVtable), 0x16, {}, nullptr};
    read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteWithArmour && result.itemCount == 2
        && result.items[0].formId == result.items[1].formId
        && result.items[0].instanceToken != result.items[1].instanceToken,
        "same armour form on distinct instances is never coalesced by form ID");

    f.Reset(false, 0); f.entryHead = {nullptr, nullptr}; read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteNoArmourObserved && result.itemCount == 0
        && result.enumerationComplete && result.stableDoubleRead,
        "valid empty object list is complete raw telemetry");
    Check(!result.bareRegionVerified, "zero observed armour is not verified bare skin");

    f.Reset(false, 0); f.instance.head = nullptr; Presence(f.instance, 0x16, false);
    read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteNoArmourObserved && result.itemCount == 0
        && result.enumerationComplete && result.stableDoubleRead
        && !result.bareRegionVerified,
        "baked model without a Worn inventory instance is observed but never declared bare");

    f.Reset(false, 0); f.ActorExtras().head = nullptr; Presence(f.ActorExtras(), 0x15, false);
    read = {}; ExpectRejected(Run(f, read), Code::MissingContainerChanges,
        "missing container changes remains unavailable");
    f.Reset(false, 0); Presence(f.ActorExtras(), 0x15, false); read = {};
    ExpectRejected(Run(f, read), Code::PresenceMismatch,
        "actor presence mismatch rejects");
    f.Reset(false, 0); f.container.owner = f.armour; read = {};
    ExpectRejected(Run(f, read), Code::OwnerMismatch, "foreign container owner rejects");
    f.Reset(false, 0); f.container.list = nullptr; read = {};
    ExpectRejected(Run(f, read), Code::NullObjectList, "null object list is not empty");
    f.Reset(false, 0); f.xcc.data = reinterpret_cast<void*>(0xFFF0u); read = {};
    ExpectRejected(Run(f, read), Code::InvalidPointer,
        "low container-data pointer rejects before dereference");
    f.Reset(false, 0); f.entry.extend = reinterpret_cast<Node*>(0x10003u); read = {};
    ExpectRejected(Run(f, read), Code::InvalidPointer,
        "misaligned instance-list pointer rejects before dereference");

    f.Reset(false, 0); Xcc duplicate{};
    duplicate.base = {reinterpret_cast<void*>(kVtable), 0x15, {}, nullptr};
    duplicate.data = &f.container; f.xcc.base.next = &duplicate.base; read = {};
    ExpectRejected(Run(f, read), Code::DuplicateContainerChanges,
        "duplicate container changes rejects");
    f.Reset(false, 0); f.xcc.base.next = &f.xcc.base; read = {};
    ExpectRejected(Run(f, read), Code::CycleOrAlias, "actor-extra cycle rejects");
    f.Reset(false, 0); f.entryHead.next = &f.entryHead; read = {};
    ExpectRejected(Run(f, read), Code::CycleOrAlias, "entry cycle rejects");
    f.Reset(false, 0); f.instanceHead.next = &f.instanceHead; read = {};
    ExpectRejected(Run(f, read), Code::CycleOrAlias, "instance-node cycle rejects");
    f.Reset(false, 0); f.worn.next = &f.worn; read = {};
    ExpectRejected(Run(f, read), Code::CycleOrAlias, "instance-extra cycle rejects");

    f.Reset(false, 0); Extra secondWorn{reinterpret_cast<void*>(kVtable), 0x16, {}, nullptr};
    f.worn.next = &secondWorn; read = {};
    ExpectRejected(Run(f, read), Code::DuplicateWorn, "duplicate worn marker rejects");
    f.Reset(true, 50); HealthExtra secondHealth{};
    secondHealth.base = {reinterpret_cast<void*>(kVtable), 0x25, {}, nullptr};
    secondHealth.health = 40; f.health.base.next = &secondHealth.base; read = {};
    ExpectRejected(Run(f, read), Code::DuplicateHealth, "duplicate health rejects");
    f.Reset(true, 50); Presence(f.instance, 0x25, false); read = {};
    ExpectRejected(Run(f, read), Code::PresenceMismatch,
        "instance presence mismatch rejects");

    f.Reset(false, 0); reinterpret_cast<Form*>(f.armour)->type = 0x28; read = {};
    result = Run(f, read);
    Check(result.code == Code::CompleteNoArmourObserved && result.itemCount == 0,
        "verified equipped weapon is ignored");
    f.Reset(false, 0); reinterpret_cast<Form*>(f.armour)->type = 0x1F; read = {};
    ExpectRejected(Run(f, read), Code::UnsupportedWornForm,
        "unknown worn form does not disappear");
    f.Reset(false, 0); Presence(f.instance, 0x16, false); Presence(f.instance, 0x17);
    f.worn.type = 0x17; read = {};
    ExpectRejected(Run(f, read), Code::UnsupportedWornForm,
        "left-worn armour is unsupported rather than guessed");

    f.Reset(true, -1.0f); read = {};
    ExpectRejected(Run(f, read), Code::InvalidCondition, "negative condition rejects");
    f.Reset(true, 101.0f); read = {};
    ExpectRejected(Run(f, read), Code::InvalidCondition, "condition above base rejects");
    f.Reset(true, (std::numeric_limits<float>::quiet_NaN)()); read = {};
    ExpectRejected(Run(f, read), Code::InvalidCondition, "nonfinite condition rejects");
    f.Reset(false, 0); const U32 zero = 0; Put(f.armour, 0x6C, zero); read = {};
    ExpectRejected(Run(f, read), Code::InvalidArmourRecord, "zero base health rejects");
    f.Reset(false, 0); const U32 highMask = 0x80000004u; Put(f.armour, 0x74, highMask); read = {};
    ExpectRejected(Run(f, read), Code::InvalidArmourRecord, "unknown slot bits reject");
    f.Reset(false, 0); Put(f.armour, 0x74, zero); read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteWithArmour && result.items[0].partMask == 0
        && !result.regionCoverageComplete, "zero slot mask stays raw without coverage");
    f.Reset(false, 0); const float negativeDt = -1.0f; Put(f.armour, 0x17C, negativeDt); read = {};
    ExpectRejected(Run(f, read), Code::InvalidArmourRecord, "negative DT rejects");

    f.Reset(false, 0); Node aliasNode{&f.instance, nullptr}; f.instanceHead.next = &aliasNode; read = {};
    ExpectRejected(Run(f, read), Code::CycleOrAlias,
        "same exact instance reachable twice rejects");
    f.Reset(false, 0); ExtraList sharedExtraInstance{};
    Node sharedExtraInstanceNode{&sharedExtraInstance, nullptr};
    sharedExtraInstance.vt = reinterpret_cast<void*>(kVtable);
    sharedExtraInstance.head = &f.worn; Presence(sharedExtraInstance, 0x16);
    f.instanceHead.next = &sharedExtraInstanceNode; read = {};
    ExpectRejected(Run(f, read), Code::CycleOrAlias,
        "one extra node shared by distinct instances rejects");

    f.Reset(false, 0); std::vector<Extra> extras(65);
    for (auto& e : extras) e = {reinterpret_cast<void*>(kVtable), 1, {}, nullptr};
    extras[0].type = 0x16; Presence(f.instance, 0x16);
    for (std::size_t i = 0; i + 1 < 64; ++i) extras[i].next = &extras[i + 1];
    f.instance.head = &extras[0]; read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteWithArmour, "exact instance-extra cap succeeds");
    extras[63].next = &extras[64]; read = {};
    ExpectRejected(Run(f, read), Code::TraversalLimit,
        "instance-extra cap plus one rejects without truncation");

    f.Reset(false, 0);
    constexpr unsigned totalExtraInstances =
        nvo::armour::reader::kMaxTotalInstanceExtras
        / nvo::armour::reader::kMaxInstanceExtras;
    static_assert(totalExtraInstances * nvo::armour::reader::kMaxInstanceExtras
        == nvo::armour::reader::kMaxTotalInstanceExtras);
    std::vector<Node> totalExtraNodes(totalExtraInstances + 1);
    std::vector<ExtraList> totalExtraLists(totalExtraInstances + 1);
    std::vector<Extra> totalExtras(nvo::armour::reader::kMaxTotalInstanceExtras + 1);
    for (unsigned i = 0; i < totalExtraInstances; ++i) {
        totalExtraNodes[i].data = &totalExtraLists[i];
        totalExtraNodes[i].next = i + 1 < totalExtraInstances
            ? &totalExtraNodes[i + 1] : nullptr;
        totalExtraLists[i].vt = reinterpret_cast<void*>(kVtable);
        totalExtraLists[i].head =
            &totalExtras[i * nvo::armour::reader::kMaxInstanceExtras];
        for (unsigned j = 0; j < nvo::armour::reader::kMaxInstanceExtras; ++j) {
            const unsigned index = i * nvo::armour::reader::kMaxInstanceExtras + j;
            totalExtras[index] = {reinterpret_cast<void*>(kVtable), 1, {},
                j + 1 < nvo::armour::reader::kMaxInstanceExtras
                    ? &totalExtras[index + 1] : nullptr};
        }
    }
    f.entry.extend = &totalExtraNodes[0]; read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteNoArmourObserved
        && result.instancesVisited == totalExtraInstances
        && result.extrasVisited == nvo::armour::reader::kMaxTotalInstanceExtras,
        "exact total instance-extra cap succeeds without truncation");
    totalExtraNodes[totalExtraInstances - 1].next =
        &totalExtraNodes[totalExtraInstances];
    totalExtraNodes[totalExtraInstances].data = &totalExtraLists[totalExtraInstances];
    totalExtraLists[totalExtraInstances].vt = reinterpret_cast<void*>(kVtable);
    totalExtraLists[totalExtraInstances].head =
        &totalExtras[nvo::armour::reader::kMaxTotalInstanceExtras];
    totalExtras[nvo::armour::reader::kMaxTotalInstanceExtras] = {
        reinterpret_cast<void*>(kVtable), 1, {}, nullptr};
    read = {}; ExpectRejected(Run(f, read), Code::TraversalLimit,
        "total instance-extra cap plus one rejects without truncation");

    f.Reset(false, 0); std::vector<Node> emptyEntries(513);
    for (std::size_t i = 0; i + 1 < 512; ++i) emptyEntries[i].next = &emptyEntries[i + 1];
    f.container.list = &emptyEntries[0]; read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteNoArmourObserved, "exact entry-node cap succeeds");
    emptyEntries[511].next = &emptyEntries[512]; read = {};
    ExpectRejected(Run(f, read), Code::TraversalLimit,
        "entry-node cap plus one rejects without truncation");

    f.Reset(false, 0); std::vector<Node> emptyInstances(1025);
    for (std::size_t i = 0; i + 1 < 1024; ++i) emptyInstances[i].next = &emptyInstances[i + 1];
    f.entry.extend = &emptyInstances[0]; read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteNoArmourObserved,
        "exact instance-node cap succeeds");
    emptyInstances[1023].next = &emptyInstances[1024]; read = {};
    ExpectRejected(Run(f, read), Code::TraversalLimit,
        "instance-node cap plus one rejects without truncation");

    f.Reset(false, 0); std::vector<Extra> actorExtras(64);
    for (auto& e : actorExtras) e = {reinterpret_cast<void*>(kVtable), 1, {}, nullptr};
    f.xcc.base.next = &actorExtras[0];
    for (std::size_t i = 0; i + 1 < 63; ++i) actorExtras[i].next = &actorExtras[i + 1];
    read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteWithArmour, "exact actor-extra cap succeeds");
    actorExtras[62].next = &actorExtras[63]; read = {};
    ExpectRejected(Run(f, read), Code::TraversalLimit,
        "actor-extra cap plus one rejects without truncation");

    f.Reset(false, 0); std::vector<Node> manyEntryNodes(33), manyInstanceNodes(33);
    std::vector<Entry> manyEntries(33); std::vector<ExtraList> manyInstances(33);
    std::vector<Extra> manyWorn(33);
    for (std::size_t i = 0; i < 33; ++i) {
        manyEntryNodes[i].data = &manyEntries[i];
        manyEntryNodes[i].next = i + 1 < 32 ? &manyEntryNodes[i + 1] : nullptr;
        manyEntries[i] = {&manyInstanceNodes[i], 1, f.armour};
        manyInstanceNodes[i].data = &manyInstances[i];
        manyInstances[i].vt = reinterpret_cast<void*>(kVtable);
        manyInstances[i].head = &manyWorn[i]; Presence(manyInstances[i], 0x16);
        manyWorn[i] = {reinterpret_cast<void*>(kVtable), 0x16, {}, nullptr};
    }
    f.container.list = &manyEntryNodes[0]; read = {}; result = Run(f, read);
    Check(result.code == Code::CompleteWithArmour && result.itemCount == 32,
        "exact equipped-armour output cap succeeds");
    manyEntryNodes[31].next = &manyEntryNodes[32]; read = {};
    ExpectRejected(Run(f, read), Code::TraversalLimit,
        "equipped-armour output cap plus one rejects all rows");

    f.Reset(true, 60.0f); read = {}; result = Run(f, read);
    const unsigned successfulReadCount = read.calls;
    Check(successfulReadCount > 20, "fixture exercises a nontrivial guarded-read graph");
    for (unsigned failAt = 1; failAt <= successfulReadCount; ++failAt) {
        ReadContext injected{}; injected.failAt = failAt;
        const Snapshot failed = Run(f, injected);
        Check(!nvo::armour::reader::Complete(failed.code) && failed.itemCount == 0,
            "each injected guarded-read failure rejects all output");
    }

    f.Reset(true, 60.0f); read = {};
    const float changedHealth = 59.0f;
    read.mutateAddress = &f.health.health; read.mutateLocation = &f.health.health;
    read.mutateValue = &changedHealth; read.mutateSize = sizeof(changedHealth);
    read.mutateAtOccurrence = 2;
    ExpectRejected(Run(f, read), Code::Unstable,
        "condition mutation between passes rejects");

    f.Reset(false, 0); read = {};
    const U32 changedPartMask = 1;
    read.mutateAddress = f.armour + 0x74; read.mutateLocation = f.armour + 0x74;
    read.mutateValue = &changedPartMask; read.mutateSize = sizeof(changedPartMask);
    read.mutateAtOccurrence = 2;
    ExpectRejected(Run(f, read), Code::Unstable,
        "armour field mutation between passes rejects");

    f.Reset(false, 0); read = {};
    ExtraList replacementInstance{}; Extra replacementWorn{};
    replacementInstance.vt = reinterpret_cast<void*>(kVtable);
    replacementInstance.head = &replacementWorn; Presence(replacementInstance, 0x16);
    replacementWorn = {reinterpret_cast<void*>(kVtable), 0x16, {}, nullptr};
    void* replacementPointer = &replacementInstance;
    read.mutateAddress = &f.instanceHead; read.mutateLocation = &f.instanceHead.data;
    read.mutateValue = &replacementPointer; read.mutateSize = sizeof(replacementPointer);
    read.mutateAtOccurrence = 2;
    ExpectRejected(Run(f, read), Code::Unstable,
        "exact instance identity mutation between passes rejects");

    f.Reset(false, 0); reinterpret_cast<Form*>(f.actor)->type = 0x3C; read = {};
    ExpectRejected(Run(f, read), Code::UnsupportedTarget,
        "creature reference is unsupported rather than bare");
    f.Reset(false, 0); reinterpret_cast<Form*>(f.actor)->id = kActorId + 1; read = {};
    ExpectRejected(Run(f, read), Code::UnsupportedTarget,
        "target identity mismatch rejects");

    std::printf("PASS %u checks; guarded x86 reader only, no game or DLL execution.\n", gChecks);
    return 0;
}

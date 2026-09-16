#include "NvseBootstrapApi.hpp"
#include "NativeLog.hpp"
#include "NativeObserver.hpp"
#include "DamageEvents.hpp"
#include "FlightPhysics.hpp"
#include <Windows.h>

namespace {
constexpr char kPluginName[] = "NVOCombatCore";
constexpr std::uint32_t kPluginVersion = 312; // 0.3.12, packet 3F1 bounded failure diagnostics
constexpr bool kHitHooksImplemented = false;
constexpr bool kDamageReplacementEnabled = false;
bool gLoaded = false;
unsigned gSession = 0;

bool SupportsHost(const nvo::nvse::InterfacePrefix* host) noexcept
{
    return host && !host->isEditor
        && host->runtimeVersion == nvo::nvse::kSupportedRuntime
        && host->nvseVersion >= nvo::nvse::kMinimumXnvse
        && (host->nvseVersion >> 24) == 6;
}

void __cdecl OnNvseMessage(nvo::nvse::Message* message) noexcept
{
    if (!message) {
        return;
    }
    using nvo::nvse::MessageType;
    switch (static_cast<MessageType>(message->type)) {
    case MessageType::PostLoad:
        nvo::log::Write("LIFECYCLE post_load_plugins");
        break;
    case MessageType::PostPostLoad:
        nvo::log::Write("LIFECYCLE post_post_load_plugins");
        break;
    case MessageType::DeferredInit:
        nvo::log::Write("LIFECYCLE deferred_init");
        nvo::physics::Initialize();
        break;
    case MessageType::PreLoadGame:
        nvo::observer::Suspend("pre_load_game");
        nvo::damage::Suspend("pre_load_game");
        nvo::log::Write("LIFECYCLE pre_load_game");
        break;
    case MessageType::LoadGame:
        nvo::log::Write("LIFECYCLE load_game");
        break;
    case MessageType::PostLoadGame: {
        // xNVSE Serialization.cpp casts the Boolean VALUE to void*.
        // It is not a pointer to a Boolean and must not be dereferenced.
        const bool success = message->data != nullptr;
        if (success) {
            ++gSession;
            nvo::observer::QueueCapture("post_load_game");
            nvo::damage::QueueCapture("post_load_game", gSession);
        } else {
            nvo::observer::Suspend("load_failed");
            nvo::damage::Suspend("load_failed");
        }
        nvo::log::Write("LIFECYCLE post_load_game success=%u session=%u",
            success ? 1u : 0u, gSession);
        break;
    }
    case MessageType::NewGame:
        ++gSession;
        nvo::observer::QueueCapture("new_game");
        nvo::damage::QueueCapture("new_game", gSession);
        nvo::log::Write("LIFECYCLE new_game session=%u", gSession);
        break;
    case MessageType::ExitToMainMenu:
        nvo::observer::Suspend("exit_to_main_menu");
        nvo::damage::Suspend("exit_to_main_menu");
        nvo::log::Write("LIFECYCLE exit_to_main_menu");
        break;
    case MessageType::ExitGame:
    case MessageType::ExitGameConsole:
        nvo::observer::Suspend("exit_game");
        nvo::damage::Suspend("exit_game");
        nvo::log::Write("LIFECYCLE exit_game");
        break;
    case MessageType::MainGameLoop:
        nvo::observer::Tick();
        nvo::damage::Tick();
        break;
    default:
        break;
    }
}

// Observer callbacks do not install engine damage hooks or change damage.
static_assert(!kHitHooksImplemented && !kDamageReplacementEnabled);
} // namespace

extern "C" bool __cdecl NVSEPlugin_Query(
    const nvo::nvse::InterfacePrefix* host,
    nvo::nvse::PluginInfo* info) noexcept
{
    if (!info) {
        return false;
    }
    info->infoVersion = nvo::nvse::kInfoVersion;
    info->name = kPluginName;
    info->version = kPluginVersion;

    if (!SupportsHost(host)) {
        OutputDebugStringA("NVOCombatCore: requires normal FNV 1.4.0.525 and xNVSE 6.4.8+, major 6. Editor unsupported.\n");
        return false;
    }
    if (!nvo::log::Initialize()) {
        OutputDebugStringA("NVOCombatCore: cannot create NVOCombatCore.log in the game directory. Query rejected.\n");
        return false;
    }
    nvo::log::Write("NVOCombatCore 0.3.12 | phase=3F1 | native_events=1 | current_hit_observer_pending=1 | itr_damage_events_pending=1 | flight_preview=1 | flight_timing_pending=1 | native_physics_pending=1 | per_shot_selection=1 | movement_argument_pilot=1 | isolated_record_flight_pilot=1 | hit_hooks=0 | damage_replacement=0");
    nvo::log::Write("QUERY runtime=0x%08X xnvse=0x%08X editor=%u",
        host->runtimeVersion, host->nvseVersion, host->isEditor);
    return true;
}

extern "C" bool __cdecl NVSEPlugin_Load(
    const nvo::nvse::InterfacePrefix* host) noexcept
{
    if (!SupportsHost(host)) {
        return false;
    }
    if (gLoaded) {
        return true;
    }
    if (!host->QueryInterface || !host->GetPluginHandle) {
        nvo::log::Write("LOAD rejected: required public interface functions unavailable");
        return false;
    }
    const auto* messaging = static_cast<nvo::nvse::MessagingPrefix*>(
        host->QueryInterface(nvo::nvse::kMessagingInterface));
    const auto handle = host->GetPluginHandle();
    if (!messaging || messaging->version < nvo::nvse::kMessagingVersion
        || !messaging->RegisterListener || handle == nvo::nvse::kInvalidPluginHandle) {
        nvo::log::Write("LOAD rejected: messaging v4 or valid plugin handle unavailable");
        return false;
    }
    if (!messaging->RegisterListener(handle, "NVSE", OnNvseMessage)) {
        nvo::log::Write("LOAD rejected: could not register NVSE lifecycle listener");
        return false;
    }
    nvo::observer::Initialize(static_cast<nvo::observer::EventApiPrefix*>(host->QueryInterface(8)),
        static_cast<nvo::nvse::ConsolePrefix*>(host->QueryInterface(1)));
    nvo::damage::Initialize(static_cast<nvo::observer::EventApiPrefix*>(host->QueryInterface(8)),
        static_cast<nvo::nvse::ConsolePrefix*>(host->QueryInterface(1)));
    gLoaded = true;
    nvo::log::Write("LOAD registered=1 messaging=%u hit_hooks=0 damage_replacement=0",
        messaging->version);
    return true;
}


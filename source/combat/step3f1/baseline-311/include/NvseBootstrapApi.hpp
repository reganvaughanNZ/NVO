#pragma once

#include <cstddef>
#include <cstdint>

// Read-only prefix views of xNVSE 6.4.8 public interfaces.
// This header describes public APIs only; CurrentHit.hpp holds the separate
// version-guarded game layout. No script opcode is registered.
// Source of field order: xNVSE nvse/nvse/PluginAPI.h.
// See README.md and the packet's sdk-reference.json for provenance.
namespace nvo::nvse {

struct CommandInfo;
using PluginHandle = std::uint32_t;

struct InterfacePrefix {
    std::uint32_t nvseVersion;
    std::uint32_t runtimeVersion;
    std::uint32_t editorVersion;
    std::uint32_t isEditor;
    bool (__cdecl* RegisterCommand)(CommandInfo*);
    void (__cdecl* SetOpcodeBase)(std::uint32_t);
    void* (__cdecl* QueryInterface)(std::uint32_t);
    PluginHandle (__cdecl* GetPluginHandle)();
};

struct PluginInfo {
    std::uint32_t infoVersion;
    const char* name;
    std::uint32_t version;
};

// MAKE_NEW_VEGAS_VERSION layout from xNVSE nvse_version.h.
constexpr std::uint32_t kMinimumXnvse = 0x06040080; // 6.4.8
constexpr std::uint32_t kSupportedRuntime = 0x040020D0; // 1.4.0.525
constexpr std::uint32_t kInfoVersion = 1;
constexpr std::uint32_t kMessagingInterface = 2;
constexpr std::uint32_t kMessagingVersion = 4;
constexpr PluginHandle kInvalidPluginHandle = 0xFFFFFFFFu;

struct Message {
    const char* sender;
    std::uint32_t type;
    std::uint32_t dataLen;
    void* data;
};

using MessageCallback = void (__cdecl*)(Message*);

struct MessagingPrefix {
    std::uint32_t version;
    bool (__cdecl* RegisterListener)(PluginHandle, const char*, MessageCallback);
};

// Public Console API v2+ prefix, queried as interface 1. Used only for a
// fixed console diagnostic after gameplay begins; never opens a message box.
struct ConsolePrefix {
    std::uint32_t version;
    bool (__cdecl* RunScriptLine)(const char*, void*);
};
static_assert(sizeof(ConsolePrefix) == 8);

// Values from NVSEMessagingInterface in PluginAPI.h. Omitted messages
// are intentionally ignored rather than treated as gameplay callbacks.
enum class MessageType : std::uint32_t {
    PostLoad = 0,
    ExitGame = 1,
    ExitToMainMenu = 2,
    LoadGame = 3,
    PreLoadGame = 6,
    ExitGameConsole = 7,
    PostLoadGame = 8,
    PostPostLoad = 9,
    NewGame = 14,
    DeferredInit = 18,
    MainGameLoop = 20
};

static_assert(sizeof(void*) == 4, "The plugin must be built for Win32.");
static_assert(sizeof(InterfacePrefix) == 32);
static_assert(offsetof(InterfacePrefix, isEditor) == 12);
static_assert(offsetof(InterfacePrefix, QueryInterface) == 24);
static_assert(offsetof(InterfacePrefix, GetPluginHandle) == 28);
static_assert(sizeof(PluginInfo) == 12);
static_assert(offsetof(PluginInfo, name) == 4);
static_assert(offsetof(PluginInfo, version) == 8);
static_assert(sizeof(Message) == 16);
static_assert(offsetof(Message, data) == 12);
static_assert(sizeof(MessagingPrefix) == 8);
static_assert(offsetof(MessagingPrefix, RegisterListener) == 4);

} // namespace nvo::nvse

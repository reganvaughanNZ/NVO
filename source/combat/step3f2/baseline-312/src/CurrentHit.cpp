#include "CurrentHit.hpp"
#include "NativeObserver.hpp"
#include "NativeLog.hpp"
#include <Windows.h>
#include <atomic>
#include <cstring>

namespace {
using U32 = std::uint32_t;
constexpr std::uintptr_t kSlots[] = {0x1087FD8, 0x10897C0};
constexpr U32 kJipTimestamp = 0x665225A8, kJipSize = 0x80000;
constexpr U32 kCopyRva = 0x9490, kAmmoRva = 0x10620;
constexpr U32 kPreferredJipBase = 0x10000000;
void* gOriginal{}; // Same verified JIP CopyHitData target for both process tables.
std::atomic<bool> gAmmoSupported{false};
bool gAttempted{}, gInstalled{};

// C++ observer receives copied scalars only. Preserve Win32 thread error state.
void __cdecl Capture(const nvo::hit::Data* data, void* process, const void* caller) noexcept
{
    const DWORD error = GetLastError();
    nvo::observer::CurrentHit(data, process, caller);
    SetLastError(error);
}

// Same stack and return address reach JIP; it is tail-called exactly once.
// Save integer registers/EFLAGS and all x87/SSE state, including MXCSR.
// No replay of instructions, new game allocations, or hit-data writes.
__declspec(naked) void CopyObserver()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push dword ptr [ebx+36]
        push dword ptr [ebx+24]
        push dword ptr [ebx+40]
        call Capture
        add esp, 12
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginal]
    }
}

bool ImageMatches(HMODULE module, U32 timestamp, U32 size) noexcept
{
    IMAGE_DOS_HEADER dos{};
    IMAGE_NT_HEADERS32 nt{};
    if (!module || !nvo::hit::ReadBytes(module, &dos, sizeof(dos))
        || dos.e_magic != IMAGE_DOS_SIGNATURE || dos.e_lfanew < 0x40 || dos.e_lfanew > 0x1000)
        return false;
    if (!nvo::hit::ReadBytes(reinterpret_cast<const char*>(module) + dos.e_lfanew, &nt, sizeof(nt)))
        return false;
    return nt.Signature == IMAGE_NT_SIGNATURE && nt.FileHeader.Machine == IMAGE_FILE_MACHINE_I386
        && nt.OptionalHeader.Magic == IMAGE_NT_OPTIONAL_HDR32_MAGIC
        && nt.FileHeader.TimeDateStamp == timestamp && nt.OptionalHeader.SizeOfImage == size;
}
bool InImage(const void* address, HMODULE module, bool executable) noexcept
{
    MEMORY_BASIC_INFORMATION info{};
    if (!VirtualQuery(address, &info, sizeof(info)) || info.State != MEM_COMMIT
        || info.Type != MEM_IMAGE || info.AllocationBase != module
        || (info.Protect & (PAGE_NOACCESS | PAGE_GUARD))) return false;
    return !executable || (info.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ
        | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY));
}
// Compatibility fingerprints of complete inspected functions, not copied code.
// Normalize the only JIP base relocation in CopyHitData before hashing.
bool Fingerprint(HMODULE module, U32 rva, unsigned size, std::uint64_t expected,
    unsigned relocatedOffset = 0) noexcept
{
    unsigned char bytes[160]{};
    const auto* address = reinterpret_cast<const char*>(module) + rva;
    if (size > sizeof(bytes) || !InImage(address, module, true)
        || !InImage(address + size - 1, module, true)
        || !nvo::hit::ReadBytes(address, bytes, size)) return false;
    if (relocatedOffset) {
        U32 value{};
        std::memcpy(&value, bytes + relocatedOffset, 4);
        value -= static_cast<U32>(reinterpret_cast<std::uintptr_t>(module)) - kPreferredJipBase;
        std::memcpy(bytes + relocatedOffset, &value, 4);
    }
    std::uint64_t hash = 14695981039346656037ull;
    for (unsigned i = 0; i < size; ++i) hash = (hash ^ bytes[i]) * 1099511628211ull;
    return hash == expected;
}
bool OwnsSlots(void* target) noexcept
{
    for (auto address : kSlots) {
        void* actual{};
        if (!nvo::hit::ReadBytes(reinterpret_cast<void*>(address), &actual, sizeof(actual))
            || actual != target) return false;
    }
    return true;
}
bool AmmoHookMatches(HMODULE jip) noexcept
{
    unsigned char branch[5]{};
    if (!Fingerprint(jip, kAmmoRva, 156, 0xB1A07310C15D7E37ull)
        || !nvo::hit::ReadBytes(reinterpret_cast<void*>(0x9BC241), branch, sizeof(branch))
        || branch[0] != 0xE9) return false;
    std::int32_t relative{};
    std::memcpy(&relative, branch + 1, 4);
    return static_cast<U32>(0x9BC246 + relative)
        == reinterpret_cast<std::uintptr_t>(jip) + kAmmoRva;
}
bool Disabled(const char* reason) noexcept
{
    gAmmoSupported.store(false);
    nvo::log::Write("CURRENT_HIT_DISABLED reason=%s damage_replacement=0", reason);
    return false;
}
} // namespace

bool nvo::hit::ReadBytes(const void* address, void* destination, std::size_t size) noexcept
{
    if (!address) return false;
    __try {
        std::memcpy(destination, address, size);
        return true;
    } __except (GetExceptionCode() == EXCEPTION_ACCESS_VIOLATION
        ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) { return false; }
}
bool nvo::hit::ReadForm(void* form, Form& result) noexcept
{
    result = {};
    if (!form) return true;
    unsigned char header[16]{};
    if (!ReadBytes(form, header, sizeof(header))) return false;
    result.type = header[4];
    std::memcpy(&result.id, header + 12, 4);
    return true;
}
bool nvo::hit::IsProjectile(unsigned char type) noexcept
{
    return (type >= 0x3D && type <= 0x40) || type == 0x69;
}
bool nvo::hit::ProjectileLayoutReady() noexcept { return gAmmoSupported.load(); }
std::uint32_t nvo::hit::ProjectileAmmo(void* projectile, unsigned& failures) noexcept
{
    if (!gAmmoSupported.load()) return 0;
    Form form{};
    if (!ReadForm(projectile, form)) { ++failures; return 0; }
    if (!IsProjectile(form.type)) return 0;
    unsigned char count{};
    auto* bytes = static_cast<const char*>(projectile);
    if (!ReadBytes(bytes + 0x14A, &count, 1)) { ++failures; return 0; }
    if (!count) return 0;
    void* ammo{};
    if (!ReadBytes(bytes + 0x60, &ammo, sizeof(ammo)) || !ReadForm(ammo, form)) {
        ++failures; return 0;
    }
    return form.type == 0x29 ? form.id : 0;
}

bool nvo::hit::EnsureInstalled() noexcept
{
    if (gAttempted) {
        if (!gInstalled || !OwnsSlots(reinterpret_cast<void*>(CopyObserver)))
            return Disabled("observer_slot_changed_or_previous_install_failed");
        gAmmoSupported.store(AmmoHookMatches(GetModuleHandleW(L"jip_nvse.dll")));
        return true;
    }
    gAttempted = true;
    auto game = GetModuleHandleW(nullptr);
    auto jip = GetModuleHandleW(L"jip_nvse.dll");
    if (reinterpret_cast<std::uintptr_t>(game) != 0x400000
        || !ImageMatches(game, 0x4E0D50ED, 0x107B000)) return Disabled("unsupported_game_image");
    if (!ImageMatches(jip, kJipTimestamp, kJipSize)
        || !Fingerprint(jip, kCopyRva, 106, 0x5DB9CC631AC1E846ull, 0x59))
        return Disabled("unsupported_jip_copy_function");
    auto* original = reinterpret_cast<char*>(jip) + kCopyRva;
    if (!OwnsSlots(original)) return Disabled("copy_slots_owned_by_other_implementation");
    for (auto address : kSlots)
        if (!InImage(reinterpret_cast<void*>(address), game, false)) return Disabled("invalid_vtable_page");

    // Both protections must succeed before either pointer is written.
    DWORD oldProtection[2]{};
    if (!VirtualProtect(reinterpret_cast<void*>(kSlots[0]), 4, PAGE_READWRITE, &oldProtection[0]))
        return Disabled("first_vtable_protection_failed");
    if (!VirtualProtect(reinterpret_cast<void*>(kSlots[1]), 4, PAGE_READWRITE, &oldProtection[1])) {
        DWORD ignored{};
        VirtualProtect(reinterpret_cast<void*>(kSlots[0]), 4, oldProtection[0], &ignored);
        return Disabled("second_vtable_protection_failed");
    }
    gOriginal = original; // Publish before either table can call the wrapper.
    const auto wrapper = reinterpret_cast<void*>(CopyObserver);
    bool changed[2]{};
    for (unsigned i = 0; i < 2; ++i) {
        changed[i] = InterlockedCompareExchangePointer(
            reinterpret_cast<void* volatile*>(kSlots[i]), wrapper, original) == original;
        if (!changed[i]) break;
    }
    gInstalled = changed[0] && changed[1];
    if (!gInstalled) for (unsigned i = 0; i < 2; ++i) if (changed[i])
        InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(kSlots[i]), original, wrapper);
    for (unsigned i = 0; i < 2; ++i) {
        DWORD ignored{};
        if (!VirtualProtect(reinterpret_cast<void*>(kSlots[i]), 4, oldProtection[i], &ignored))
            nvo::log::Write("HOOK_PROTECTION_RESTORE_FAILED slot=%u", i);
    }
    if (!gInstalled) return Disabled("copy_slot_changed_during_install");
    gAmmoSupported.store(AmmoHookMatches(jip));
    nvo::log::Write("CURRENT_HIT_READY provider=JIP5730 phase=copy_input vtable_slots=2 original_tail_calls=1 ammo_layout_verified=%u damage_replacement=0",
        gAmmoSupported.load() ? 1u : 0u);
    return true;
}

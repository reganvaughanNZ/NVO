#include "NativeLog.hpp"
#include <Windows.h>
#include <cstdarg>
#include <cstdio>
#include <cwchar>
#include <cstring>

namespace {
SRWLOCK gLock = SRWLOCK_INIT;
wchar_t gPath[32768]{};
constexpr DWORD kPathCapacity = static_cast<DWORD>(sizeof(gPath) / sizeof(gPath[0]));
bool gReady = false;
unsigned gRows = 0, gDetailRows = 0, gPriorityRows = 0;
constexpr unsigned kMaximumDetail = 7168, kMaximumPriority = 1024;

class Lock final {
public:
    Lock() noexcept { AcquireSRWLockExclusive(&gLock); }
    ~Lock() { ReleaseSRWLockExclusive(&gLock); }
    Lock(const Lock&) = delete;
    Lock& operator=(const Lock&) = delete;
};

bool Append(const char* text, DWORD length) noexcept
{
    const HANDLE file = CreateFileW(gPath, FILE_APPEND_DATA,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    }
    DWORD written = 0;
    const bool ok = WriteFile(file, text, length, &written, nullptr)
        && written == length;
    CloseHandle(file);
    return ok;
}
} // namespace

bool nvo::log::Initialize() noexcept
{
    const Lock lock;
    if (gReady) {
        return true;
    }
    const DWORD length = GetModuleFileNameW(nullptr, gPath, kPathCapacity);
    if (!length || length >= kPathCapacity) {
        return false;
    }
    wchar_t* separator = std::wcsrchr(gPath, L'\\');
    if (!separator) {
        return false;
    }
    separator[1] = L'\0';
    if (wcscat_s(gPath, L"NVOCombatCore.log") != 0) {
        return false;
    }
    const HANDLE file = CreateFileW(gPath, GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    }
    CloseHandle(file);
    gRows = gDetailRows = gPriorityRows = 0;
    gReady = true;
    return true;
}

bool nvo::log::Write(const char* format, ...) noexcept
{
    const Lock lock;
    const bool priority = std::strstr(format, "SUMMARY") || std::strstr(format, "LIFECYCLE")
        || std::strstr(format, "READY") || std::strstr(format, "DISABLED") || std::strstr(format, "REJECT")
        || std::strstr(format, "PHYSICS_SHOT") || std::strstr(format, "FLIGHT_TIMING_SHOT")
        || std::strstr(format, "PHYSICS_NO_UPDATE") || std::strstr(format, "PHYSICS_ARMED")
        || std::strstr(format, "NVOCombatCore");
    if (!gReady || (priority ? gPriorityRows >= kMaximumPriority : gDetailRows >= kMaximumDetail)) {
        return false;
    }
    char line[768]{};
    va_list args;
    va_start(args, format);
    const int count = vsnprintf_s(line, sizeof(line) - 2, _TRUNCATE, format, args);
    va_end(args);
    if (count < 0) {
        return false;
    }
    line[count] = '\r';
    line[count + 1] = '\n';
    if (!Append(line, static_cast<DWORD>(count + 2))) {
        return false;
    }
    ++gRows;
    if (priority) ++gPriorityRows; else ++gDetailRows;
    if (!priority && gDetailRows == kMaximumDetail) {
        constexpr char footer[] = "DETAIL_LIMIT reached; lifecycle and summaries retain separate bounded reserve\r\n";
        Append(footer, sizeof(footer) - 1);
    }
    return true;
}

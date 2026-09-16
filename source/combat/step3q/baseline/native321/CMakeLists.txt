cmake_minimum_required(VERSION 3.21)
project(NVOCombatCore VERSION 0.3.21 LANGUAGES CXX)

if(NOT WIN32 OR NOT MSVC)
    message(FATAL_ERROR "NVOCombatCore requires Windows and the MSVC C++ toolchain.")
endif()
if(NOT CMAKE_SIZEOF_VOID_P EQUAL 4)
    message(FATAL_ERROR "Configure with -A Win32. Fallout New Vegas is a 32-bit process.")
endif()

add_library(NVOCombatCore SHARED src/Plugin.cpp src/NativeLog.cpp src/NativeObserver.cpp src/CurrentHit.cpp src/DamageEvents.cpp src/HitTransaction.cpp src/ActorValueObserver.cpp src/FlightPreview.cpp src/FlightTiming.cpp src/FlightPhysics.cpp src/SpawnBoundary.cpp src/Exports.def)
target_compile_features(NVOCombatCore PRIVATE cxx_std_17)
target_include_directories(NVOCombatCore PRIVATE include)
target_link_libraries(NVOCombatCore PRIVATE kernel32)
target_compile_definitions(NVOCombatCore PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
target_compile_options(NVOCombatCore PRIVATE /W4 /permissive- /EHsc /Zi)
set_property(TARGET NVOCombatCore PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
set_target_properties(NVOCombatCore PROPERTIES PREFIX "" OUTPUT_NAME "NVOCombatCore")

# Deliberately no install target or automatic copy into a game directory.

target_link_options(NVOCombatCore PRIVATE /DEBUG:FULL /OPT:REF /OPT:ICF)


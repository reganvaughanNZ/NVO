# Step4C verification

Standalone PE32 x86 checker compiled with MSVC C++17, /W4 /WX and static runtime.53 focused C++ checks,21 strict authoring checks,76 captured-snapshot replays and10,000 deterministic repetitions passed. No DLL build or game installation occurred. Existing native and pure-model sources match their pinned baselines. See CHECKS.json for counts and SOURCE-SNAPSHOT.json for new source hashes.

Rebuild from the working project (or packaged Source tree): run the Python generator tools/generate_combat_4c_fixtures.py, then native/NVOCombatModel/run_coverage_checks.cmd. Run tools/check_combat_4c_profiles.py for authoring validation. The CMD uses the installed Visual Studio18 Community x86 environment. Generated fixtures contain only known captured base-game armour identities; they are not a general runtime FormID resolver.

# Step 4A build result

Prepared on 2026-09-16 with the local Visual Studio x86 toolchain.

`run_shadow_checks.cmd` compiled `ArmourModel.cpp`, `ShadowAdapter.cpp`, and `shadow_adapter_tests.cpp` with C++17, `/W4`, `/WX`, `/permissive-`, optimization and static runtime. The compiler reported no warnings or errors. The executable completed 48 checks with zero failures and reported `gameplay_writes=0 runtime_integrated=0 synthetic_profiles=1`.

The existing `run_checks.cmd` target was rebuilt after the adapter change. Its 45 armour-model checks passed with zero failures and `gameplay_writes=0 synthetic_fixtures=1`.

These are standalone offline executables. No NVSE DLL or installable game binary was produced.

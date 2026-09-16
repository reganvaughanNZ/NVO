# NVOCombatCore 0.3.26 / Packet 4B build result

Final build: `out/build-20913-15431`

- Compiler: MSVC x86 19.51.36257.0
- Options include `/O2 /MT /Zi /W4 /WX /permissive-`
- Result: zero compiler warnings and zero errors
- Format: PE32 x86
- Exports: exactly `NVSEPlugin_Load` and `NVSEPlugin_Query`
- Imported DLLs: `KERNEL32.dll` only
- Reader harness: PASS 452
- RSDS/PDB identity: `8F044AF3-BB3A-4716-9FA2-182E48BED43C`, age 1

Artifacts:

- `NVOCombatCore.dll` — 362,496 bytes — SHA-256 `3d5ff40c5c8ba418c0764cba55bd8595cfa1444396f4e814552210524094e13a`
- `NVOCombatCore.pdb` — 4,673,536 bytes — SHA-256 `9411d09fefe2e59fa50a891081592b81fbc9cc50602bee8951a04e706ac8d2a0`

Static comparison against frozen Packet 3U1 found all 45 existing patch-related source lines unchanged. The new armour modules contain no patch API, ShadowAdapter/ArmourModel linkage, or health, limb, inventory, condition, equipment, or damage write.

This build has not been copied into Fallout New Vegas and has not been loaded by the game.

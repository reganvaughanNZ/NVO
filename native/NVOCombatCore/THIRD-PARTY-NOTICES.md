# NVOCombatCore packet 4B notices

This native NVOCombatCore packet is supplied under GNU GPL version 3. See LICENSE-GPL-3.0.txt. Corresponding source and build instructions accompany the compiled delivery. Preserve these notices when sharing this packet. This notice concerns the native packet, not a relicensing of Fallout New Vegas, NVO.esm or unrelated donor content.

NVO's observer, lifetime tracking, guarded installation and logging are newly authored integration code. The ActorHitData layout, process slot locations, form types and projectile ammunition contract were adapted from JIP LN NVSE source by jazzisparis and contributors, supplied under GPLv3. No JIP function implementation or DLL is redistributed here. Function fingerprints are compatibility identifiers and are not executed. Reference: https://github.com/jazzisparis/JIP-LN-NVSE

xNVSE developers: public plugin, messaging, Console and native event interfaces. Reference: https://github.com/xNVSE/NVSE

Demorome and ShowOff contributors: projectile/explosion event contracts. We call these existing provider events; no ShowOff implementation or DLL is redistributed. Reference: https://github.com/Demorome/Showoff-NVSE

JohnnyGuitar remains an existing NVO dependency. Its release binaries were inspected as references and are not bundled. The EDID warning identified in REVIEW-4 is independent of this packet.

Fallout New Vegas is required and remains separately owned. No game executable, master, assets or extracted executable code are distributed in this packet.

Into the Rough contributors (2026): ITR 2.2.2 pre-hit/pre-health event contracts and float-slot encoding, supplied under MIT. See LICENSE-ITR-MIT.txt. We observe existing public events without copying its hooks or bundling its DLL. Matching source paths/hashes are in sdk-reference.json.

Packet 3B1 also reads the xNVSE GameData loaded-mod layout and JIP projectile/base-form speed, gravity, lifetime and distance layouts. These source contracts are pinned in sdk-reference.json. BallistX donor data and the barrel-speed relation are credited separately in CREDITS-BALLISTX.md; no donor asset relicensing is asserted.

Packet 3P inspects ShowOff184 OnPreProjectileCreate::HandleEvent and its saved engine continuation. Newly authored NVO code atomically interposes the pinned in-memory continuation pointer for a diagnostic, forwards the inspected sixteen-word cdecl ABI unchanged, and correlates return/creation events. ShowOff source and deployed binary were used to establish that contract; no ShowOff implementation, DLL, PDB, or extracted disassembly is redistributed.

Packet3Q moves NVO selection into that same pinned provider continuation, after bounded physics/lifecycle reservation. This is newly authored integration code; it changes only the per-call projectile-base argument when admitted. Corresponding source and the failure-policy limitations accompany the binary.

Packet 3R: the original diagnostic capacity-probe helper and ownership tests add no new donor code. Existing notices remain applicable.

Packet 4B uses the supplied JIP LN NVSE and xNVSE type declarations as layout references for `TESObjectREFR`, extra-data lists, `ExtraContainerChanges`, inventory list nodes, `ExtraWorn`, `ExtraHealth`, and `TESObjectARMO`. The guarded traversal and validation code is newly authored NVO code. No provider implementation, binary, engine helper, or extracted game code is copied into the reader. Exact local reference hashes and line ranges accompany the packet in `LAYOUT-PROVENANCE.json`.

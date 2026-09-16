# Directional Shooting v1.1 — idea review, 15 September 2026

Status: candidate only. User explicitly asked for an assessment and no implementation. No installation, activation, native code/config changes, game launch or gameplay test performed for this resource. The source review below supersedes the earlier binary-only limits. Current NVO work remains the separately proposed 3B3 timing observer.

## Source added and inspected, 15 September 2026

Archive: `C:/Users/regan/Desktop/NVO Mod References (Open Source)/FNV-Directional-Shooting-main.zip` (281,747 bytes).
SHA256: `1d73467e79d0e016bdba9aa3be7eeeaa3f18febe40ec9cdf9f9a17b6d1c720e4`.
Member root: `FNV-Directional-Shooting-main/`. File hashes and scope are in `DIRECTIONAL-SHOOTING-SOURCE.json`. Source was read directly from the ZIP, without executing or installing anything.

`DirectionalShooting/main.cpp` advertises integer plugin version 114 (line 49). It is not established that this source reproduces the previously supplied v1.1 binary. The archive includes a GNU GPL version 3 LICENSE; preserve it and record the applicable source-release requirements before distributing an adaptation. The earlier Nexus binary-page permission summary is not a substitute for the source license.

### Useful implementation and fit

- `main.cpp:88–114` converts the first-person Weapon node's world rotation into projectile angles. Lines 128–132 capture the projectile node's world position. This provides a concrete reference for a later launch-direction/origin module.
- Lines 173–180 bypass correction for third person and non-player references. This is first-person player shooting, not a replacement for NPC aim or threat scanning.
- Lines 195–214 preserve an angular spread offset measured before the original aiming call, then add it to the corrected angles. This intends to retain spread; it does not prove correct composition with NVO spread, auto-aim, recoil or every animation.
- Active hooks are call sites `009BD9E2` (projectile aim initialization) and `00949CF1` (before attack animation), lines 242–248. Impact and wobble hooks in that function are commented out. Neither active address is the candidate missile-update boundary `009B8030` or the already-detoured base update `009BECC0`.
- The saved main-menu runtime snapshot shows `009BD9E2` calling `00965620`. This establishes the captured site's contents only; the other active call site was outside that snapshot. Distinct hook addresses do not prove interoperability. NVO must sample final launch state after correction, and later flight must preserve that direction.

### Issues to address before adopting it

1. **Throwing toggle is ineffective in the inspected implementation.** `CFG_ThrowableMelee` is declared and populated from INI, but the throwing branch at lines 183–192 never checks it. That branch directly changes projectile rotation after calling the original function.
2. **Position correction is independent of direction toggles.** A valid projectile node sets `doRectifyPos` at lines 128–132 without consulting the options; lines 201–205 then move the projectile. Turning off hip-fire and aimed direction correction is therefore not a complete disable switch.
3. **Scope exclusions are partial.** Lines 138–141 suppress aimed rotation correction for scopes/B42 detection, but do not gate the separately captured position change. `Gathering_Utility.h:143–156` detects B42 via an `OldIS` node and sights via `##SightingNode`; universal compatibility with current optics/animation setups is unproven.
4. **Per-shot state needs lifecycle review.** A single global rectifier stores and consumes flags. Missing Weapon rotation can leave a true flag with old angle values. Multi-projectile shots and repeated/nested callbacks need verification to ensure every pellet gets the intended correction once. There is no explicit VATS guard in the inspected main implementation.
5. **Configuration/build hardening is needed.** Hooks install before configuration is read (lines 304–307). `std::stoi` has no local exception handling, and the successful path through the bool config reader lacks a return. No call-site byte/ownership check is visible at the hook-install call sites; the `CallDetour` implementation was not established in this review. The ZIP has no solution/project files and lacks included headers such as `RoughINIReader.h` and `Gathering_GameOSInput.h`, so it is not a self-contained build package as supplied.

Recommendation: retain this as an optional Step 6 donor, with explicit enable/disable behaviour and launch-state ownership. Correct the toggle/state issues before integration and verify first-person hip fire first. Keep current speed diagnostics isolated. No need to install this resource or obtain missing build files for packet 3B3.

## Earlier binary-only assessment

Local archive: C:/Users/regan/Desktop/NVO Mod References (Open Source)/Directional Shooting v1.1-92443-1-1-1751451693.7z
Archive SHA256: 99d847f8c23972402f9009750fb11fc92923c787ef14823e875606d9d0a7cd81

Archive contains only DirectionalShooting.dll, its PDB and DirectionShootingConfig/DirectionShootConfig.ini beneath DirectionShoot/NVSE/Plugins. The DLL is PE32 x86; SHA256 9de4734facfc7543c256262f1d625029b07905b11df96e166d0c2f84b0b2d960. A PDB supplies debug symbols, not C++ source. No source files were present in this archive, and no source download was advertised among the page's two files when reviewed. Full hook ownership and compatibility are unverified.

The supplied INI explicitly sets HipFireRectify=1, AimingRectify=1 and ThrowableMeleeRectify=1. The page's statement that aiming defaults off therefore differs from the supplied configuration. No settings were changed.

Author LOW / LowbeeBob describes player-only shot-direction correction toward the weapon, including hip fire, aimed fire and thrown melee; vanilla scopes and B42 True Optics are excluded. Requirements list xNVSE. Modification/use permissions are permissive; redistribution requires creator credit and commercial asset use is restricted. Preserve the author's notices if adopted. Source: https://www.nexusmods.com/newvegas/mods/92443 (reviewed 2026-09-15).

Design assessment (inference, not verified interoperability): promising optional weapon-behaviour component for later Step 6. It could establish the initial shot direction while NVO controls subsequent flight and damage. We must establish the order of direction correction, recoil/animation motion and spread so dispersion is not applied twice or overwritten. It does not replace NVO speed/drag/armour/injury systems or supply NPC aiming/AI threat evaluation.

A later minimal evaluation should begin with hip fire only, checking compatibility with the actual animation setup and the existing ShowOff/JIP/NVO launch path. Scoped aiming, throwables, shotguns, VATS and camera modes require separate consideration before broad adoption. Accurate C++ source would simplify the hook and math review. A separate optional module/config switch would preserve modularity. Do not install or start this work without a later user instruction.

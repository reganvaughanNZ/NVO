# Packet 4F - Material and target response definitions

Status: **prepared offline**. Native runtime remains 0.3.27 (327). No installation, GECK edit or gameplay test is required for this packet.

The purpose is to give every planned attack family an explicit place in the armour system before introducing damage authority. The new standalone `ResponseDefinitions` module selects and validates symbolic response definitions. It does **not** calculate protection, penetration, damage, wear, wounds or stagger. `DefinitionsOnly` is its best possible result, not permission to apply an effect.

## Delivered

- Eleven family contracts: ballistic, piercing, cutting, blunt, blast, laser, plasma, flame, external heat, electrical and EMP.
- Delivery is separate: projectile, individual pellet/fragment, melee, thrown object, explosion, pulse and continuous exposure. A thrown axe cannot inherit bullet stopping rules. Timing follows the accepted delivery.
- Separate worn-item, natural-protection and mechanical-structure definitions. Equipment policy and natural protection must be explicitly known. Empty inventory is never enough to classify a creature as unprotected.
- Authored region mappings and biological/mechanical tissue responses. A synthetic creature region 42 is used in checks to prove the selector does not force human limb numbering. This is not an actual bloatfly or robot mapping.
- Per-family construction/condition declarations and provenance. Missing response entries remain unresolved; cross-family and biological/mechanical substitutions reject selection.
- Bounded validation, all-or-nothing selection and standalone MSVC x86 checks. No hooks, engine reads, providers or new runtime dependencies.

Read [RESPONSE-DESIGN.md](RESPONSE-DESIGN.md) for the family matrix, material/target authoring rules, and how damage and stagger will share a later resolved component.

## Source and checks

Active repository source: `native/NVOCombatModel/ResponseDefinitions.hpp`, `.cpp`, `response_definition_tests.cpp`, `run_response_checks.cmd`. The release contains copies under `Source/`, not a second active implementation.

From the repository, run:

```bat
native\NVOCombatModel\run_response_checks.cmd
```

From an extracted release, run `Source\run_response_checks.cmd`. It discovers installed Visual Studio 2022/2026 C++ tools, compiles a standalone x86 executable with `/W4 /WX`, and writes results under `out-response/`. It does not build, load or install a game DLL. The optional packager is `tools/prepare_combat_4f.py`; it runs these checks afresh before copying evidence and verifies the manifest/ZIP.

All catalogue entries in the executable are labelled `synthetic.*` and `SyntheticFixture`. There are no actual armour/creature record bindings, production coefficients or measured physical constants in this packet. The 10,000 repeated selections check deterministic behavior, not game stress performance. Exact fresh results are in `Evidence/VERIFICATION.json` and `Evidence/CHECKS.txt`.

## Boundaries and next checkpoint

Packet 4E's keyword/exact-record coverage authoring remains unchanged. It does not automatically map to 4F definitions. A later reviewed binding will join exact record identity, coverage, construction and target profiles. A material label or armour slot cannot establish a struck surface or a layer order.

The original `ArmourModel` still has five numeric preview families; `ShadowAdapter` still admits only its tightly guarded kinetic evidence path. The new family enum must never be cast into those old arrays. Both modules remain offline. A successful 4F definition selection supplies none of the actual-hit evidence that adapter requires.

Before applying any future output: resolve component identity and attribution, exact contact/units, mapped anatomy, actual protection coverage, coherent condition state and layer order, complete modifier ownership and one engine application. Unknown evidence continues to hold interpretation. Custom equipment, anatomical mappings and special-weapon records need their own review; a lightning effect alone cannot classify the Tesla prototype.

Suggested next packet, subject to approval: connect the definitions to the disabled numeric preview, starting with a reviewed kinetic material/condition rule and separate tissue/structure outputs. Other family calculations stay explicitly unimplemented until their own inputs and rules are reviewed. Do not enable runtime damage or replace vanilla behavior as a side effect of that work.

## Reversal

Nothing was installed. Continue using the existing 4D runtime/4E authoring files; do not copy this packet into `Data`. The new module is not listed in either native DLL build definition. To discard the development packet, revert its new source and documentation changes in the workspace. No saves, load order, plugins or GECK records need changing.

## Dependencies and credits

No new runtime dependencies. Offline checks require the installed MSVC x86 toolchain; packaging uses Python's standard library. This module is original NVO code with no copied donor implementation. The root `CREDITS.md` and component notices are preserved in the release; existing mixed-project licensing is not replaced by this packet.

# NVO offline armour model — Packet 3N

Separate from NVOCombatCore. Not linked into its DLL. No NVSE/engine includes, hooks, file/console logging, mutation callbacks or application API. `Resolve` returns a would-be result only, and `kGameplayWrites` is always false. Fixture support does not make a family runtime-ready.

This first, deliberately simple model implements per-region layered kinetic stopping thresholds, distinct laser/plasma/flame/blast response entries, condition-dependent shielding, bounded transmitted blunt energy, normalized wear and authored HP/limb conversion. Kinetic thresholds are per construction (Ball/AP/HP/Pellet), and profiles must describe the actual matched ammunition. Diameter is validated metadata; it does not yet select or calculate material response. No incidence, tissue-depth, ricochet, ablation-history, fragment generation, critical engine effect or physiology simulation is claimed.

All coefficients in tests are **synthetic fixtures**, not production balance or measured armour. The model's linear condition rule and scalar stopping thresholds are provisional authored approximations. No populated game profiles or fabricated laser/plasma joules are installed. Flame uses dose rate times simulated duration; partition invariance assumes an unchanged armour snapshot. Damage/wear across evolving snapshots and burn scheduling are later coordinator responsibilities.

Unknown context, actor anatomy, body region, modifier ownership, contact calibration or relevant armour response rejects interpretation. Invalid/nonfinite/mixed-unit/overflow input returns an empty result with a reason, never a partially resolved hit. A zero incident input is valid and produces no wound; missing data is not encoded as zero. Mechanical targets cannot qualify for biological wound/payload flags.

Exact-once **engine** admission, component lifetime/deduplication, threading, serialization and applying effects remain outside this pure model. Repeated calls intentionally repeat the same preview. They are not additional hits, nor do these previews authorize gameplay. The current DLL remains native320. `run_checks.cmd` compiles a standalone x86 fixture executable only; there is no install target.

## Packet3O companion

AdmissionLedger.md describes the new offline bounded hit ledger and its separate run_admission_checks.cmd target (47 checks). It does not replace the pure-model45-check target or link either module into NVOCombatCore.

## Packet 3S companion

ImpactEnergy.hpp/.cpp adds a separate conditional energy-input checker. It is not linked into the DLL or converted into armour Threat inputs. Two generated BallistX profiles, 61 focused checks and a 19-contact diagnostic replay are recorded in source/combat/step3s. Rebuild with tools/prepare_combat_3s.py using the configured Python/VS toolchain. Current installed native323 remains unchanged; the earlier native320 reference above describes the original 3N checkpoint only.

Packet 3T settles the authored 70-units/metre convention and the parent projectile clock for the inspected path. Its source trace, 455 paired updates and 427-step production-integrator replay are in source/combat/step3t. It does not certify instantaneous contact speed or enable the energy module's damage authority. Native323 and all model code remain unchanged by that audit.

## Packet 4A companion

`ShadowAdapter.hpp/.cpp` adds the first typed bridge into the pure armour preview. It remains offline and is not linked into `NVOCombatCore`. The adapter requires verified hit/component/application identity, a verified engine path and mode, agreement between collision and hit-data regions, owned modifiers, a complete equipped-layer snapshot, an exact kinetic profile, an exact authoritative speed, calibrated units, and a verified target profile. Missing evidence returns a named waiting or unsupported result with an empty preview.

Valid speed intervals are represented but deliberately not collapsed to a midpoint or endpoint. The current 3U1 owned-step range therefore remains diagnostic and cannot enter `ArmourModel::Resolve`. Empty layers count as bare only after complete equipment and regional-coverage enumeration explicitly verifies the region as bare. Unknown worn armour cannot become bare skin.

`run_shadow_checks.cmd` builds a standalone x86 executable with `/W4 /WX` and runs 48 focused checks plus 10,000 deterministic preview repetitions. All profiles and coefficients in those checks are synthetic. There is no DLL, engine reader, runtime logger, install target, mutation path, or gameplay authority in Packet 4A.

# NVO code map

Read this alongside the current checkpoint in [STATUS.md](STATUS.md). This map describes the Packet 4E / native 0.3.27 snapshot.

## Native runtime

`native/NVOCombatCore/CMakeLists.txt` and `BUILD.cmd` enumerate the DLL's compiled sources. `include/` contains its interfaces; `src/` contains implementations.

| Area | Starting files under `native/NVOCombatCore/src/` |
| --- | --- |
| Plugin lifecycle and provider integration | `Plugin.cpp`, `NativeObserver.cpp`, `NativeLog.cpp` |
| Hit identity, observation, and transaction scope | `CurrentHit.cpp`, `DamageEvents.cpp`, `HitTransaction.cpp`, `ActorValueObserver.cpp` |
| Projectile flight and diagnostic contact evidence | `FlightPreview.cpp`, `FlightPhysics.cpp`, `FlightTiming.cpp`, `SpawnBoundary.cpp`, `Flight*.inl` |
| Guarded worn-armour reads | `ArmourSnapshotReader.cpp`, `ArmourSnapshot.cpp` |
| Exact origin, profile parsing, and coverage integration | `ArmourOrigin.cpp`, `ArmourCoverageConfig.cpp`, `ArmourCoverage.cpp` |

Tests and standalone runners are under `native/NVOCombatCore/tests/`. Runtime flight configuration is under `native/NVOCombatCore/config/`.

## Offline model and shared classification

`native/NVOCombatModel/` contains `ArmourModel`, `AdmissionLedger`, `ImpactEnergy`, `ShadowAdapter`, and `CoverageProfiles`, together with their fixtures/checks. Most are offline research modules. `CoverageProfiles.cpp` is also compiled into the current native DLL; the model and shadow adapter are not.

The model previews possible outcomes only. Its existence does not authorize runtime damage, wear, or stagger. Read the component README and headers for input contracts and rejection conditions.

## Armour authoring path

1. Edit reviewed definitions and bindings in `source/combat/step4e/profiles/armour-tags.json`.
2. `tools/resolve_armour_profiles.py` validates tags and resolves exact record profiles, using `compile_armour_coverage.py` and `generate_combat_4c_fixtures.py`.
3. Generated coverage JSON, TSV, and resolution reports live under `source/combat/step4e/generated/` in this checkpoint.
4. The runtime parser and classifier are the native coverage modules above. The current 4E TSV is byte-identical to the previously accepted 4D output; 4E does not introduce live keyword discovery.

Use a workspace output directory for new candidates. See the packet README for validation limits and exact-record exception rules. Synthetic check IDs are not game records.

## Foundation and history

`source/step1/` through `source/step7/`, `source/startup-delay/`, and the root script files hold alternative-start development material. `source/combat/step*/` records successive combat packets. Baseline subdirectories are historical copies, not separate active modules.

`tools/` includes both reusable validators and one-time preparation/install/review scripts. Inspect each script before use: many depend on existing local packets or absolute game/tool paths. `reference/` holds retained research and provenance, not runtime dependencies.

## Reading this with another AI

Provide the repository URL and ask the AI to read `AGENTS.md`, `README.md`, `CODEMAP.md`, and the top of `STATUS.md` before proposing changes. A local coding agent can clone the repository; a chat service needs GitHub/web access or uploaded files. Repository visibility alone does not give every AI a live connection or guarantee it has the latest commit.

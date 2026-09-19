# NVO code map

Read [README.md](README.md), [AGENTS.md](AGENTS.md) and the newest checkpoint in [STATUS.md](STATUS.md) before editing. Active implementation lives under `native/` and reusable tools under `tools/`; `source/combat/step*/baseline*` and packaged `Source/` directories are historical copies.

**Current source and installation: Packet 4J1 / native 0.3.31 / 331; live check pending.** See [the packet](source/combat/step4j1/README.md), [document assessment](source/combat/step4j1/DOCUMENT-REVIEW.md), [preparation receipt](source/combat/step4j1/Evidence/VERIFICATION.json) and [installation receipt](source/combat/step4j1/INSTALL-result.json). The installed pair matches the prepared hashes and 58 protected files are unchanged. The short [flame/9mm/reload check](source/combat/step4j1/TEST-NOW.html) still needs live review; recovery from the prior [4J flame-related flight fault](source/combat/step4j/LIVE-REVIEW.md) is not established by installation.

The [three-report research assessment](source/combat/step4j1/references/REFERENCES-REVIEW.md) preserves exact bindings and separate worn/natural/mechanical protection. Catalogue values, appearance-based coverage and unrelated animation-stack dependencies are not implementation facts.

## Native runtime

[`native/NVOCombatCore/CMakeLists.txt`](native/NVOCombatCore/CMakeLists.txt) and [`BUILD.cmd`](native/NVOCombatCore/BUILD.cmd) enumerate the DLL's compiled sources. Interfaces are under `include/`, implementation under `src/`, standalone fixtures under `tests/`, and runtime flight configuration under `config/`.

| Area | Starting files under `native/NVOCombatCore/` | Main check runner under `tests/` |
| --- | --- | --- |
| Plugin/provider lifecycle and flame-repeat identity | `src/Plugin.cpp`, `src/NativeObserver.cpp`, `include/NativeObserver.hpp`, `tests/ProjectileLifecycleTests.cpp` | `RUN-PROJECTILE-LIFECYCLE-CHECKS.cmd` |
| Flight admission and retained ownership | `include/FlightAdmission.hpp`, `include/SpawnCall.hpp`, `src/SpawnBoundary.cpp` | `RUN-ADMISSION-CHECKS.cmd` |
| Hit observation, generation and transaction scope | `src/CurrentHit.cpp`, `src/HitTransaction.cpp`, `tests/HitTransactionScopeTests.cpp` | `RUN-HIT-SCOPE-CHECKS.cmd` |
| Callback registration and emission | `src/DamageEvents.cpp`, `tests/DamageEventLifecycleTests.cpp` | `RUN-DAMAGE-EVENT-CHECKS.cmd` |
| Caller-route and actor-value diagnostics | `src/ActorValueObserver.cpp`, `include/DamageAttribution.hpp`, `tests/ActorValueAttributionTests.cpp` | `RUN-AV-ATTRIBUTION-CHECKS.cmd` |
| Copy identity and armour receipts | `include/CopyCapture.hpp`, `src/ArmourSnapshot.cpp`, `tests/CopyCaptureTests.cpp` | `RUN-COPY-CAPTURE-CHECKS.cmd` |
| Bounded worn-armour reads | `src/ArmourSnapshotReader.cpp` | `RUN-ARMOUR-SNAPSHOT-CHECKS.cmd` |
| Exact armour origin and coverage | `src/ArmourOrigin.cpp`, `src/ArmourCoverageConfig.cpp`, `src/ArmourCoverage.cpp` | `RUN-ARMOUR-COVERAGE-CHECKS.cmd`, `RUN-ARMOUR-COVERAGE-INTEGRATION.cmd` |
| Flight/contact observation and cleanup | `src/FlightPreview.cpp`, `src/FlightPhysics.cpp`, `src/FlightTiming.cpp`, `src/Flight*.inl` | Consult the affected packet; observer fixtures stub the actual physics/preview cleanup branches. |

Run these from the repository root with their full `native\NVOCombatCore\tests\` path. Read the runner first: several older scripts use a fixed Visual Studio path. Fixtures use synthetic inputs and do not load the DLL or install hooks.

### Recent diagnostic changes

- **4J1:** `NativeObserver.cpp` quarantines only positively matching observation-only flame repeats. Any retained/incoming admission claim, unknown identity or conflicting identity preserves the process fault. Ambiguous entries retain cleanup ownership while public lookup/current-hit association withholds their identity. `FlightPreview::EndSample` and `FlightPhysics::Event` skip fresh contact/travel interpretation during ambiguous cleanup. The preparation receipt records 83 production-observer checks with synthetic dependencies plus 35 pool/receipt checks; actual physics/preview cleanup received compilation and source review, not fixture execution.
- **4J:** `DamageAttribution.hpp` defines guarded caller windows and conservative carrier/flag labels. `ActorValueObserver.cpp` records route, original transaction context and pre-health argument matches independently. Provider-call nets can include nested activity and must not be summed. Call IDs and copy-attempt counts are not component/application IDs.
- **4I1:** `DamageEvents.cpp` performs bounded idempotent registration checks and records actual emission separately. `HitTransaction.cpp` queues scalar gap notices outside its lock. A positive registry query establishes membership; a negative result is ambiguous. Registration success does not establish provider emission.
- **4I:** `HitTransaction` creates generation/transaction/copy identity. `CurrentHit` carries one scope through armour observation, revalidates it, and forwards the original receipt to `FlightPhysics::HitQuery` / `FlightImpactJoin.inl`. A joined receipt can still be rejected, unsupported or omitted. `CopyCapture` is a diagnostic association, distinct from offline `ImpactBinding`.

Packet preparation tools are `tools/prepare_combat_4i.py`, `prepare_combat_4i1.py`, `prepare_combat_4j.py` and `prepare_combat_4j1.py`. They verify retained inputs and package evidence without installation. Historical pins and excluded local inputs can prevent a later checkout from reproducing a package; use the packet's receipt to understand its original scope.

## Offline model and shared classification

Active modules and their fixtures are under [`native/NVOCombatModel/`](native/NVOCombatModel/). Read the component README and headers for input contracts. Passing fixtures do not authorize runtime damage, wear or stagger.

| Module | Purpose | Runner in this directory |
| --- | --- | --- |
| `ArmourModel` | Provisional offline damage preview; `ArmourModel::ResolveKineticLayers` is the shared kinetic arithmetic. | `run_checks.cmd` |
| `AdmissionLedger` | Standalone admission accounting. | `run_admission_checks.cmd` |
| `ShadowAdapter` | Guarded offline identity/mode and kinetic-input admission. | `run_shadow_checks.cmd` |
| `CoverageProfiles` | Exact-record coverage classification; **also compiled into the DLL**. | `run_coverage_checks.cmd` |
| `ResponseDefinitions` ([4F](source/combat/step4f/RESPONSE-DESIGN.md)) | Eleven-family symbolic definitions with distinct delivery, tissue and protection owners. | `run_response_checks.cmd` |
| `MaterialPreview` ([4G rules](source/combat/step4g/MODEL-RULES.md)) | Offline kinetic bridge with condition curves and worn/natural/mechanical surface outputs. Other ten families remain unsupported here. | `run_material_checks.cmd` |
| `ImpactBinding` ([4H contract](source/combat/step4h/BINDING-CONTRACT.md)) | Independently captured evidence stamps must match before MaterialPreview version 2 performs arithmetic. | `run_binding_checks.cmd` |

`ImpactEnergy` contains additional offline energy research and remains outside the runtime DLL. The material runner also runs model, shadow and response-definition regressions. The [4H input audit](source/combat/step4h/INPUT-AUDIT.md) traces the remaining native producer gaps. Reserved exact-contact/at-impact kinds are contracts, not implemented providers. Do not cast the eleven-family enum or raw engine-region IDs into legacy model enums, or relabel cached evidence with current stamps.

## Armour authoring

1. Edit reviewed definitions/bindings in [`source/combat/step4e/profiles/armour-tags.json`](source/combat/step4e/profiles/armour-tags.json).
2. [`tools/resolve_armour_profiles.py`](tools/resolve_armour_profiles.py) validates tags and resolves exact records, using the existing coverage compiler/validators.
3. Write new candidate coverage JSON, TSV and resolution reports to a workspace output directory. Accepted historical outputs are under `source/combat/step4e/generated/`.
4. Follow [the 4E checkout instructions](source/combat/step4e/README.md) for commands and verification limits. The retained 4E TSV is byte-identical to the 4D output; this does not implement live keyword discovery.

Equip slots do not prove anatomical coverage, traversal order does not prove layering, and synthetic fixture IDs are not game records. The full historical Python replay runner needs an excluded local 4D capture log.

## Foundation, history and evidence

`source/step1/` through `source/step7/`, `source/startup-delay/` and root script files hold alternative-start development material. `source/combat/step*/` records successive combat packets. [`NVO-Implementation-Plan.md`](NVO-Implementation-Plan.md) distinguishes the original plan from the current checkpoint.

`tools/` includes reusable validators and one-time preparation/install/review scripts. Some require existing local packets or absolute game/tool paths; inspect prerequisites before use. `reference/` retains research and provenance rather than runtime dependencies. Raw logs, donor distributions, compiled game records and deployment archives are intentionally excluded; retained reports describe evidence without making a clean clone a complete game installation.

Preserve [CREDITS.md](CREDITS.md), component licenses and third-party notices. Record meaningful changes and precisely scoped validation in `STATUS.md`; do not rewrite historical evidence as if it were a new result.

# Repository publication verification — 19 September 2026

This update publishes the development work from Packet 4F through **Packet 4J1 / native 0.3.31**. During publication, the separate approved installation task recorded a successful 0.3.31 deployment in [INSTALL-result.json](../source/combat/step4j1/INSTALL-result.json), including 58 protected files unchanged. The short live test remains pending; recovery from the 0.3.30 flame admission fault is not yet established in-game.

## Fresh offline checks

The following existing runners were executed for this publication with MSVC x86 and strict warning checks. All **1,345 checks passed**, with zero failures.

| Suite | Runner | Passed |
| --- | --- | ---: |
| Projectile lifecycle | `native/NVOCombatCore/tests/RUN-PROJECTILE-LIFECYCLE-CHECKS.cmd` | 83 |
| Admission pool and receipt | `native/NVOCombatCore/tests/RUN-ADMISSION-CHECKS.cmd` | 35 |
| Hit transaction scope | `native/NVOCombatCore/tests/RUN-HIT-SCOPE-CHECKS.cmd` | 58 |
| Copy capture | `native/NVOCombatCore/tests/RUN-COPY-CAPTURE-CHECKS.cmd` | 44 |
| Callback lifecycle | `native/NVOCombatCore/tests/RUN-DAMAGE-EVENT-CHECKS.cmd` | 51 |
| AV attribution and ABI | `native/NVOCombatCore/tests/RUN-AV-ATTRIBUTION-CHECKS.cmd` | 98 |
| Armour snapshot reader | `native/NVOCombatCore/tests/RUN-ARMOUR-SNAPSHOT-CHECKS.cmd` | 452 |
| Impact binding | `native/NVOCombatModel/run_binding_checks.cmd` | 80 |
| Material preview | `native/NVOCombatModel/run_material_checks.cmd` | 108 |
| Armour model regression | Included by the material runner | 45 |
| Shadow adapter regression | Included by the material runner | 48 |
| Response definitions regression | Included by the material runner | 243 |

These are standalone synthetic fixtures. They do not establish in-game behaviour, real component/application identity, exact contact evidence, production armour balance, or performance under game workloads. The projectile lifecycle fixture stubs physics/preview dependencies; the actual cleanup implementations retain their previous compilation and source-review evidence, not fresh execution coverage here.

The publication checks did not rebuild, load, install, or test the plugin DLL in the game. The separate installation receipt above is distinct from these checks. Existing packet build manifests remain historical preparation records. The full historical Python replay suite was not rerun; it depends on excluded capture logs.

## Source and evidence integrity

- All 97 current source inputs and two baseline evidence inputs checked against the 4J1 verification record matched their recorded hashes and lengths before publication.
- All 113 inspected packet evidence, manifest, review and installation-receipt files remained unchanged after the fresh checks.
- `.gitattributes` preserves exact bytes under `native/`, `source/` and `tools/`, because automatic line-ending conversion can invalidate source fingerprints. Existing historical snapshots are not mass-reformatted.
- All 97 pinned native inputs were also checked against the staged Git blobs and matched. Four legacy Windows-encoded quotation marks in `STATUS.md` were converted to UTF-8 without changing their wording; the status file is now valid UTF-8 throughout.
- Verification output from this run remains in ignored native output directories. The table above records the observed results without rewriting frozen packet receipts.

## Repository contents

The update includes active source, tests, authored profiles, preparation/review/install tools, packet documentation and retained verification summaries. Authored Titans research and the source provenance inventory are included; these do not import donor code or assets.

Builds, DLLs/PDBs, game records, backups, packaged releases, raw logs and full user-report extracts remain local. Source-document receipts retain their historical fingerprints and may include local paths. Reference assessments distinguish unverified report claims from accepted native evidence. Excluded archive paths are not downloadable repository artifacts.

Some historical tools require the original game installation, local donor sources or archived captures. A Git clone is a source checkout, not a complete reproducible installation or deployment archive. No GitHub Actions workflow is claimed by this update.

# Guide for AI coding assistants

## Start here

1. Read `README.md`, then the newest checkpoint at the top of `STATUS.md`.
2. Read `CODEMAP.md` to locate the active implementation.
3. Read the relevant component and packet documentation before editing.
4. Preserve `CREDITS.md`, component licenses, and third-party notices.

This guide is shared project context for any AI that can read repository files. It is not tied to a particular AI vendor. It does not automatically connect an AI service to GitHub.

## Source of truth

Active C++ lives under `native/`. Active reusable development tools live under `tools/`. `source/` includes editable game scripts, authored data, fixtures, reports, and historical packet snapshots. Do not accidentally patch a historical `baseline*` copy instead of the active implementation. Older README files describe older checkpoints; use `STATUS.md` and current source/build definitions to resolve version differences.

At this snapshot, Packet 4E is prepared offline and the native core is 0.3.27. Update these navigation notes when the accepted checkpoint changes. A prepared build is not proof of installation or live acceptance.

## Engineering boundaries

- ArmourModel, ShadowAdapter, and ImpactEnergy remain offline; the coverage classifier is integrated into the diagnostic native core. Inspect `CMakeLists.txt` and `BUILD.cmd` for actual linkage.
- Preserve the existing disabled damage/stagger authority. Unknown evidence must remain unresolved; never turn missing data into verified bare skin, protection, or contact energy.
- Equip slots do not establish anatomical coverage, inventory traversal order does not establish layer order, and stable reads do not prove an atomic impact snapshot.
- Keep source preparation, offline checks, installation, and live acceptance distinct. Do not install into the game, launch/close game processes, change load order, or enable gameplay writes merely as part of a code edit. Obtain explicit user direction for those actions unless already authorized in the conversation.
- Fixtures and provisional coefficients are not measured physics or production balance. Preserve that distinction in code, tests, and documentation.

## Work and validation

Use the relevant existing check runners; read their scripts first because some toolchain and game paths are local. The DLL requires Windows/MSVC and a 32-bit target. Offline checks must not silently install or run a game plugin. Report precisely what ran and what remains untested; do not reuse historical pass counts as fresh test results.

After a meaningful change, update the affected documentation and record the new checkpoint/evidence in `STATUS.md`. Keep generated builds, original donor distributions, credentials, local tooling, and backups out of Git. Do not mass-reformat historical evidence.

The repository intentionally omits game plugins/records, raw logs, and local deployment archives. Some historical workflows need those local inputs and cannot run from a clone alone. Never fabricate missing files or claim a fully reproducible game installation.

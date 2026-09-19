# Guide for AI coding assistants

## Start here

1. Read `README.md`, then the newest checkpoint at the top of `STATUS.md`.
2. Read `CODEMAP.md` to locate the active implementation.
3. Read the relevant component and packet documentation before editing.
4. Preserve `CREDITS.md`, component licenses, and third-party notices.

This guide is shared project context for any AI that can read repository files. It is not tied to a particular AI vendor. It does not automatically connect an AI service to GitHub.

## Source of truth

Active C++ lives under `native/`. Active reusable development tools live under `tools/`. `source/` includes editable game scripts, authored data, fixtures, reports, and historical packet snapshots. Do not accidentally patch a historical `baseline*` copy instead of the active implementation. Older README files describe older checkpoints; use `STATUS.md` and current source/build definitions to resolve version differences.

At this snapshot, **Packet 4J1 / native 331 is installed; the short live check is pending**. See `source/combat/step4j1/INSTALL-result.json` and `TEST-NOW.html` in that packet. The approved DLL/PDB deployment and backup are verified, with 58 protected files unchanged and no game/GECK process launched or closed. The original 118-check receipt remains preparation evidence; `docs/REPOSITORY-VERIFICATION.md` separately records 1,345 fresh publication checks. Preserve qualified-flame quarantine, admitted ownership guards, cleanup-only ambiguous serials and process-fault persistence. Model/gameplay authority remains disabled and component/application identity unresolved. Next: review the flame/9mm-before-reload/9mm-after-reload capture. Do not reinstall or advance damage without the relevant direction and evidence.

The three additional reports are assessed in `source/combat/step4j1/references/REFERENCES-REVIEW.md`. Catalogue values remain unverified. The weapons report conflates NVO with an unrelated animation stack, so its dependency and load-order advice is excluded. Full report extracts stay local; assessments and receipts are versioned.

## Engineering boundaries

- ArmourModel, ShadowAdapter, ImpactEnergy, ResponseDefinitions, ImpactBinding and MaterialPreview remain offline; the coverage classifier is integrated into the diagnostic native core. MaterialPreview version 2 connects definitions to shared kinetic arithmetic with synthetic fixtures only. ImpactBinding's exact/at-impact producer kinds are reserved contracts, not implemented native providers; never relabel cached evidence with a current stamp. Do not cast response families or raw engine region IDs into legacy enums. Inspect `CMakeLists.txt` and `BUILD.cmd` for actual linkage.
- Preserve the existing disabled damage/stagger authority. Unknown evidence must remain unresolved; never turn missing data into verified bare skin, protection, or contact energy.
- CopyCapture is a native diagnostic key/receipt, distinct from offline ImpactBinding. Matching generation/transaction/copy/session establishes diagnostic association only. A joined receipt may still be rejected/unsupported/omitted; copy ordinals and transaction IDs do not establish component/application or committed damage. Preserve original producer scope and post-reader liveness checks.
- Callback registry query true is positive membership; false is ambiguous with competing handlers. Idempotent Set true means added/revived; false can mean an active duplicate. Neither proves provider emission. Preserve bounded main-loop checks, lifecycle cancellation and disabled gameplay writes. Copy-stage callback gaps are diagnostic hints, including legitimately omitted streams; never dispatch fabricated damage events to test registration.
- AV caller route, active HitMe context and pre-health argument matches are separate diagnostic witnesses. In-scope is not primary and unscoped is not automatically secondary. Provider-call net changes can include nested calls; never sum overlapping windows or pre-hit/pre-health/net values. Call IDs and copy-attempt counts are not component/application IDs. Keep absent metadata unknown and lifecycle generations distinct.
- Equip slots do not establish anatomical coverage, inventory traversal order does not establish layer order, and stable reads do not prove an atomic impact snapshot.
- Keep source preparation, offline checks, installation, and live acceptance distinct. Do not install into the game, launch/close game processes, change load order, or enable gameplay writes merely as part of a code edit. Obtain explicit user direction for those actions unless already authorized in the conversation.
- Fixtures and provisional coefficients are not measured physics or production balance. Preserve that distinction in code, tests, and documentation.

## Work and validation

Use the relevant existing check runners; read their scripts first because some toolchain and game paths are local. The DLL requires Windows/MSVC and a 32-bit target. Offline checks must not silently install or run a game plugin. Report precisely what ran and what remains untested; do not reuse historical pass counts as fresh test results.

After a meaningful change, update the affected documentation and record the new checkpoint/evidence in `STATUS.md`. Keep generated builds, original donor distributions, credentials, local tooling, and backups out of Git. Do not mass-reformat historical evidence.

The repository intentionally omits game plugins/records, raw logs, and local deployment archives. Some historical workflows need those local inputs and cannot run from a clone alone. Never fabricate missing files or claim a fully reproducible game installation.

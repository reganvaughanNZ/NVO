# NVO

A work-in-progress **Fallout: New Vegas** mod: an alternative-start foundation and a native combat research implementation built around projectile flight, explicit armour coverage and evidence-led damage modelling.

This repository contains development source and review evidence. It is **not an installable mod release**.

## Current progress

| State | Checkpoint |
| --- | --- |
| Current source and installation | **Packet 4J1 · native 0.3.31 / 331 — installed; live check pending.** Qualified observer-only flame repeats are quarantined without blocking unrelated flight admission. Genuine admission conflicts and unknown or changed identities still fault. |
| Installation evidence | [The 4J1 receipt](source/combat/step4j1/INSTALL-result.json) records the matching DLL/PDB pair installed and 58 protected files unchanged. The existing 4J kit is reused; no game/GECK process was launched or closed. |
| Next live checkpoint | A short flame tap and standard 9mm hits before and after reload, following [the installed-packet check](source/combat/step4j1/TEST-NOW.html). **No live 331 result is recorded.** Recovery from the prior 330 flame-related flight fault remains unverified. |
| Gameplay authority | NVO damage, armour wear and stagger remain disabled. The material/damage model remains offline; exact contact evidence, coherent impact state and component/application ownership are unresolved. |

The [4J1 preparation receipt](source/combat/step4j1/Evidence/VERIFICATION.json) records **118 passing offline checks**: 83 production-observer checks with synthetic dependencies and 35 admission-pool/receipt checks, plus 86 retained files unchanged and a clean x86 build. Those are the packet's original preparation results. Fresh checks for this repository update are recorded separately in [repository verification](docs/REPOSITORY-VERIFICATION.md). Actual physics/preview cleanup branches were compiled and source-reviewed; the observer fixture does not execute them.

Read [STATUS.md](STATUS.md) for the latest chronological evidence, [Packet 4J1](source/combat/step4j1/README.md) for the change and its limits, and [the 4J live review](source/combat/step4j/LIVE-REVIEW.md) for the earlier flame fault. The [three-report assessment](source/combat/step4j1/references/REFERENCES-REVIEW.md) records reviewed armour, creature and weapon research without importing unverified catalogue values or unrelated dependency advice into the mod.

## Start here

- **Contributors and AI assistants:** read [AGENTS.md](AGENTS.md), the newest entry in [STATUS.md](STATUS.md), then [CODEMAP.md](CODEMAP.md) to find active source and the relevant check runner.
- **Project direction:** [implementation plan](NVO-Implementation-Plan.md), [alternative start](NVO-Alternative-Start.md) and [background expansion](NVO-Background-Expansion.md).
- **Attribution:** [CREDITS.md](CREDITS.md) and component licenses/third-party notices.

Give another AI this repository URL and the reading order above. It still needs its own repository access or uploaded files; these guides do not automatically connect an AI service to GitHub.

## Recent development

Each packet retains its preparation and review records. Older packet README status statements describe that packet's original preparation; use the current checkpoint above and `STATUS.md` for later installation and live results.

| Packet | Main progress | Recorded scope |
| --- | --- | --- |
| [4F](source/combat/step4f/README.md) | Eleven attack-family definitions; separate worn, natural and mechanical protection/target profiles. | Offline symbolic selection only; no numerical or runtime damage authority. |
| [4G](source/combat/step4g/README.md) | Kinetic material preview with shared arithmetic, condition curves and distinct surface-loss owners. | Synthetic numerical fixtures; other ten families unsupported by this bridge. |
| [4H](source/combat/step4h/README.md) | Impact-evidence binding and MaterialPreview contract version 2. | Offline evidence gate; reserved exact-contact/at-impact providers remain unimplemented. |
| [4I](source/combat/step4i/README.md) | Native diagnostic copy identity and armour receipts, native 328. | [Three-hit copy association passed](source/combat/step4i/LIVE-REVIEW.md); a callback gap after reload required follow-up. |
| [4I1](source/combat/step4i1/README.md) | Bounded callback registration checks and lifecycle recovery, native 329. | [Three-hit/one-reload callback check passed](source/combat/step4i1/LIVE-REVIEW.md); the original cause and recovery branch remain unproven live. |
| [4J](source/combat/step4j/README.md) | Caller-route, transaction-context and pre-health diagnostics, native 330. | [Bounded route/callback pass](source/combat/step4j/LIVE-REVIEW.md); the flame-related flight failure led to 4J1. |
| [4J1](source/combat/step4j1/README.md) | Isolate qualified observation-only flame repeats while preserving ownership faults and cleanup, native 331. | Compiled, checked offline and installed; live recovery check pending. |

## Repository layout

| Location | Contents |
| --- | --- |
| [`native/NVOCombatCore/`](native/NVOCombatCore/) | Active C++ plugin source, runtime configuration, build entry points and native checks. |
| [`native/NVOCombatModel/`](native/NVOCombatModel/) | Offline model, response definitions, evidence binding and fixtures; the shared coverage classifier is also linked into the DLL. |
| [`source/`](source/) | Editable scripts, authored profiles, packet history, review reports and fixtures. Historical `baseline*` copies are not active implementations. |
| [`tools/`](tools/) | Reusable validators plus packet preparation, installation and evidence-review utilities. Inspect each script before running it. |
| [`reference/`](reference/) | Project research and provenance records. Original donor distributions remain local. |

Compiled plugins, game records, packaged releases, backups, downloaded tools, caches and raw logs are excluded. Historical reports/manifests may reference those local inputs; a clone does not reproduce the complete test archive or installed game. Some retained scripts and receipts contain machine-specific paths.

## Build and offline checks

The native DLL requires **Windows, MSVC with the x86 C++ toolchain, and a Windows SDK**. `BUILD.cmd` discovers Visual Studio 2022/2026. From the repository root in a command prompt:

```bat
native\NVOCombatCore\BUILD.cmd --no-pause
```

The DLL and matching PDB are written under `native/NVOCombatCore/out/build-*/`. The build does not install or load the DLL. The alternative [CMake project](native/NVOCombatCore/CMakeLists.txt) requires MSVC and `-A Win32`.

For the current flame-lifecycle packet:

```bat
native\NVOCombatCore\tests\RUN-PROJECTILE-LIFECYCLE-CHECKS.cmd
native\NVOCombatCore\tests\RUN-ADMISSION-CHECKS.cmd
```

For the offline impact-binding and material model:

```bat
native\NVOCombatModel\run_binding_checks.cmd
native\NVOCombatModel\run_material_checks.cmd
```

The material runner also checks the model, shadow adapter and response definitions. Native fixtures use synthetic memory and inert dependencies; they do not install hooks or run the game. Some older runners, including the admission runner, contain a fixed Visual Studio path that must match your installation. See [CODEMAP.md](CODEMAP.md) for other component checks.

Python authoring tools require Python 3. [Packet 4E](source/combat/step4e/README.md) gives separate checkout and extracted-package paths for shared armour-profile exports. Its historical full replay suite requires an excluded local capture log. Preparation/install scripts can also depend on retained local packages and evidence; they are not general-purpose setup commands.

## Credits and licensing

See [CREDITS.md](CREDITS.md) for attribution and source provenance. The starter repository's root [LICENSE](LICENSE) contains CC0; it does not supersede the GPL or other terms on included components and donor-derived material. Preserve component licenses and third-party notices under `native/NVOCombatCore/`. No new blanket license is assigned to this mixed project snapshot. Game files and original donor distributions are not included.

# NVO

Work-in-progress Fallout: New Vegas mod development: an alternative-start foundation and a native combat research implementation.

## Current checkpoint

Packet 4E prepares shared armour-profile authoring offline. The native combat core is version 0.3.27; the armour model and shadow adapter remain offline, and the new armour/damage/stagger authority is disabled. This repository is a development snapshot, not an installable mod release.

Read [STATUS.md](STATUS.md) for the latest checkpoint and [the implementation plan](NVO-Implementation-Plan.md) for the broader design. Older packet documents describe their own historical state.

For AI assistants and new contributors, start with [AGENTS.md](AGENTS.md) and [CODEMAP.md](CODEMAP.md).

## Repository layout

- `native/NVOCombatCore/`: C++ source, configuration, build entry points, native checks, and licensing notices.
- `native/NVOCombatModel/`: standalone offline model, coverage classifier, and fixture checks.
- `source/`: editable scripts, authored profiles, packet history, review reports, and test fixtures.
- `tools/`: Python and PowerShell preparation, verification, packaging, and installation utilities.
- `reference/`: project research notes and provenance records; downloaded donor code is excluded.
- Root Markdown files: design proposals, implementation plan, status, and credits.

Compiled plugins, game records, packaged releases, backups, downloaded tools, caches, and raw logs remain local. Some historical reports and manifests reference these excluded files; a clone does not reproduce the complete local test archive or installed game. Retained reports and scripts may contain machine-specific paths that need adapting.

## Building and checking

The native DLL requires Windows and a Visual Studio installation with the MSVC x86 C++ toolchain. From a command prompt:

```bat
native\NVOCombatCore\BUILD.cmd --no-pause
```

The build writes to `native/NVOCombatCore/out/` and does not install the DLL. Alternatively, configure the included CMake project for Win32. Read the component documentation before running a diagnostic build in the game.

Standalone checks live alongside each native component. Some check runners currently use a fixed Visual Studio path; adapt it to your installation. Python authoring tools use Python 3; see [Packet 4E](source/combat/step4e/README.md) and its profiles and checks for the current authoring workflow. Packet README commands can refer to packaged release layouts, so use the corresponding files under `tools/` and `source/` in this checkout.

Installation and packaging utilities can depend on the local game and previously prepared packets. Inspect their paths and prerequisites before running them; they are not general-purpose setup commands.

## Credits and licensing

See [CREDITS.md](CREDITS.md) for attribution and source provenance. The starter repository's root `LICENSE` contains CC0; it does not supersede the GPL or other terms on included components and donor-derived material. Preserve the component licenses and third-party notices under `native/NVOCombatCore/`. No new blanket license is assigned to this mixed project snapshot. Game files and original donor distributions are not included.

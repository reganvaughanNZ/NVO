# Packet 4B — guarded equipped-armour snapshot reader

Step 4B adds a bounded, read-only inventory reader to the existing exact JIP `CopyHitData` observation boundary. It records the exact worn `ARMO` instances found on a hit target, their raw equip-slot mask, record fields, and per-instance condition. It does not calculate protection or change damage.

## Purpose

Step 4A defined a pure armour model but deliberately refused to run without trustworthy engine evidence. Step 4B obtains one narrow piece of that evidence: which armour instances a supported target has equipped at the observed hit boundary.

The reader accepts only form type `0x3B` (`Character`). This covers ordinary human NPCs and non-feral ghouls represented by that engine type. Form type `0x3C` (`Creature`) is skipped before consuming the 64-snapshot humanoid sample budget.

## What it reads

For each supported target, the reader traverses `ExtraContainerChanges`, inventory entries, exact item-instance extra lists, `ExtraWorn`, and optional `ExtraHealth`. It records:

- exact call-local instance token and armour FormID;
- raw 20-bit biped equip-slot mask;
- base and current health plus an arithmetic condition ratio;
- raw armour rating, damage threshold, 32-bit biped flags, and armour flags.

Every pointer read uses the existing SEH-guarded byte reader. Traversals use fixed storage, hard limits, cycle/alias detection, a strict hash-probe bound, and two complete identical passes. Any unreadable, changing, aliased, contradictory, or over-limit graph rejects the entire snapshot; partial armour rows are never published.

## What it does not mean

Equip slots are not anatomical coverage, inventory traversal order is not armour layer order, and two stable passes are not an atomic impact snapshot. A complete inventory scan with zero worn armour is only `complete_no_armour_observed`; it is never promoted to verified bare skin.

Baked or toggled BIP/model geometry in an NPC record is visual/model state rather than a worn inventory instance, so this reader cannot treat it as armour. Bloatflies, feral ghouls, robots, yao guai, and other creatures will later receive explicit physiology and inherent-protection profiles for hide, shell, chassis, or natural armour. Step 4B intentionally does not guess those values.

The Step 4A shadow adapter is not called. Snapshot authority, coverage authority, layer authority, impact authority, armour preview, and every gameplay write remain disabled.

## Runtime and performance boundary

Observation occurs synchronously inside the already installed `CopyHitData` wrapper and only under a valid exact transaction scope on the main thread. The wrapper and all existing hook/patch sites are unchanged. At most 64 supported snapshots are attempted per load session and at most 32 armour rows are logged per accepted snapshot. Unsupported creatures are counted only in the final summary.

This diagnostic still scans a supported target's inventory twice. The work is strictly bounded, but a heavily loaded actor under automatic fire is the important live stress case. Before any always-on damage authority, NVO should move to an equipped-slot-directed lookup or a validated cache with explicit invalidation.

## Offline result

- Reader checks: 452 passed under x86 `/W4 /WX`.
- DLL build: x86 PE32, exactly `NVSEPlugin_Load` and `NVSEPlugin_Query`.
- New armour modules contain no patch API or model/damage linkage.
- Existing 3U1 patch-related source surface: 45 lines compared, zero differences.
- Preparation made no game changes. Installation is recorded separately below.

## Installed checkpoint

User approved installation. Native326 / NVO0.3.26 DLL and PDB are installed and hash verified, along with two optional console BAT text helpers. The installer verified53 protected files, including NVO.esm, the pilot ESP, configurations and activation lists. RD.esm remains absent. No process needed closing and the game was not launched.

Open START-HERE.html for the six-hit, one-reload test, copy buttons and reversal instructions. Runtime acceptance is pending; damage remains disabled. Helpers change test inventory/condition/health only when manually invoked by the user and are separate from the read-only native reader.

The original Source/NVOCombatCore snapshot and OFFLINE-CHECKS.json retain their preparation-time status deliberately. The top-level manifest and INSTALL-4B-result.json record the installed state.

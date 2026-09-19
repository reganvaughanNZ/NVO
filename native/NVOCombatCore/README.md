# Packet 4J1 — flame lifecycle isolation

Prepared native 0.3.31/331, not installed. Installed330 passed its bounded route/callback check but repeated flame creation notifications blocked subsequent custom flight. Positively matching, observation-only flame repeats now quarantine diagnostic identity without creating a new lifetime or blocking unrelated admission. Claimed admission, inconsistent/unknown/changed identity and other projectile repeats retain process-wide faults across reload.

NativeObserver retains raw cleanup ownership separately from public identity. FlightPreview/FlightPhysics suppress fresh ambiguous contact/travel interpretation while preserving impact stop and destruction cleanup. No damage, wear or stagger authority, new hook, dependency, profile or model linkage is added. Actual damage components/applications remain unresolved. Read source/combat/step4j1/README.md, DOCUMENT-REVIEW.md and the fresh Evidence/VERIFICATION.json. Production observer fixtures use synthetic dependencies; actual preview/physics cleanup is compiled and source-reviewed. Installation and live acceptance remain separate.

The following sections describe earlier preparation checkpoints.
# Packet 4J — damage route diagnostics

Prepared source is native0.3.30/330, not installed. Installed329 passed its bounded callback/copy checkpoint. ActorValueObserver now reports guarded caller routes, original transaction carrier/flag context and a real pre-health callback's match to its active AV call. Values before/after a call remain net observations, not unique damage applications. Nested windows are inclusive and non-additive. No total damage, component ID, deduplication authority or primary/secondary guess is fabricated.

DamageAttribution.hpp fingerprints three retained, manifest-verified engine call-setup windows. A failed/missing window produces an unclassified route and preserves the original call. MatchScope carries original scalar context with generation and copy-attempt counts; those counts do not bind a particular copy to an AV call. AV generation/counter cancellation now survives same-session reactivation and callback/getter reentrancy. See source/combat/step4j/README.md and SOURCE-TRACE.md. Fresh standalone suites are recorded by tools/prepare_combat_4j.py. Runtime hooks and assembly remain unchanged; damage/model authority stays disabled.

The following describes the retained callback and copy paths at their preparation checkpoints.

# Packet 4I1 — bounded callback survival diagnostics

Current prepared source is native 0.3.29/329. Installed native328 passed its copy-association check but lost both ITR callback streams after reload. 4I1 replaces remove/readd with bounded idempotent registration, positive-only public registry witnesses, separate first-emission rows, and lifecycle cancellation. A copied transaction missing either callback can queue a main-loop check; it never changes registry state inside the hit. No fabricated events or private ITR memory accesses are used. Registration success is not emission proof; the prior live cause remains unestablished.

See `source/combat/step4i1/README.md` and `SOURCE-TRACE.md`. `tests/RUN-DAMAGE-EVENT-CHECKS.cmd` exercises the production callback lifecycle with synthetic API/PE/form fixtures. `RUN-HIT-SCOPE-CHECKS.cmd` checks the transaction notice, and `RUN-COPY-CAPTURE-CHECKS.cmd` retains receipt regressions. The existing xNVSE6.4.8/ITR2.2.2 requirements remain. No new engine hook or damage/model linkage. Preparation is not installation or live acceptance.

The following describes the retained Packet4I copy path.

# Packet 4I — native diagnostic copy capture

Native0.3.28/328 passed its bounded copy-association checkpoint. CopyCapture.hpp defines a generation/transaction/copy/session key and scalar armour receipt. CurrentHit passes one scope through armour and current-hit observation; NativeObserver independently verifies identity and forwards the original receipt to the flight query. HitTransaction revalidates generation across unlocked reads and old-frame returns. No new hook or movement logic is added. This is diagnostic copy association, not a verified component/application or coherent impact snapshot.

See `source/combat/step4i/README.md` for log semantics, fresh evidence and deployment limits. `tests/RUN-COPY-CAPTURE-CHECKS.cmd` and `tests/RUN-HIT-SCOPE-CHECKS.cmd` exercise the changed production paths with synthetic stubs; `RUN-ARMOUR-SNAPSHOT-CHECKS.cmd` checks the underlying reader. No test loads the native DLL. MaterialPreview and its evidence/model modules remain offline. Damage, wear and stagger remain disabled. Preparation does not install the build.

The following describes the original 4B reader, retained for its contract and historical validation.

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
- No game, GECK, ESM, ESP, INI, save, or installed DLL was changed.

The compiled packet is prepared but not installed. Installation and the short live checkpoint require a separate approval.

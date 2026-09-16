# 3G2 /native317: read-only hit-context join

## Purpose and evidence

Native316 capture9a54c6410f44628130ff1e4db97af2a85184eb2422a9c288d5956983116f7bcf: shot1 contact exists before the first movement update; shot2 collision region0 versus current hit-data region1; shot3 both0 but candidate withheld for off-chord distance. User now suspects the VATS head aim may instead have struck torso. Neither the log nor this packet resolves visual landing or a universal VATS rule.

The supplied JIP ActorHitData layout stores hitLocation at+10. Its CopyHitDataHook copies the supplied0x64-byte record, saves hitLocation at+60 in the destination and may invoke critical-hit callbacks afterward. NVO's existing guarded CopyObserver samples the input then tail-calls that function exactly once. ShowOff's independent Projectile::ImpactData stores contact position+4 and hitLocation+24; its impact callback later moves the projectile to that contact. These establish distinct provenance, not the upstream engine rule choosing the differing regions. No copied-hit-data mutation is added. See ENGINE-FINDINGS.json for source hashes/lines.

The candidate appears before the current-hit input and the confirming impact callback follows it in the saved log. Waiting for that callback is unsuitable for a future damage decision already processing. Pre-damage authority remains future work; this observer is not claimed to be the eventual damage setter.

## Implementation

- HitQuery is an internal copied-scalar structure. NativeObserver calls ObserveHit only after its existing current actor/process validation and projectile lifetime lookup. It retains no game pointer in the query. Existing observer logic, CurrentHit.cpp wrapper and all original calls are unchanged.
- ObserveHit holds the physics lock with the existing error-state guard, checks active session/lifetime, and looks up the active projectile. Lock ordering is observer -> physics -> logger, already used for projectile events. The new helper calls no engine behavior or observer callback while holding physics lock; its only game access is existing guarded memory reads.
- FlightImpact.inl stores the already computed model status/speed/time in its private32-slot diagnostic record. The physics model and tolerances are byte-identical to316. No Track, actor, hit-data or projectile value is written.
- FlightImpactJoin.inl verifies projectile/source/weapon/ammunition IDs, reads fresh guarded contact data, requires matching target and stable single contact, and reports whether the cached model is available. It rejects stale/changed identity, target, contact, multiple contacts, missing reads, after-callback/stopped tracks and unavailable geometry. Hit-data region is never replaced with contact region; disagreement is explicitly counted. Joined model output is0 when unavailable and must not be interpreted as zero physical speed.
- Hit positions come from the already copied input with finite/range validation. Fresh contact positions are reported separately. Immediate contact before movement can report actual target/region but has no model. The ordinary no-sample impact callback now performs the same optional read to label pre_movement_contact rather than printing only unknown target. It remains unpaired with a movement sample; this does not fabricate collision timing.
- New join budget64 queries per load, max3 rows each and one summary, with explicit omissions/read/log failures. Combined extra impact/join detail bound416 rows, plus3 summary rows; existing global logger budget remains. Reset clears all new counters/cache state. No new console message, native hook, shared record mutation or dependency.

## Checks

Offline C++ harness uses the actual model/cache/join code with captured engine reads stubbed. Native316 actor samples preserve one valid candidate808.438545 m/s and one unavailable off-chord result. Checks cover region disagreement without overwriting either region; wrong identity/target; changed contact; late callback; untracked projectile; immediate/multiple/unreadable contact; join limit/reset; existing32-lifetime coverage/omission/duplicate handling; and seven original model invalid-input guards. Source hashes identify the exact replayed code. These are not live engine or gameplay tests.

Static packaging verifies unchanged model/drag/CurrentHit source, controlled additions to physics/observer/header, native PE32 DLL and matching PDB, expected two exports, version317 and unchanged nine physics hook bridges. Sixteen baseline files remain byte-identical. Complete source/diff and donor notices included.

## Installation and reversal

The prepared transaction replaces only NVOCombatCore.dll/PDB, after backing up the316 pair and checking deployment dependencies. All current records/configuration/activation are protected. User has authorized closing the game if needed. No assistant game launch or GECK operation.

To reverse, close New Vegas and restore both files from the backup listed in INSTALL-3G2.md, originals/Data/NVSE/Plugins, into the matching game folder. This returns native316; retain NVO.esm, NVOFlightPilot.esp and existing masters/configuration/saves.

Review the short user317 capture before advancing. The separate PRE-DAMAGE-REVIEW.md defines the authorized Ultra review; it has not run. Unit calibration, mass/energy, immediate-contact speed policy, region producers and actual pre-damage integration remain prerequisites, not silently completed features.

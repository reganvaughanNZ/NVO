# Packet 3G: collision observations before armour inputs

## Why the callback's last speed is insufficient

The accepted 3F3 capture, lifetime 8, reports a collision step with 1,740.10254 engine units added to the travel counter while the projectile position advanced only 287.051876 units. That collision step is deliberately excluded from free-flight verification, so the stored accepted velocity remains the speed at the start of the collision step. Neither the full-step mean nor that stored speed is a direct contact-speed measurement.

ShowOff's OnProjectileImpact handler dispatches at its hook near 0x009C20C9, after updating projectile position from the first ImpactData position. The reviewed log shows damage callbacks preceding this event. Therefore the packet observes contacts at NVO's existing BeforeAccounting collision branch, then correlates the later event. It adds no new engine hook and does not take damage authority. Relevant donor file hashes and the earlier logged example are in ENGINE-FINDINGS.json.

## Isolated implementation

New private source FlightImpact.inl is included after the unchanged integrator in FlightPhysics.cpp. Its fixed arrays hold diagnostic data for the existing first eight logged physics lifetimes. Four small calls reset state, sample the existing collision branch, observe the existing event, and summarize/clear the cache on suspend. Removing these calls and the include reproduces the native 314 FlightPhysics.cpp exactly. No existing Track field or flight branch is changed; nine assembly bridges are compared after compilation.

The collision helper receives const Track and a const accounting-vector pointer. It reads the exact projectile/vtable/base/source/weapon identity, position, age, distance, impact byte and first contact record. It does not call engine functions or write projectile, actor, controller, request, collision, damage or Track data. Native ownership locks already held by the caller serialize its private cache. Callback observations occur synchronously before existing retirement for that p/serial. Memory-read failures affect diagnostics only and cannot reject or stop physics.

Validity bits: 1 = identity, 2 = position/age/travel/impact state, 4 = list head/next read, 8 = first contact target/position/material/region, 16 = accounting vector. Complete collision snapshots have mask31; complete callback snapshots have mask15. Unknown fields are zero or region-1 with their validity bit unset. Only the first contact is read; a non-null next pointer marks multiple/ambiguous contacts. Contact region is the engine's reported integer, not a precise organ coordinate.

## Candidate model and limits

The helper logs the entire collision step: start position, proposed displacement, actual projectile position, first contact point, raw accounting vector, initial and proposed end velocity, dt and flight-model inputs. It projects contact position onto the proposed segment to calculate progress, without interpreting the full travel counter as contact distance.

A candidate is considered only for a complete, single-contact snapshot with a point inside the proposed segment, contact-to-segment and projectile-to-contact distances within the existing position tolerance, an already verified baseline, and an NVO-applied step. A collision during the initial unchanged engine segment is labelled engine_baseline_contact and yields no candidate. Multiple contacts, invalid reads and mismatched geometry are recorded rather than guessed.

For eligible steps, 24 bounded bisection iterations solve for partial flight time using the unchanged RK4 integrator on local velocity copies. Endpoint velocities must project forward along the proposed segment. Fraction times full dt is not assumed correct under drag. The resulting partial position must also match contact within the unchanged tolerance. Success is labelled model_estimate_only and records candidate time/speed; all rows retain contact_time_measured=0 and speed_authority=0. The existing assumed unit scale is reported as uncalibrated. This is a candidate under the current model, not an engine timestamp or permission to apply armour/damage.

At most eight collision snapshots produce four detail rows each. The first impact callback per sampled lifetime produces at most one callback row, including missing-sample cases. A collision later destroyed without a matching callback can produce one additional ending row. Duplicate events count in summaries without repeated detail. Total extra detail is bounded by48 rows/load, with the unchanged global7168-detail/1024-priority limits. Optional interpolation performs at most25 local integrator evaluations per eligible collision, with the existing dt<=0.25 bound (at most60 substeps each). No new console messages or per-frame logging is added.

Callback correlation requires matching sampled lifetime identity, contact target/region, single-contact lists and stable contact coordinates within tolerance. No timing or target guess is used when these differ. Candidate/geometry and callback evidence must both be reviewed before any future interface publishes a usable impact speed. A candidate alone is not accepted automatically. Destruction without a callback and missing/changed contact cases remain explicit diagnostics.

## User checkpoint and next boundary

Use the ordinary Hunting Rifle with standard .308. First hit a large solid object from very close range outside VATS, then hit a live target at a normal distance, then another live target farther away in VATS. Choose a clear line of sight without buildings in the shot path. Allow three seconds after confirmed impacts; if a shot misses, make at most one replacement for that check. Wait20 seconds after the final shot and exit. No required reload or other weapon cycle.

Review evidence must cover the first-step limitation, a correlated later-step impact, raw collision distance versus full-step displacement and the candidate's stated status. It may reveal an unresolved contact representation or timing case; do not silently convert an estimate into authority. Unit calibration, cartridge mass/energy, material penetration, ammunition tuning, armour wear and injuries are later work. Preserve accepted 3F3 terrain/range checks; no new miss-reproduction loop.

## Installation and reversal

The installer verifies the current native314 pair and protected dependencies, backs up both files and the existing log, replaces only DLL/PDB, and verifies other files unchanged. It can close the exact game under the user's prior permission. No game launch or assistant gameplay occurs.

To reverse, close New Vegas and restore both NVOCombatCore.dll and NVOCombatCore.pdb from the recorded backup's originals/Data/NVSE/Plugins directory. This returns native314. Keep current records, configuration, masters, activation and saves.

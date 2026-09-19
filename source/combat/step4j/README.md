# Packet 4J — native component and application diagnostics

Prepared native **0.3.30/330, not installed or live accepted**. The last accepted checkpoint remains Packet 4I1/native 0.3.29/329: its three-hit, one-reload callback/copy check passed. Packet 4J gathers evidence needed to investigate direct hits and secondary effects. Primary/secondary labels and component/application identities remain unresolved.

## Purpose and observed evidence

The existing actor-value observer now records three independent observations around its provider call:

| Observation | What it establishes | What it does not establish |
| --- | --- | --- |
| Engine caller route | A known return address, compatible actor-value argument and matching code-window fingerprint identify an observed `health_helper_call` or `hitme_condition_call`. | A damage family, primary/secondary effect, unique component or committed application. |
| Active HitMe transaction context | Matching receiver/source, main thread, valid initial data and current session/generation associate the call with the original transaction's scalar metadata. | An atomic impact snapshot or ownership of all effects observed during that call. |
| ITR pre-health argument match | The active, untainted health call received a callback with the same receiver/source and finite negative requested delta. | Final damage after callbacks, a single storage write or committed health loss. |

Unknown callers, incompatible arguments, unavailable bytes and fingerprint mismatches stay `unclassified_call`, with an explicit witness reason. No route is guessed from an explosion flag, projectile type, callback count or nearby log row. Carrier kind is limited to the observed form category; an unfamiliar carrier remains `other` or `unresolved`.

The matched transaction metadata retains its original generation, lifetime, carrier, weapon, ammunition, flags and critical-effect reference presence. Changes to current hit data do not rewrite entry context. `explosion_flag` reports only the initial flag bit; `critical_effect=reference_present` reports only a reference. Neither means that an effect was applied. Without a matching transaction, these fields remain unavailable or unknown.

## Reading the log

`AV_ATTRIBUTION_BEGIN` accompanies the existing `AV_APPLY_BEGIN`. Join them by session and AV call ID, retaining the attribution generation. The attribution row distinguishes `context`, `route`, `route_witness`, transaction generation and initial hit metadata. `copies_seen` counts copy-stage attempts, including rejected attempts. It does not bind this AV call to a particular accepted copy.

`AV_ATTRIBUTION_END` accompanies `AV_APPLY_END`. `scope_retained=1` requires the same matched transaction ID, session and generation at the end. `health_callbacks` counts matching pre-health argument observations; `callback_mismatches` keeps rejected observations separate. The observer reads only the three immutable callback argument slots and never reads or writes the mutable multiplier slot.

The before/after AV difference remains a measurement over the entire provider-call window. An enclosing call may include nested activity: `net_kind=inclusive_nested_window` makes that explicit. **Do not add nested and enclosing net values, pre-hit inputs, callback counts or copy counts as damage.** The attribution end row retains `additive_net=0`; both attribution rows retain `component_verified=0`, `application_verified=0` and `primary_or_secondary=unresolved`. A valid numerical window can coexist with unresolved attribution.

`AV_ATTRIBUTION_SUMMARY` reports scoped/unscoped calls, verified/unresolved route observations, matching/mismatched pre-health callbacks and callbacks without a current AV frame. These are diagnostic counts. Zero or absent callbacks do not prove that no damage or continuing effect occurred.

## Bounds and unchanged authority

The existing AV hook and provider chain are retained. The observer samples finite negative health requests (AV 16) and condition requests (AVs 25–31), with a maximum depth of 16 and 96 detailed calls per session. Attribution adds two rows to each detailed call, for four AV rows total. Each recognized route checks one fixed code window of at most 41 bytes. These are work bounds, not measured timing results.

Lifecycle generations cancel stale observations and prevent old continuations from changing a new session's counters. Nested continuations still return through their original callers. Foreign-thread calls pass through; invalid reads, identity changes, tainted frames and unsupported routes remain explicit failures or unclassified evidence.

No new engine hook, dependency or model linkage is introduced. Damage, armour wear and stagger authority stay disabled. MaterialPreview and ImpactBinding remain offline; exact contact speed, coherent impact state, component/application ownership and committed damage remain unfinished.

## Preparation evidence

See [SOURCE-TRACE.md](SOURCE-TRACE.md) for route provenance, [REVIEW.md](REVIEW.md) for the interpretation limits, and [Evidence/VERIFICATION.json](Evidence/VERIFICATION.json) for the actual fresh check counts, compiler/binary inspection and source-preservation results. Standalone production-code fixtures use synthetic memory and stubs; they do not execute the game or establish live acceptance. Earlier unchanged checks are not fresh results for this packet.

Preparation read `FalloutNV.esm` only to verify the base-game forms in the optional inventory kit. [Evidence/TEST-KIT-FORMS.json](Evidence/TEST-KIT-FORMS.json) records that read-only check and the master hash. No game files were written, no game or GECK process was launched or closed, and no native DLL was loaded or installed during preparation.

## Proposed installation and user check

Installation requires separate approval after review. The proposed deployment is the reviewed `NVOCombatCore.dll` and matching PDB, plus optional `NVOComponentKit4J.txt` in the game root, with fresh installed-state validation and backups. No ESM/ESP, dependency, configuration or load-order change is proposed.

After installation, load the saved test setup and use a living target for each sample. If supplies are needed, the optional console command `bat NVOComponentKit4J` adds a 9mm pistol, 50 standard 9mm rounds, three frag grenades, a flamer and 100 flamer fuel to the player. It changes inventory only when the user runs it; preparation does not execute it. The kit does not set up a target or perform attacks.

1. Land one standard-9mm pistol torso hit on a living target.
2. Throw one frag grenade near a living target and let it detonate.
3. Use one very short flamer tap on a living target, then wait three seconds unpaused for any continuing effects.
4. Reload the saved setup and land another standard-9mm pistol torso hit on a living target.
5. Report completion for log review.

No VATS, GECK or stress test is required. Review will compare these observations and the reload boundary without assuming that each attack produces a fixed number of callbacks or applications. Missing or ambiguous evidence stays unresolved. This check can establish usable diagnostics within its observed scope; it cannot by itself establish actual damage identity or enable gameplay authority.

Reversal after an approved installation restores the backed-up DLL/PDB pair together while the game is closed. Restore the prior kit file if one existed, or remove the deployed kit if it was newly added. The installation record must retain that prior-presence distinction. The build and check runners do not perform installation or reversal.

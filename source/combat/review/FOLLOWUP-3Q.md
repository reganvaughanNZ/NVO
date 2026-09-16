# Native 322 / Packet 3Q follow-up

The frozen Ultra-317 pre-damage decision remains **HOLD**. This is a focused implementation follow-up, not a replacement independent review or live acceptance.

## Change and evidence

317-07: private projectile selection now follows reservation of both physics (128) and lifecycle (512) slots. Selection has one owner at the guarded ShowOff continuation. The previous pre-create selector is removed. Capacity refusal leaves the supplied base unchanged, with no eviction. A verified creation receipt binds identity; the exact engine return commits physics. Null return without a create event cancels both tickets. Pool ownership and monotonic identities reject reused, stale and foreign tickets.

Compiled Win32 native 322 without warnings; matching DLL/PDB. The final binary's wrapper copies sixteen argument words, calls Prepare, forwards once, settles and returns the saved engine pointer. Prepare changes only argument zero after a valid dual reservation. The forwarding routine pushes sixteen words, calls once and cleans 64 bytes. Existing movement bridge, integration equations, drag data and damage-observer sources are unchanged outside the capacity/lifetime integration.

35 checks exercise production pool and receipt primitives, including bounded capacity, rollback, reset, stale/cross-pool identity and omitted logging. 19 ABI/receipt checks also pass. These do not execute the installed DLL or prove the complete native coordinator. Source changes, added production header/tests, build evidence and identity hashes are retained in the packet.

## Ownership, locks and failure

The observer owns life slots; physics owns flight slots. Reservation/settlement hold observer ownership before subordinate locks. Spawn preparation and settlement release the spawn lock before calling the observer. No lock is retained across the original engine continuation. The exception-finally path only latches an atomic fault and restores TLS scope; it does not acquire locks or repair game objects.

After a post-selection mismatch or physics rejection, further substitutions are blocked for the process. The rejected flight gets no additional NVO movement edits, while valid committed flights may continue. Current private projectile state is left to the engine. This is **not** stock trajectory restoration, reversal of displacement or guaranteed preservation of integrated velocity. Ambiguous reservations remain bounded until lifecycle cleanup. Reload clears transient bookkeeping but does not clear the process fault.

## Still required

- User check: ordinary pistol, VATS rifle, automatic burst, actual flight time and reload. Inspect commitment, retirement and fault counters.
- Later actual overload, exceptional cancellation, reentrancy/thread and fault evidence. Offline pool exhaustion is not live NPC saturation.
- Units/contact-energy authority, authoritative damage application, actual hit-region policy and separation of diagnostic limits from damage authority remain open prerequisites.
- No armour, health, limb, biological injury or medicine replacement is enabled by this packet. Unknown equipment keeps its existing path.

Follow the packet README for acceptance; missing evidence is not a pass. No broad performance or crash-free claim is made.

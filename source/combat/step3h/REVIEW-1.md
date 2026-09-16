# Packet 3H / native318: live diagnostic checkpoint passed

2026-09-16. The prescribed two rifle hits and punch after one reload all completed the new entry/copy/return observation. This passes Packet 3H's narrow diagnostic checkpoint. The pre-damage gate remains **HOLD**; no damage replacement is enabled and no further gameplay repetition is needed for this checkpoint.

## Preserved evidence

Capture: [NVOCombatCore.log](captures/2026-09-16-3H-e8d6c57f37f9/NVOCombatCore.log), 46,550 bytes, SHA-256 `e8d6c57f37f94a6ef93975ebede002bcea145824d5a8aff85e3ab2024d2968f5`. Last write 2026-09-16 00:01:26.439162 +12:00. Two identical reads with unchanged size/time were checked before archiving. `capture.json` preserves the user report, prescribed sequence and interpretation limits. Both `tools/audit_flight_capture.py` and `tools/audit_hit_transactions.py` completed successfully against the archived hash; their results are `audit.json` and `transactions-audit.json` in the capture folder. `review-data.json` records additional sequence/value checks.

## Observed sequence

| Call | Session | Recorded hit | Entry health input | Later requested health delta | Evidence lines |
|---|---|---|---:|---:|---|
| 1 | Initial load | Hunting Rifle, standard .308, torso 0 | 52 | -104 | 60-73 |
| 2 | Initial load | Hunting Rifle, standard .308, head 1 | 104 | -208 | 110-123 |
| 3 | After one reload | Unarmed, torso 0, no projectile/ammo | 2.75 | -5.5 | 175-185 |

The ordinary-shot/VATS-shot interpretation comes from completion of the prescribed sequence; the log itself does not tag VATS firing mode or selected aim. Actual head/torso hit and projectile-contact regions agree for both bullets. That does not resolve the earlier316 discrepancy for every route.

All three calls record: entry before ITR -> ITR pre-hit -> copy of the exact same input pointer with matching identities/process -> ITR pre-health -> provider return. The three process-wide call IDs are distinct and continue across the reload. Each has one pre-hit, one copy, one pre-health and one return. No tainted, invalid, open, overflowed or unscoped transaction; no omitted stage rows or log failures. This confirms earlier identity availability for the observed calls, not one committed damage application.

Both rifle entries retain the creation ammunition and distinct projectile lifetimes 1/2. The engine reused projectile reference FF001994 after its first destruction; the observer matched the second lifetime correctly. The punch uses lifetime0 and unknown/no ammunition rather than inheriting the rifle's identity. All hits are player00000014 to actorFF001978 on the main thread through site0089A738. The other five entry sites, nested/off-thread work and diagnostic exhaustion were not exercised live; prior mock ABI/capacity evidence is separate.

Two projectile creates, two impacts and two destructions reconcile. Both session summaries have no unmatched events, reused-live-address errors, overflow, read failures, open projectile lifetimes or movement mismatches. A successful reload and normal-exit event are logged. This is not proof about every possible crash path or events after the exit log.

## Limits and audit disposition

Both bullets collided in the first unchanged engine movement segment (`engine_baseline_contact`). The zero applied steps and `lives_without_update=2` therefore reflect this short-range case; no NVO impact-speed candidate was accepted or exercised. Do not turn unavailable speed into zero energy or call this a new flight-model validation. Prior movement/terrain evidence remains unchanged.

The later requested health deltas are exactly twice the entry health fields for all three calls. This corroborates a downstream change in these inputs, but does not identify its cause or measure final HP loss. The event remains `scope_only`, `cause=unclassified`, `committed_loss=unverified`. Return acknowledges completion of the provider call, not completion/count of health and limb writes. No duplicate damage application is established by this capture.

Ultra finding317-01 has progressed: the earlier full-input observation and exact-pointer handoff are confirmed on this route. Its terminal-application/downstream-scaling requirement remains open. Findings concerning actor speed, units/mass, first-segment policy, region semantics, diagnostic-independent gameplay coverage, admission/fallback and record damage ownership remain open. Do not repeat the full Ultra audit or activate armour/damage from these counts.

## Proposed next packet

Prepare the separate foundation record repair identified by the audit: correct the actual RD bootstrap and old-only JIP checks; make a deliberate plan for RD's inherited Player record while preserving the user's five health GMSTs and all required startup references; document migration or exclusion of the Brahmin Baron extra damage handler before coordinated damage. Full RD master removal requires proper reference migration, not deletion of the file/header. This is a proposal awaiting the user's go-ahead, not an installed repair.

Continue the final-application and model/region contracts before implementing coordinated damage. Review only affected changes thereafter. This review changed evidence/checkpoint documents only: no DLL, game files, ESM/ESP, profiles, activation or saves; no assistant gameplay or GECK work.

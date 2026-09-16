# Step 4B stress capture review

**PASS for the bounded automatic-fire/enlarged-inventory checkpoint.** User gameplay; no assistant gameplay test or game changes.

Pinned capture `LIVE-4B-STRESS-20260916-235307.log`, SHA256 `555081337821fb407cb29afa59ca98b86f174766b2a108d1e1675b8849ad7ace`.

| Evidence | Before reload | After reload |
|---|---:|---:|
| Standard 9mm SMG projectiles | 90 | 8 |
| Target hit transactions | 87 | 8 |
| Complete stable armour snapshots | 64 | 8 |
| Inventory entries in every snapshot | 137 | 137 |
| Worn items in every snapshot | 2 | 2 |
| Intentionally omitted snapshots after cap | 23 | 0 |
| Reader rejections / instability / scope errors | 0 | 0 |

The 128 distinct added MISC records increased the earlier nine-entry inventory to137. Body00020420 and helmet00020426 were present in all72 snapshots. The loop stayed bounded at64 attempts in session1 while transaction accounting continued to87;23 later qualifying snapshots were intentionally omitted. Reload reset the budget and produced eight fresh complete snapshots. The user fired eight rounds after reload rather than roughly five; this is adequate and needs no repeat.

One startup banner, one save reload and normal process exit. All98 projectiles had create/impact/destroy accounting, with zero lifecycle/admission/read faults, zero movement mismatches or unpaired movement accounting, and no open lifetimes. Hit transaction entries/returns balance95/95. Three first-session projectiles did not produce a target damage transaction. The final sampled target health after reload is99969.9844; no target death is shown.

Impact diagnostics separately count17 and5 unpaired callbacks. Every one is explicitly `pre_movement_contact`, with no movement observation yet, not an armour-reader failure. Those contacts remain non-authoritative for speed under the existing Step3 contract. Broader diagnostic detail omissions after caps are intentional. No claim that all impact-speed cases are solved is made.

All14 pinned foundation/helper hashes match; RD.esm is absent. All snapshot, coverage, region, speed, armour-preview and damage-write authorities remain zero. This evidence establishes only this bounded diagnostic workload:137 entries, one humanoid and72 sampled scans. No per-scan timing exists, and the user has not supplied smoothness/stutter feedback. It does not certify exact overhead, the512-entry maximum, many-NPC concurrency, NPC-to-player consistency or uncapped production performance.

Next proposal, requiring user approval: Step4C explicit coverage/target-profile classification in preview only. Distinguish semantic body-region protection from raw equip slots, handle unknown equipment conservatively and preserve creature/natural-protection separation. Full damage remains HOLD, including exact speed and modifier-ownership requirements.

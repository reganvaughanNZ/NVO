# Packet 3C5 / 310 - reload regression reviewed

**Two reloads passed the observed cleanup and reinitialization checks. The reported VATS session verifies one edited 9mm free-flight segment; edited rifle free flight in VATS remains unobserved.** Repeating steps 2 and 3 did not invalidate this capture.

Archive: `source\combat\step3c5\captures\2026-09-15-3C5-484a826a0db9\NVOCombatCore.log`. SHA256 `484a826a0db979cd8323a6110e6be2257fd135b250f881c2414f7a3f8e689a4d`, 135,530 bytes, 600 lines. Source last write 2026-09-15T16:04:17.4867269+12:00. Normal exit. `tools/review_combat_3c5_regression.py` verifies this immutable capture and writes the detailed comparisons in review-data.json. The VATS label for session 3 comes from the user's completed-instructions report; the log does not explicitly identify VATS mode.

| Session | Context | Rifle applied / verified | 9mm applied / verified | Controller pairs |
|---|---|---:|---:|---:|
| 1 | Scenery, initial load | 3 / 2 | 10 / 9 | 15 |
| 2 | Scenery, repeated after reload | 4 / 3 | 10 / 9 | 16 |
| 3 | Live targets, reported VATS after second reload | 1 / 0 | 2 / 1 | 5 |

All six lifetimes have one unchanged baseline and one final collision segment. All 24 edited free-flight comparisons match. Maximum logged edited-vector error is 0.00755284822 units; maximum tolerance fraction 0.134921. All six baseline comparisons match too. Each final collision segment is deliberately excluded from free-flight verification, explaining the applied/verified difference.

All 36 movement/accounting/controller/reset observations pair. Baselines retain the original local-Z reset, and all 30 edited requests preserve the submitted vector at the guarded reset branch. No reported rejection, mismatch, read/identity error, unpaired accounting, concurrent address reuse, overflow, nesting/overlap, invalid timing or log cap. The three sessions each have two creates, impacts and destructions, with no open lifetimes at either reload or exit. Reinitialization arms the same restricted pilot scope. The final session has two linked actor hit contexts with known ammunition and two hit/two health callbacks; those callbacks do not independently prove single damage application. Damage replacement stays disabled.

## Remaining evidence gap

The final rifle (lifetime 5) has one unchanged baseline followed immediately by an edited collision segment. Its guarded local-Z preservation executes, but there is no PHYSICS_ACTUAL row for an edited free-flight segment. The final 9mm (lifetime 6) has one matching edited free-flight segment before its collision. This establishes limited 9mm movement evidence, not every VATS trajectory or critical/armour rule.

Rifle collision-boundary candidate Z is -305.188477 versus intended -360.377746, about 55.19 engine units apart. It is not a verified free-flight match, and this review does not attribute the correction to a particular engine mechanism. The collision boundary also has a nonzero current delta. The next observation must distinguish pre-contact flight from collision/target adjustment; do not dismiss this row as proof of exact collision-path physics or use it to validate impact energy. The rifle's guarded caller input remained intact.

Keep build 310 installed. Propose only one farther-away live-target VATS torso shot with the private hunting rifle, with sufficient travel for an edited free-flight segment. Ask before giving the next checkpoint. No additional pistol or reload repetition is needed. If a longer shot still shows no usable free-flight observation, investigate that path instead of repeatedly asking for the same test. No wider ammunition, tracers, damage or armour work is accepted by this review.

Archived/reviewed evidence and updated checkpoint documents only. No native edits, rebuild, install, game launch, gameplay, GECK work or process-memory access.

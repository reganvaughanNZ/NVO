# Packet 3E playtest review — accepted

2026-09-15. The user completed the test and clarified that the second .44 VATS shot missed and that the distance changed. No repeated test is required for this checkpoint.

Archived log: `captures/2026-09-15-3E-9a8b6287ee09/NVOCombatCore.log`. SHA256 `9a8b6287ee098f0037562c30a85e349e658efac6a7b8ccb746a8c422b0a8e0ba`, 198,093 bytes, 851 lines, last write 18:26:03 +12. The adjacent `capture.json` and `review-data.json` retain capture metadata and numerical results.

## Flight and reload evidence

The expected native build 311 / 0.3.11 / phase3D loaded all nine profiles. Packet 3E changes configuration and private records, so this native version is correct. Two loaded sessions, one reload, six shots and normal exit were recorded. The selector was ready and bound in both sessions. Every selection was corroborated by the actual created private projectile, source projectile, weapon and ammunition.

| Session | Lifetime | Weapon | Verified edited free-flight segments | Impact target |
|---|---|---|---:|---|
| 1 | 1 | 10mm Pistol | 4 | 00106B5E |
| 1 | 2 | .357 Magnum Revolver | 5 | 00106B5E |
| 1 | 3 | .44 Magnum Revolver | 5 | 00106B5E |
| 2 | 4 | .44 Magnum Revolver | 3 | Live actor FF001978 |
| 2 | 5 | .44 Magnum Revolver | 22 | 00107B8E, no linked actor hit |
| 2 | 6 | .44 Magnum Revolver | 6 | Live actor FF001978 |

The middle post-reload shot agrees with the reported miss. Its 22 verified flight segments remain useful flight evidence. VATS use and the distance change are user context; the log has no direct VATS-mode flag.

All six baseline segments match. There are 57 paired controller/accounting/local-Z calls and 51 applied segments: 45 verified edited free-flight segments and six collision exclusions. No selector/preview skips, rejected or mismatched tracked steps, unpaired calls, unmatched lifetimes, live-address reuse, overflows, remaining pending/open state, read errors or detail caps were logged. Untracked movement/accounting counts are zero.

Maximum edited-vector error is 0.00871941167 game units, at most 0.169863357 of the unchanged native tolerance. Maximum position error is 0.00000762939453 game units; this is within tolerance. Maximum intended-versus-precontact-candidate error is 0.00872028562 game units. Collision segments are excluded from free-flight verification.

## Hit interpretation and limits

Lifetimes 4 and 6 link to actor FF001978 using .44 weapon 0008F215, ammunition 0002937E and carrier FF001737. There are two pre-hit and two pre-health callbacks. Recorded health/base context values of 36 and 144 are engine-stage observations, not proof of final health loss or duplicated damage. NVO damage replacement remains disabled throughout.

Accept the limited standard-ammunition expansion to these three weapons and its reload/VATS checkpoint. Prior 3D1 acceptance remains valid. This does not validate special ammunition, other weapon mappings, precise impact energy or a future damage calculation. The initial unchanged segment, game-unit calibration and earlier collision-only discrepancy remain recorded limitations before armour authority. The assistant reviewed files only; gameplay was performed by the user.

Keep packet 3E installed. The separately approved reversible game-folder cleanup is now complete; see reference/game-cleanup-20260915/RESULT.md. Retain RD.esm until its references are migrated, and ask before preparing another combat packet.

# One-shot recheck: trailer collision; terrain correction still unexercised

The shot passed its ordinary movement checks but hit a mobile-home trailer after0.157 seconds. There were no failed terrain queries, so this test does not validate the3F2 correction. No further manual aiming repeat is requested; propose a controlled test position before continuing.

Archived log: `captures/2026-09-15-3F2-61b25ed13fb3/NVOCombatCore.log`, SHA256 `61b25ed13fb3accf597e3dcd8166fc76f43801a309fa136dbc43e843d1d69822`,28,583bytes/131lines, last write2026-09-15T20:22:06.127542+12:00. Native313/phase3F2, one loaded session, one shot, no reload, normal exit. User reported completion after RECHECK-1; the log does not directly establish aiming mode.

## Findings

- Correct standard .308 identity at selection and creation: Hunting Rifle00004333, ammo0006B53C, private projectile0C000807.
- One verified baseline and four independently checked edited movements. Six paired movement/accounting calls, six local-Z reset observations, final collision excluded from free-flight comparison.
- Five eligible terrain queries, all successful. Zero corrections, displacement mismatches, stopped-track errors, identity failures, overflow or open lifetimes. One matched creation/impact/destruction sequence and no linked actor hit.
- Initial trajectory was about2.497 degrees downward, with vertical velocity-37.0223m/s under the current donor scale. It was not the roughly level, unobstructed trajectory needed for this observation.
- Impact reference001070C1 is vanilla REFR using STAT000928F3, editor ID`MobileHomeASNV`, mesh`vehicles\MobileHomeASNV.nif`. Its placed position is(-67640,-2280,8104). No matching reference/base override was found in RD.esm, NVO.esm or NVOFlightPilot.esp. This identifies the same reference struck by the earlier misses.

The reference lookup is saved as `impact-reference.json`; `tools/review_combat_3f2_recheck.py` verifies the log and writes `review-data.json`. No game, native source, configuration, record or activation file changed. No assistant gameplay was performed. Damage authority remains off.

## Proposed next action

Ask for approval to prepare a small controlled test-position fixture above the local obstructions, with a defined position and shallow trajectory, so the next shot has a reproducible opportunity to exercise missing-terrain handling. Explain how to use and reverse the fixture on the test save. Keep native313 unless a separately justified change is needed; do not broaden logging, relax movement tolerances, or declare success simply because no error was printed.

Before choosing coordinates/commands, verify the applicable worldspace, placement, player control/aim behavior and projectile lifetime limits. Do not invent a teleport target or promise that a trajectory must invoke the branch. The fixture is proposed, not built or installed in this review. Wait for the user before preparing that next step. No further blind aiming retries or HP/ammo-cycle tests are requested.

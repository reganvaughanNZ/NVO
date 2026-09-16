# Range and lifetime: evidence and limits after the repeated 3F2 test

This is a read-only source/log investigation. No executable or game configuration changed. The user declined a fixed-position fixture; do not build one.

## Established observations

1. In capture `d456dd06d026`, lifetimes 17-20 ended without impact callbacks at 1.344-1.360 seconds and 53,013.9-53,406.6 engine units travelled. Their `FLIGHT_PREVIEW` rows report `range_setting=53000`.
2. In original 3F1 capture `77ebadbd30fd`, the user-confirmed VATS miss failed at about 5.846 seconds and ended at about 8.023 seconds / 265,154 units. This is approximately five times the current base range, but numerical agreement alone does not establish a multiplier or its owner.
3. `native/NVOCombatCore/src/FlightPreview.cpp` reads the base projectile range at base + 0x6C. Its `range_setting` field does not represent a separately observed instance limit.
4. Supplied donor source `C:/Users/regan/Desktop/NVO Mod References (Open Source)/JIP-LN-NVSE-main/nvse/GameObjects.h` declares `Projectile::distTravelled` at 0x110 and `Projectile::range` at 0x14C; it asserts a Projectile size of 0x150. This is a source lead, not proof of which engine paths consume the instance field in the installed build.
5. Authenticated runtime disassembly at `source/combat/step3b2/timing-investigation/runtime-20260915-102703/projectile-disassembly.txt` shows calls to 0x00508070 and 0x00979260 followed by float comparisons in the projectile update route (for example near 0x009B807D-0x009B8093). The helper bodies are outside that saved region. Their names/semantics have not been established here.

## Limits

- Final-shot destruction is consistent with range expiry; the exact cause was not logged.
- The latest final four shots' aiming mode is not explicitly logged or user-confirmed. Following an outside-VATS instruction is not direct telemetry.
- A longer VATS instance range is plausible, not a verified five-times rule.
- Stewie's source reference to `g_fVATSWeaponTargetRangeMultiplier` concerns weapon target acquisition and does not prove projectile lifetime handling.
- Previously observed on-disk executable bytes differ from authenticated loaded code. Do not substitute them for absent runtime helper bodies.
- No failed query occurred in the newest run. Absence of errors does not verify the correction's write/verification path.

## Next diagnostic scope, pending approval

Verify the instance range field and relevant range handling against supplied source and trustworthy engine evidence, then consider logging the instance limit alongside existing create/destruction observations. Keep output bounded and on disk. Do not change flight rules, range, damage, record ownership or correction tolerances just to make the test reach the branch. Define another gameplay checkpoint only after understanding the lifetime constraint; do not request another blind retry.

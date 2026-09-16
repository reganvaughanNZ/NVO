# Firing-range observations (native 314 / packet 3F3)

Do not interpret Projectile +0x14C as the firing lifetime limit merely because some source layouts name it `range`. Authenticated saved code compares that field in a passing-sound path (0x009BF0BB), then operates on the sound at +0x128 and the played flag at +0x148.

Observe Projectile +0xD4 instead. Stewie calls it `fRange`; ITR uses that offset as range. Saved firing code initializes it at 0x009BDD10 and conditionally multiplies it at 0x009BDDB5-0x009BDDC0. The referenced GMST 0x011CE5F4 is `fCombatIronSightsRangeMult`, corroborated by JIP and Stewie setting maps. NVO's previous `range_setting` field is base projectile +0x6C, not this instance field.

Evidence is pinned in source/combat/step3f3/ENGINE-FINDINGS.json, referring to the saved runtime-20260915-102703 capture. No new process capture or engine-code distribution was needed. This supersedes the 3F2 review's tentative +0x14C range lead. Do not claim a universal VATS multiplier or exact destruction cause from that earlier hypothesis.

Native 314 adds optional D4/C8/90 reads after the existing sampled lifetime and snapshot identity checks. Failures affect diagnostic counters only. FLIGHT_RANGE logs current/creation range, base range, travel, age, raw flags and impact context at creation/first impact/destruction, capped at 96 attempts per load plus the existing global detail cap. FLIGHT_RANGE_SUMMARY records unavailable optional reads and log failures. A range_reached result is only a numerical comparison; every row retains cause=unverified.

The helper tools/audit_flight_capture.py collects these rows and checks identities. Gameplay review must compare launch and final range, selected ammunition, mode reported by the user, terrain-query outcomes and actual movement accounting. No blanket acceptance follows from clean counters alone. All flight/terrain/damage behavior remains at native 313 rules pending that review.

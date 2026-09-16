# 3G1 review: boundary correction observed; preserve unavailable cases

The corrected diagnostic produces a valid model candidate for shot2 and correctly retains unavailable cases for the close rock contact and shot3. Both actor hits correlate to their projectile lifetimes and later contact callbacks. No movement mismatch or tracking leak appeared. This accepts the diagnostic correction within the observed scope, not physical speed calibration or damage/armour authority.

## Evidence

Capture `captures/2026-09-15-3G1-9a54c6410f44/NVOCombatCore.log`, SHA256 `9a54c6410f44628130ff1e4db97af2a85184eb2422a9c288d5956983116f7bcf`, 60,867 bytes /256 lines, last written2026-09-15T22:19:16.270465+12:00. Stable across two reads. Native316/0.3.16/phase3G1, one loaded session, no reload, normal exit. The audit validates the archive hash, identities and detailed movement vectors; review-data.json retains independent geometry comparisons. A separate read-only source review corroborated the findings.

The user reports1 rock,2 VATS headshot,3 live torso shot at the same distance. The two actor checks were performed in the reverse order to the page, which does not invalidate their evidence. Shot3's aiming mode is not explicitly stated and the log does not prove it. Do not demand a repeat simply to restore instruction order.

All3 shots are player Hunting Rifle00004333, standard .3080006B53C, private projectile0C000807. Creation, selection, impact and destruction identities agree for all3. Both actor hits targetFF001978.

## Shot results

| Shot | Result | Speed diagnostic |
|---|---|---|
|1|Rock contact00122F8F; no movement/accounting entry|Unavailable: contact already present before first timed update|
|2|Hit-data region1 (head), user-reported VATS headshot|Model estimate808.438545 m/s, inferred partial time0.00431042584 s|
|3|Hit-data region0 (torso), critical flag set|Unavailable: contact lies outside the accepted chord tolerance|

For shot1, contacts_before=1 and state_before=1 on the first timed update (lines40-41). Both life and travelled distance initially remain zero; movement/accounting entries are zero. The paired accounting path that calls ImpactCollision never runs. Its one unpaired callback is therefore an immediate-contact coverage case, not evidence of lost tracking. The existing no-sample branch prints target=unknown without reading the contact; the ordinary impact event already supplies the rock reference. Speed cannot be reconstructed from zero travel/time counters or claimed to be zero. The observed instance range is zero for this immediate contact; it is not evidence of general range failure.

For shot2, the endpoint and accounting comparisons pass with errors0.00867344 against tolerance0.05208549. Perpendicular contact offset is0.021771916. Partial integration ends0.0371457212 units from contact, also within tolerance. The estimate lies between the step's start810.993109 and full-step end802.156262 m/s; inferred time lies within the0.0150000006-second step. The later callback has the same target, raw contact region and exact contact coordinates. This is a supported model estimate for this observed collision; units remain uncalibrated and no exact engine contact timestamp is measured.

For shot3, both endpoint/accounting checks pass (error0.00592806, tolerance0.0532246123). The contact's perpendicular distance0.0710916499 exceeds that tolerance by approximately0.017867. The partial-time solver therefore does not run. The later callback confirms unchanged contact. The log does not explain that offset. Do not widen tolerance, substitute last velocity, or describe it as a failed movement update merely to obtain a candidate.

## Body-region and timing distinction

Shot2's IMPACT_STEP and IMPACT_CALLBACK carry contact region0, while its linked HIT_CONTEXT carries hit-data region1. Shot3 has0 in both. The head/torso names follow the prior3B3A mapping and agree with the user's report. The raw contact region cannot be substituted for the hit-data region when selecting helmet versus torso armour. This discrepancy is not proof of a damaged record or a universal VATS rule; the producers still need a bounded source audit.

Ordering matters: shot2's model is logged at136, HIT_CONTEXT at141 and confirming callback at146. Shot3 follows224,229,234. A future damage resolver cannot wait for the later callback before authorizing damage already being processed. Both snapshots should be preserved and joined by lifetime plus target/source/weapon/ammo, with the collision candidate's availability explicit. A hit-data region read at this observer is still an input snapshot; do not claim final damage application or universal anatomy correctness from it.

## Accounting and decision

All11 movement/accounting entries balance:2 verified baselines +7 verified applied movements +2 applied collision exclusions. Detailed rows cover all9 ordinary verified movements. No rejects, mismatches, unpaired movement accounting, invalid contexts, optional read failures, duplicate impact callbacks, log failures or open lifetimes. All3 diagnostic lifetimes were admitted, none omitted. Impact summary has2 samples,1 candidate,1 unavailable candidate,3 callbacks,2 correlated and1 unpaired (rock). The separate baseline-contact count is0 because the rock never entered the sampled movement path. The legacy lives_without_update=1 is explained by that immediate contact.

This short test does not exercise the32-lifetime cap, reload or failed-terrain correction. Their previous evidence remains recorded separately; do not expand this pass claim to them. Source/configuration/gameplay files remain unchanged during review, native316 stays installed, and no assistant game/GECK operation occurred.

**Next proposed packet3G2:** inspect the existing collision-query and body-region producers using available sources/captures, then add a read-only joined collision/hit-context diagnostic at the existing hit observer. Keep contact region and hit-data region distinct, classify immediate contacts, and retain unsupported geometry without fallback. This prepares the armour inputs and clarifies what is available at the actual hit-processing point. Do not enable damage changes or add native hooks without a demonstrated need. No repeat of this unchanged test is requested. Ask before preparing/installing that packet.

Physical unit calibration, mass/energy, first-segment ownership and the actual pre-damage integration remain prerequisites for later armour authority. Preserve the accepted3F3 terrain/range findings; RD master removal and HP ammo-selection persistence remain separate work.

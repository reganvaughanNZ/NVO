# Packet 3K live-log review

Verdict: useful live net actor-value evidence; reload checkpoint incomplete. No native or game files changed during review.

Capture: 564895 bytes, SHA256 ef0816806766c462238da95b359ee2a1cb852f49276da9f359f459e285f921fa. Two identical reads archived this log. Native319, new_game session1 followed by normal exit; no pre/load/post-load events.

- 197 observed AV entries and 197 returns; open=0, invalid=0, depth_overflow=0, nested_calls=0, log_failures=0. This is call observation, not a count of independent hits or internal engine writes.
- Detail limit reached normally at96 calls:48 health and48 body-condition observations. All96 detailed rows match a synchronous hit transaction and source/receiver identity, with no taint. All are player-origin 9mm Pistol000E3778 / ammo0008ED03, on11 target references. Do not infer later weapon coverage from capped rows.
- All48 detailed health net changes match the requested pre-ITR delta within floating-point precision. They are twice the earlier hit input. This establishes the factor in observed HP change for these samples; it does not establish the cause, implicate NVO, or prove an exhaustive single-write path.
- Two condition samples establish why request and applied change need separate fields: calls94/96 requested-510.333405/-204.133347, but their current values moved100->0 and damage components0->-100. Other94 detailed AV changes agree with requested values within0.001.
- Conditions25,26,27,28,29,30 observed; no creature remapping or incoming player health sample in detailed rows. Later health samples include a target already below zero HP, so these are not all live-target survival measurements.
- The6796 other_thread_passthrough count covers any AV dispatch on other threads; the observer checks thread before filtering AV or delta. It is not6796 known missed health hits. These calls are deliberately unmeasured.
- Existing hit scope counters:104 entries/104 returns, no invalid/overflow/unscoped stages. Physics reports no movement/accounting mismatches, no failed boundary queries, no open state. Limited-detail first-contact speed candidates remain unavailable in this capture; no new flight authority claim.

No repeated stress or broad test needed. Remaining compact checkpoint: load a saved game, land one ordinary Hunting Rifle/standard .308 torso hit on a living human, reload that same save once, land one unarmed punch on a living human, then wait20 seconds and exit. This fills the absent save boundary and avoids exhausting the detail budget. Do not change the installed build. Continue to hold damage activation; identify the factor-of-two scaling and resolve the existing Ultra317 units/mass/contact/admission and separate damage-owner findings before enabling damage.

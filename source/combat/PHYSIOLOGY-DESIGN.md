# Physiology design direction — discussion, not implementation

User direction, 2026-09-14: keep the proposed wound/physiology ideas, but accommodate the gameplay loop. Build around the existing powerful New Vegas medicines as they are. Healing should remain simple.

Retained ideas: armour determines the injury reaching the body; wounds have engine-reported region, type and severity; bleeding, pain and impaired limb function have consequences; biological and mechanical anatomy use different profiles; preserve attacker attribution and later save/load persistence; apply consistent rules to player and NPCs. Exact internal-organ coordinates are not available and must not be claimed.

Latest constraint takes precedence over added medical complexity: preserve familiar medicine roles and existing strength, timing, skill interactions, drawbacks and normal/Hardcore distinctions. Do not implement new items, rebalance medicine or require a separate treatment minigame on this discussion alone.

Recommended approach, still a proposal:

- Stimpaks remain normal combat recovery. Recognized treatment should address ordinary NVO wounds alongside the existing healing effect.
- Existing Super Stimpaks are the first candidate for the previously discussed advanced emergency-healing role. No new mandatory advanced-stimpak item is approved. Do not infer additional limb restoration in Hardcore mode.
- Doctor's Bags and Hydra remain the familiar limb-treatment tools. Match NVO structural impairment to actual recovered limb condition so a restored limb is not blocked by an invisible injury flag.
- Preserve Med-X's existing protection and the specialist roles of radiation, poison and addiction treatments. Additional pain-suppression behaviour is undecided.
- Blood loss and pain should produce understandable consequences through familiar health/limb feedback. Ordinary healing must not leave a contradictory hidden fatal blood deficit at visibly restored health. Exact physiological recovery mapping remains undecided.
- Distinguish medicine from food, rest and other health sources when mapping effects to wound recovery. Do not make every positive health change cure every injury.
- One appropriate Aid-item use should automatically treat its corresponding problems. Serious injury should generally create a reason to find cover, treat and decide whether to continue the expedition.
- Balance danger through incoming damage, exposure and resource decisions. Medicine retains its usefulness; do not make routine injuries require prolonged downtime.

Read-only reference check: FalloutNV.esm contains Stimpak/Super Stimpak health and condition effects, Super Stimpak debuff, Doctor's Bag/Hydra limb effects, Med-X damage resistance, and radiation/poison/addiction treatments. This establishes base-record roles only; winning overrides and effect conditions must be checked during the actual medicine packet. No record or runtime change was made.

Implementation remains in the later wounds/medicine packet after native damage observation and armour decisions are validated. Current checkpoint stays packet 2B3 awaiting user capture. No compile or gameplay tests were performed for this design discussion.

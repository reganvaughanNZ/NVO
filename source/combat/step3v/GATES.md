# Step 4 and damage-activation gates

## Gate A — read-only Step 4 shadow work

**Status: allowed for a future packet; not implemented by Packet 3V.**

A shadow adapter may connect validated runtime observations to the existing pure `NVOCombatModel` only if all of the following remain true:

- it cannot write health, limb condition, armour condition, inventory or continuing effects;
- it cannot suppress or replace the engine damage path;
- every prediction records input validity and rejects ambiguous attacker, target, weapon, ammunition, region or armour context;
- approximate contact speed is labelled as a range or unavailable, never presented as exact energy;
- collision region and `ActorHitData` region remain separate fields;
- unsupported equipment produces no NVO prediction and keeps full engine behavior;
- shadow diagnostics use bounded storage that is independent of any future gameplay ledger;
- diagnostic logging can be disabled or buffered before performance testing.
- a post-selection fault cannot leave an ambiguous private-projectile path; latch lifetime and rollback behavior are explicit.

## Gate B — wider bullet-profile coverage

**Status: closed until authored and checked.**

Each additional weapon/ammunition pairing needs an explicit cartridge and projectile mapping, barrel or launch context, fallback behavior and a recorded compatibility decision. A caliber guess alone is insufficient. AP, HP and other special construction require material interaction rules in addition to flight values.

## Gate C — NVO damage authority

**Status: HOLD.**

All conditions below are required before any live damage replacement:

1. One verified engine application boundary with attacker, target, source, weapon, ammunition, collision and modifier context.
2. Exact-once ownership, including pellets, VATS, criticals, explosions, continuing effects and NPC-to-NPC hits.
3. A documented difficulty and modifier order that prevents double scaling.
4. A tested region policy for live fire, VATS misses, redirected hits and collision/`ActorHitData` disagreement.
5. A gameplay ledger whose correctness does not depend on diagnostic cache capacity or log delivery.
6. Explicit armour instance, helmet/body coverage, material and condition inputs with fail-closed behavior.
7. Attacker attribution and save/load persistence rules for continuing injuries.
8. Reload, transition, exception and reentrancy cleanup evidence.
9. Production stress evidence using real concurrent projectiles and multiple actors.
10. A reversal switch that restores the complete engine path without leaving partial state.
11. Post-selection fault, nested call, foreign-thread and exception behavior with unambiguous rollback or retirement.

## Gate D — other weapon families

**Status: future family packets.**

Laser, plasma, flame, explosive, thrown, melee and shotgun/pellet behavior must enter through explicit adapters. Every adapter needs family-specific semantics and a full stock fallback. Explosive impact and explosion are separate events; robots and biological actors need distinct injury outcomes; poison requires a penetration or delivery rule appropriate to its source.

## Gate E — activation review

Before the first damage-enabled build, repeat an independent source and evidence audit against the exact build candidate. The review must confirm that no diagnostic estimate has been promoted to authority, every new hook has a named owner, and the safe fallback remains reachable.

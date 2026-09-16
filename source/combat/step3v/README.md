# NVO Combat Packet 3V — Step 3 closure audit

Packet 3V is a review-only packet. It freezes the NVO 0.3.25 source, configuration and evidence used to decide how much of Step 3 can close. It does not build or install a DLL, change `NVO.esm`, alter the game folder, or request another gameplay test.

## Decision

Step 3 closes for the **explicitly profiled bullet-flight and diagnostic foundation**. The accepted scope is limited to the nine `select_on_fire` profiles listed in `CHECKS.json`. It covers exact profile admission, bounded projectile ownership, motion integration, collision observation, actor/reference identity preservation, world/reference classification, cleanup and stock fallback.

Step 3 does **not** establish damage authority. Exact contact speed and energy, armour interaction, body-region authority, VATS/critical policy, committed damage, injury, and unsupported projectile families remain outside the accepted scope. All gameplay damage continues through the existing engine or mod path.

The existing offline `NVOCombatModel` armour resolver and admission ledger may support a future read-only Step 4 shadow adapter. No such adapter is implemented or authorized by this packet.

## Read in this order

1. `AUDIT.md` — decision, evidence and practical limits.
2. `SCOPE-MATRIX.md` — what each weapon or projectile family currently does.
3. `GATES.md` — conditions for shadow work and eventual damage activation.
4. `FINDINGS.json` — machine-readable findings.
5. `INDEX.json` — SHA-256 inventory of reviewed source and evidence.
6. `CHECKS.json` — assertions derived from the frozen files.

No installation or gameplay action is required.

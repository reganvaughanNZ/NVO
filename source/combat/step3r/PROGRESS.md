# Progress against the original eight-step combat plan

1. Foundation: operating native plugin, quiet startup/dependency handling, repeatable compiled/install/backup packets. NVO.esm is RD-free; user health settings preserved.
2. Observe hits: projectile lifetimes, attacker/target/weapon/ammunition, engine-reported body region, hit transactions and health-input diagnostics are operational. A verified single authoritative damage-application interface remains a prerequisite, not a completed feature.
3. Projectile flight: limited explicit kinetic profiles, per-shot private projectiles, G1/G7 drag and gravity integration, VATS/terrain/lifetime fixes and reload evidence.3P verified player creation/return identity.3Q dual-capacity admission and ordinary flight/reload checkpoint accepted; last shot was still airborne at exit. 3R adds a controlled full-pool probe; its runtime check is pending. Units, impact-energy authority, stress/failure coverage and broader equipment coverage still need work.
4. Armour: an offline model and admission-ledger prototype have checks. No live penetration/armour/health/limb damage replacement yet. The pre-damage review gate is still HOLD.
5. Wounds/medicine: planned. Familiar New Vegas medicines are to remain the foundation of a manageable treatment loop. No live physiology or save-persistent injury system yet.
6. Complete weapon behaviour: partial observations and offline family examples only. Laser/plasma/flame/explosive/poison damage rules and integrated spread/injury penalties remain to be implemented. They must not be reported as live NVO behaviour.
7. Tactical judgement/morale: planned. NVO retreat/surrender/threat judgement are not implemented.
8. Start balance: alternative-start integration/menus work and the Baron's caps-based damage ability was retired. Final equipment/proficiency balance waits on combat rules; class-by-class redesign is later work.

We have substantial engine integration and diagnostic groundwork plus a limited live ballistic pilot. We are principally inStep3, with an offline prototype forStep4. Most of the new combat gameplay remains ahead. Packet count is not a completion percentage: many packets isolate engine correctness and regression risks before damage authority is enabled.

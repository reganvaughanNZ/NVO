#3G2 hit/context provenance

The user suspects the VATS head aim in316 capture9a54c6410f44 may have struck torso. Keep that uncertainty. Projectile contact region0 and current ActorHitData region1 are different input snapshots; no universal VATS rule is established.

Native317 adds a read-only join at the existing validated current-hit observer. It checks active session/lifetime, projectile/source/weapon/ammo and fresh target/contact against the cached model. Separate hit_region/contact_region and availability are logged. Late callbacks confirm later; they cannot retroactively authorize damage already processing. No authority or writes are added. The model and tolerances remain unchanged; close contacts receive no invented speed.

See source/combat/step3g2/IMPLEMENTATION.md, ENGINE-FINDINGS.json and replay. The user's Ultra review gate in source/combat/PRE-DAMAGE-REVIEW.md remains pending and mandatory before damage activation. One indexed current-source review, then only affected fixes/deltas, preserves usage. Do not silently claim Ultra ran.

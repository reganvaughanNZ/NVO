# Planned projectile families

User asked about lasers, plasma, flames and miscellaneous projectiles while packet 3C was being prepared. They remain in the plan, without expanding this packet.

- Bullets/pellets: cartridge speed, gravity, drag; each pellet tracked separately. Packet 3C implements only the private 9mm/.308 pilot.
- Lasers: beam or actual engine projectile representation, weapon-specific divergence and thermal interaction. Do not apply bullet mass, gravity or G1/G7 drag to light beams.
- Plasma: separate fictional bolt profiles for speed, spread and energy/heat delivery. Their behaviour is a gameplay/lore tuning choice, not a claim of real plasma ballistics.
- Flames: short-range stream/contact handling, exposure and continuing burns with bounded tick attribution. Avoid treating repeated contacts as separate bullet wounds.
- Grenades, rockets, mines and explosive rounds: distinguish moving projectile/direct impact from explosion event. Preserve engine fuses/bounce until specifically supported; never duplicate blast damage.
- Creature spit, poison, darts, thrown weapons and unusual/modded projectiles: explicit profiles and exceptions. Unsupported types retain their existing engine behaviour.

Step 3 establishes supported flight. Step 6 completes these weapon-effect families through the coordinated damage/injury system after armour and wounds. Step 3C does not implement these additional families. Modular profile/config changes should remain separate from native engine hook code where possible.

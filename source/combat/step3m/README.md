# Packet 3M — armour and projectile contracts

Purpose: define what the damage calculation must receive, how each attack type meets armour, and which system owns each modifier before writing damage code.

**Prepared as a design/reference packet. No install, GECK compilation or game test is needed.** Installed native320 and its banner remain unchanged. Damage replacement remains disabled.

## Your decisions included

- Remove the Brahmin Baron's caps-based damage ability instead of migrating it into NVO combat. The compiled ability is still present today; `BRAHMIN-RETIREMENT.md` specifies its removal and the checks needed before damage activation. Its replacement and a consistency review of every start are queued for the later background pass.
- Lasers, plasma, flame, explosives and unusual projectiles are required parts of the completed system. Each has its own transport/damage rules and validation status. They are not treated as bullets or described as already implemented.
- Keep the potential NVO difficulty presets separate from physical penetration and anatomy. No difficulty or health settings change in this packet.

## Files

| File | Purpose |
|---|---|
| `CONTRACT.md` | Calculation inputs, coverage/material response, exact-once ownership, failure and timing rules |
| `PROJECTILE-FAMILIES.json` | Explicit final scope versus currently implemented/verified support |
| `MODIFIER-OWNERSHIP.json` | Which vanilla/donor modifiers must be retained, replaced, retired or traced |
| `PROFILES.reference.json` | Two source-backed kinetic examples and intentionally incomplete non-kinetic profile templates |
| `BRAHMIN-RETIREMENT.md` | Removal scope, saved-game callback handling and later background decisions |
| `CURRENT-BARON-RECORDS.json` | Read-only inventory of the relevant installed records and references |
| `PACKET-RESULT.json` | Source/installed hashes and packet checks |

All JSON here is **reference data**. Do not copy it into Data/NVSE: no runtime reader or activation switch is installed for it. Armour thresholds and fictional energy-weapon doses are intentionally unset, not silently guessed.

## Existing versus planned

Bullet flight currently covers explicit pilot profiles. Existing observations identified individual Tri-beam and Multiplas carriers, but those old observations do not prove full native armour/damage support. The full plan includes those families, while current gameplay continues using their existing damage/flight behaviour until a supported replacement is delivered.

The first disabled resolver will exercise kinetic, thermal and blast channels with synthetic offline fixtures. Fixtures are software checks, not promises about live game balance. Actual per-family adapters will follow in small packets, followed by targeted user tests before their activation.

## Next proposed packet

**3N: implement the disabled resolver and prepare the Baron script retirement.** A pure calculation module, input validation and offline fixtures make the contract executable without writing actor values. Complete copy-button GECK script replacements will retire the Baron callback and registration sites using the current saved NVO.esm; the user will compile/save them. No broad review or redesign of starts yet.

Ask before preparing 3N. The overall pre-damage gate remains HOLD. This packet needs no test or reversal because it changes only workspace reference files and notes.

# Packet 3A: BallistX pilot data

Purpose: establish correct, editable flight inputs before implementing the native flight component. This packet completes source-data preparation for two pilot combinations. It does not introduce runtime flight, damage changes or a native profile reader.

## What is prepared

`NVO-Flight-Pilot.json` contains the 9mm Pistol with standard 9mm ammunition and the Hunting Rifle with standard .308 ammunition, using selected BallistX 5.4 barrel/cartridge values and G1/G7 drag tables. These are donor tuning values, not independently measured weapon specifications. Each profile retains the original row, source line, explicit units and stable plugin/local-form keys. PROVENANCE.json hashes the supplied donor archive and relevant members.

BallistX's cartridge keys are **PROJ projectile-base records**, not AMMO inventory records. NVO's proposed match therefore explicitly requires the weapon, actual ammunition and actual projectile base. All six selected identities/types were checked against FalloutNV.esm. That check does not establish the winning runtime overrides; the next native packet must verify the live combination before accepting it.

The donor velocity column is **maximum velocity**, not muzzle velocity. The supplied script uses `maximum_velocity * barrel_length / (barrel_length + 2 * peak_pressure_travel)`. This packet calculates a source-data preview at the donor reference temperature of 288.15 K. It is not an observed projectile speed. Barrel and pressure-travel lengths must use the same units. The native integrator and game-unit conversion are still to be implemented and checked.

The Hunting Rifle's donor weapon comment mentions a match cartridge. That comment is not an ammunition selector: this pilot deliberately pairs it with standard .308 and the separate M80 projectile row. No match-ammo record is added or silently substituted.

Original damage, zeroing, spread and temperature-scaling fields are retained only under `unused_donor_values` for provenance. They do not control this packet. The future flight component must not apply the donor damage formula or its unconditional three-second deletion. Energy weapons, melee, explosions, shotguns and unlisted ammunition remain outside these first two pilot combinations.

## Your action

No installation, GECK record creation, script compilation or additional gameplay test is needed for this data-only step. Keep the current NVOCombatCore DLL/PDB (version 203). Do not place these preparation files into Data/NVSE, and do not activate the standalone BallistX/CBD/PBB loaders. `START-HERE.html` provides a copy button for editing the complete JSON in the source workspace.

Expected result: unchanged game behaviour and the existing version-203 log. No `flight ready` message is expected, since the installed DLL does not consume these profiles.

Reversal: this packet changes no installed files or saves. Retain or discard the separately named workspace packet/ZIP; no game restoration is required.

## Next bounded packet, after confirmation

Implement a separate native profile reader and **read-only flight preview** for these two pilot combinations. Resolve plugin/local IDs, verify live weapon/ammunition/projectile identity, cache accepted inputs, and log the selected profile plus observed and calculated initial speed. Validate units and donor-loader ownership before any flight writes. An unsupported or unknown combination must retain engine behaviour and provide a bounded diagnostic.

That packet will contain its own DLL/PDB, installation receipt and short user check. Actual gravity/drag changes follow only after the preview result is reviewed. Broader robot/NPC-to-NPC, tagged VATS, all-pellet and exactly-once committed-damage checks remain required before damage authority; acceptance of 2B4's observation/reload checkpoint is not that approval.

## Preparation checks

The preparer checked donor hashes, row uniqueness/column counts, finite positive inputs, ascending drag tables, and base record identities/types. PREPARATION-RESULT.json records the scope and remaining checks. No engine hooks, native build, gameplay or GECK tests were performed for this packet.

Generation is workspace-oriented: run `tools/prepare_combat_3a.py` from the NVO workspace with its sibling `inspect_plugin.py`, the source/combat/step3a README/credits and the pinned donor/game reference paths. The ZIP includes corresponding generator source for review; extracting it alone is not an installer or a portable build environment.

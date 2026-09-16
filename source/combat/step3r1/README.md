# Packet 3R1 — normal tracking restored

Native 323 / NVO 0.3.23, same version and phase banner as 3R. This delivery uses the already compiled normal configuration, with `NVO_ADMISSION_CAPACITY_PROBE` absent. No gameplay source changes or fresh compilation are part of this packet. The real reservation/refusal system and explicit reset diagnostics remain; synthetic test tickets and probe arm/release code are absent from this DLL. All 128 physics slots are available for actual flights.

3R's accepted evidence remains: 20 SMG shots and one pistol after reload; one deliberate stock fallback at full capacity; all 21 returned identities and natural retirements; 434 applied/verified flight steps and zero movement mismatches; post-reset occupancy zero. This does not claim 128-real-bullet performance or all failure paths.

Only the DLL and matching PDB are installed. The compiled input hashes still match the frozen 3R source snapshot. Normal-build hashes match the verification made before the 3R playtest. The disabled-probe marker is present; probe arm/release strings/code were excluded by the compile-time flag. No ESM, pilot ESP, INI, script, weapon, ammunition or load-order change is included. Damage replacement stays OFF.

No repeated firing test or GECK action is requested for this cleanup. A future log should say `CAPACITY_PROBE_BUILD enabled=0 production_capacity=128` and should contain no probe-arm event. No new runtime validation of this binary is claimed just from installation. Installation/INSTALL-3R1-result.json records backup and file verification. The immediate backup contains the diagnostic 3R build; restoring it re-enables its one-shot probe, so ask the assistant to select the appropriate recovery build if needed.

## Other projectile families

Current exact flight profiles cover the 9mm pistol/SMG, hunting rifle, service rifle, 10mm pistol, .357/.44 revolvers, hunting-rifle AP/HP identities, and two private pilot weapons. Matching is by weapon, ammunition and supplied projectile. These are limited profiles, not blanket support for every bullet or modded gun. AP/HP share baseline flight tuning in this checkpoint; NVO penetration/damage differences are not enabled.

Grenades, lasers, plasma, thrown spears and flamers are not in the current flight profiles. They retain their existing engine/installed-mod behaviour; observation is not replacement or a guarantee of complete family coverage. The capacity experiment validates the owned bullet path and its refusal. It does not automatically implement these other families.

Planned family rules, subject to source verification and individual checkpoints:

| Family | Planned treatment |
|---|---|
| Grenades and other explosives | Preserve appropriate arc/fuse/bounce behaviour; resolve direct contact separately from blast so damage is not counted twice. |
| Throwing spears | Slower arcing physical flight, then piercing/armour and wound rules appropriate to a thrown weapon. |
| Lasers | Beam/energy and thermal protection rules, with no cartridge drag model applied by default. |
| Plasma | Its own moving energy-projectile and impact profile. |
| Flamers | Sustained heat exposure and burning, controlling repeated contacts to prevent unintended damage stacking. |

The intended common layer is attribution, actual reported hit region, armour, injuries and bounded ownership. Family-specific producers must be verified before becoming damage authorities. Unknown/unclassified attacks keep existing behaviour. The next substantive work remains the unresolved pre-damage contracts for units/contact energy and authoritative application; armour, physiology and family damage are still later work. Ultra pre-damage gate remains HOLD.

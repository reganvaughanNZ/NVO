# Step 4B automatic-fire and enlarged-inventory checkpoint

User approved this same-packet live test after the first functional check passed. This introduces only two manually invoked console BAT text files. Native 326, the armour reader, hooks, profiles, plugins, INIs and load order remain unchanged. No damage authority is granted.

The target helper equips Combat Armor and Combat Helmet, raises the selected test target's health to 100,000 and adds one each of 128 explicitly selected ordinary MISC forms. Distinct forms are intentional: adding 128 copies of one item would usually exercise a stack rather than 128 inventory entries. The list is checked against FalloutNV.esm for available, named modelled MISC records with no attached script, deleted flag or quest-item flag; provenance is retained. Other plugins may override base records, so actual traversal counts must be checked in the runtime log rather than assumed.

The weapon helper gives and equips the base-game 9mm SMG0008F217 and supplies 300 rounds of standard9mm0008ED03. Three standard30-round magazines provide roughly90 shots, allowing some misses while aiming to exceed64 qualifying Character hits. Use torso shots on a living target without VATS or god mode. A reload of the prepared save followed by roughly five rounds checks lifecycle reset with the same enlarged inventory. The user performs all gameplay.

Expected review:

- Character inventory traversal is much larger than the prior9-entry baseline and remains below the512-entry safety bound.
- Worn body and helmet remain separately identified; no stale cached pointers are used.
- Up to64 snapshots per load session; further qualifying hits increment omitted_after_limit without continued armour traversal. These omissions are intentional, not errors.
- Hit transaction summary accounting continues after its own64-call detail limit; scope identity is independent of detailed logging.
- Reload starts a new session and restores snapshot recording.
- No unstable/rejected reads, scope/lifecycle faults, movement regressions or unpaired/open transaction accounting; all gameplay-authority flags remain zero.
- User feedback supplies a coarse hitch check. There is no per-scan timing in native326. Passing cannot establish precise overhead, worst-case performance or always-on damage readiness.

Do not expand the inventory automatically if the bound is exceeded or insufficient hits land. Review evidence first. This is not a many-NPC stress test, an NPC-to-player coverage test or creature protection implementation. Review the completed capture, then ask before another packet.

Reversal: load a non-test save. Optional removal of the two uniquely named helper text files requires no DLL rollback. Installation records their hashes and verifies the12 existing foundation/helper files unchanged.

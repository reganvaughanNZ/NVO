# NVO Combat Packet 4A — offline armour shadow adapter

Packet 4A implements the first read-only adapter into the existing pure armour model. It is deliberately offline: no `NVOCombatCore` source changed, no DLL was built, no hook or engine reader was added, and no game file is included.

The adapter accepts typed evidence rather than raw engine pointers. It produces a preview only when identity, component/application, engine path, mode, both region producers, modifier ownership, armour enumeration, cartridge construction, contact speed, units and target profile are all verified. Every incomplete or conflicting case returns a named reason and an empty preview.

The current 3U1 speed range does not pass this contract because it is interval-valued and non-authoritative. Packet 4A stores that distinction and refuses to choose a midpoint. Likewise, a missing armour snapshot cannot become bare skin and collision/hit-data disagreement cannot become torso.

## Result

- Shadow adapter checks: 48 passed, zero failures.
- Existing armour-model checks: 45 passed, zero failures.
- Both standalone x86 builds use `/W4 /WX`.
- 10,000 repeated shadow previews were deterministic.
- Gameplay writes: zero by contract.
- Runtime integration: absent by contract.

## Files

- `CONTRACT.md` — evidence and rejection rules.
- `CHECKS.json` — machine-readable preparation results.
- `SOURCE-SNAPSHOT.json` — exact hashes of the reviewed model sources and build outputs.
- `BUILD-RESULT.md` — compiler and executable results.
- `START-HERE.html` — concise packet instructions.

No installation or gameplay test is appropriate for this packet. A later, separately approved Step 4B may investigate a guarded engine-side equipped-armour snapshot reader without enabling damage.

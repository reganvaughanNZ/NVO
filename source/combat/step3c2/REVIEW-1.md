# 3C2 runtime review

User completed two private-weapon pairs with one same-process reload. Archived before the next launch at `captures/2026-09-15-3C2-5235b89c05fa/NVOCombatCore.log`; SHA256 `5235b89c05faa4914ee64259a89ac0e312d55d8424a79dc8ded1b67f2aa02536`, 45,400 bytes, 183 lines. Numerical review and lifecycle/summary rows are in that folder's `review-data.json`. Read-only review tool: `tools/review_combat_3c2.py`.

Four lifetimes (two Hunting Rifle, two 9mm) all created, impacted scenery 00106B5E and were destroyed. Both loads completed and the process exited normally. No unmatched, overflow, identity/read, timing-invalid, overlap or nesting faults were reported. Thirty timing rows, eight startup/collision rows and 22 moving rows. All four first, unchanged segments matched the expected direction. This accepts observed reload recovery and forward direction for these samples only.

All four first modified segments failed the existing displacement check. Each lifetime then stopped NVO edits as intended. Four movement-argument writes were attempted; zero applied steps verified. Do not mark gravity/drag accepted or advance to damage/armour. No repeat of unchanged 307 is needed.

| Lifetime | dt (s) | Full-vector error (units) | Error if input local Z were discarded (units) |
|---|---:|---:|---:|
| 1, rifle | .016 | .0872833 | .0015696 |
| 2, pistol | .031 | .3258487 | .0033256 |
| 3, rifle after reload | .031 | .3269807 | .0038068 |
| 4, pistol after reload | .016 | .0867382 | .0024903 |

This numerical agreement supports a discarded-local-Z hypothesis; it does not locate the discard or prove which generic movement route executes. The existing log lacks an immediate write readback, the returned argument, and the generic movement exit. Tolerance is unchanged; widening it would hide the observed missing component.

User reports console spam on reload. The workspace Packet 1 bootstrap source prints multiple success lines after every GetGameLoaded reset. However, read-only enumeration of the game Data/NVO.esm (SHA256 `2bb53410287c1c409a0bbb9b51ef38bf14bba2a4e3376f23b5cfc9f73fc0028d`) found no NVOCombatBootstrapScript record. The active plugin list names NVO.esm and NVOFlightPilot.esp. Do not claim the installed source of the repeated messages is established. Native FlightPreview's test-kit notice is process-limited already; remaining native console notices report unavailable diagnostics and are also process-limited. A quiet full bootstrap replacement is prepared separately for the user's working record, not silently inserted into a different ESM or a new quest.

Next authorized packet 3C3: verify the actual 12-byte stack write, observe the generic position-commit and alternate node-commit paths, and read the argument after movement. No relaxed guards or new physics scope. User handles the new two-shot runtime checkpoint. Damage replacement remains off.

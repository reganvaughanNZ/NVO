# Follow-up to frozen Ultra317 review: units and clock

Packet 3T is an offline source/capture/numerical audit. No live code, INIs or gameplay settings changed. Native323 normal build stays installed; Ultra HOLD remains.

ULTRA317-05 is narrowed, not closed. Seventy units per simulation metre is now explicitly retained as an authored model convention. The guarded movement wrapper builds displacement from its parent argument before a possible Turbo movement-delta adjustment. The earlier decoded parent-code snapshot shows VATS adjustments before virtual UpdateProjectile; therefore applying a second VATS multiplier in NVO would be incorrect for that inspected path.

Four stored captures provide 455 exact physics/parent-delta pairs, 475 exact float32 next-lifetime predictions, 29 baseline unit round-trips and 427 production-integrator replays. One3Q physical intent row remains unpaired due to a timing cap. No per-update VATS state/global factor was logged, and the upstream VATS/parent body is not wholly covered by current movement fingerprints. No fresh process capture or game test is claimed. Partition/analytic fixture checks are model checks, not complete VATS emulation.

The next required subtask is the actual contact-speed producer: unchanged first-segment contacts and off-path actor/scenery collision points remain unresolved.3S output is still conditional, with no conversion into armour inputs or damage authority. Do not adopt physical calibration language or silently lift any gate based only on unit/time consistency. For the eventual authority adapter, verify supported producer compatibility including any required upstream clock guards.

Evidence: source/combat/step3t/RESULT.json and CONTRACT.md, tools/audit_combat_3t.py. No new Ultra agent review was run or implied.

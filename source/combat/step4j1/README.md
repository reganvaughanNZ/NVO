# Packet 4J1 — flame lifecycle isolation

Native **0.3.31/331**, prepared for review. This packet repairs the lifecycle coupling exposed by the 4J flamer recording. It does not enable NVO damage, armour wear or stagger. Installation and live acceptance are separate steps.

## Purpose

Installed 330 treats any repeated projectile CREATE address as a flight ownership fault. In the retained 4J recording, twelve flame notifications trigger fault 6 and prevent the later 9mm from entering NVO flight, including after reload. Source tracing shows that the provider's CREATE notification does not guarantee a fresh allocation. Neither a notification nor a retained projectile lifetime proves a separate damage component.

The new exception is narrow: an observation-only flame reference with positive, matching projectile, source, weapon and ammunition IDs, and consistent initial/current flame form types, may receive repeat notifications without blocking unrelated NVO flight. Its identity becomes unavailable for subsequent diagnostic association. The entry keeps its cleanup token until an exact-reference destroy notification or session reset. No replacement lifetime, fabricated hit or damage event is produced.

## Preserved safeguards

- Any retained admission claim or incoming reservation still makes a repeated address a hard fault. The claim survives failed attachment, failed completion and committed flight.
- Changed, unknown, unreadable, inconsistent or non-flame identity still faults. Matching scalar values qualify quarantine only; they do not prove continuity of an allocation or component.
- Public lifetime lookup, hit linkage and impact logs withhold ambiguous identity. Impact and destroy notifications retain internal cleanup ownership. Ambiguous cleanup skips fresh contact, travel and range interpretation while preserving physics stop/retirement and timing cleanup.
- Ambiguous or globally faulted pending reservations cannot commit. The process fault still survives reload. Wrong-reference destroy notifications do not release retained entries.
- The existing 512 lifecycle slots remain bounded. Repeats allocate no extra slot; genuine capacity refusal remains separate. Repeat details are limited to eight rows per category per capture, and blocked-reservation details to four. Omitted or failed logging does not authorize flight.

`PROJECTILE_LIFETIME_AMBIGUITY` distinguishes qualified flame quarantine from a lifecycle conflict. `PROJECTILE_LIFECYCLE_SUMMARY` separates repeated observations from conflicts and blocked requests. `FLIGHT_ADMISSION_STATE` reports the existing process latch on each capture. These are file diagnostics, not new console messages.

## Evidence and limits

[Evidence/VERIFICATION.json](Evidence/VERIFICATION.json) records fresh counts, build inspection, source hashes and unchanged files. The production `NativeObserver.cpp` fixture exercises synthetic forms and inert provider/physics/preview interfaces. The unchanged pool/receipt suite exercises bounded ownership mechanics. These are not game tests. Actual physics/preview cleanup branches are compiled and independently source-reviewed; the fixture checks the arguments passed to those branches rather than executing them.

The 4J recording is retained failing evidence, not a 331 live result. Its 207 preparation checks remain historical. No new engine hook, runtime dependency, damage setter, model linkage, ammunition profile or game record is added. Exact contact evidence, coherent armour snapshots and verified component/application ownership remain unfinished.

## Proposed deployment and check

Deploy only the matching DLL/PDB pair after separate installation approval, fresh installed-file checks and a backup. Keep the existing 4J inventory kit, configuration, NVO.esm and load order. No GECK action is required.

After approved installation, launch normally and load the saved setup. If needed, run `bat NVOComponentKit4J` for the existing inventory kit. Use living targets:

1. Give a very short flamer tap, then wait three seconds unpaused.
2. Fire one standard-ammunition 9mm torso hit **before reloading**.
3. Reload the saved setup and fire one more standard-ammunition 9mm torso hit.
4. Quit normally and report completion for log review.

No VATS, grenades, video or stress test is needed for this focused check. The log must show qualified repeat handling if repeats occurred, no process fault from that handling, and valid 9mm admission both before and after reload. Missing repeat evidence leaves that branch untested; a gameplay hit alone does not establish custom flight admission. Source/fixture success does not predict every weapon variant.

Reversal after installation: with the game closed, restore the installation backup's 330 DLL/PDB pair together. No ESM, configuration or kit change needs reversing. The earlier flame issue returns with 330. Preparation, compilation and check runners never install or load the plugin.

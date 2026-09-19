# Packet 4J live review — routes pass, flight lifecycle fix required

The requested playtest produced usable native330 damage-call diagnostics across one reload, but exposed a separate projectile-lifecycle fault. **Do not accept this as a clean flight test or advance to damage replacement.** The user does not need to repeat the unchanged test.

Pinned capture: `Evidence/LIVE-4J-20260919-094727.log`, SHA256 `8e079a12b768f5b2ae25b56e0ddc378092f73ee51efec4e3239cd2903ebb3d30`, 181002 bytes, 731 lines. It starts with native0.3.30/phase4J and ends with normal `exit_game`; one startup banner. `tools/review_combat_4j.py` reparses the exact capture and writes `LIVE-REVIEW.json`. A separate read-only review agrees with the findings.

## Accepted diagnostic observations

| Sample | Native hit transactions | Observed AV-call windows | Result |
| --- | ---: | ---: | --- |
| Standard9mm before reload | 1 | 2 | One health and one condition route, with matched health callback. |
| Frag grenade | 1 | 5 | One health and four condition calls. Initial explosion flag present; carrier type3A remains `other`, not guessed from a base-form enum. |
| Flamer | 10 | 18 | Nine transactions have health and condition calls. The region14/zero-health transaction has neither monitored AV call nor pre-health callback. |
| Standard9mm after reload | 1 | 2 | Route/context/callback association survives the reload. This does not validate flight admission. |

All27 AV intervals have verified call windows, valid before/after reads, retained current transaction context and zero callback mismatches. The12 observed health calls each have exactly one matching pre-health delta. Transaction and AV generations advance3→6 across reload; armour-reader epoch advances4→7. All13 copy receipts retain their diagnostic association. No AV/transaction depth, open-frame, validity or log-failure error is reported in these streams.

Grenade calls5 and6 both address AV29 with the same requested delta, but are distinct provider-call windows. Never deduplicate using equal arguments alone or sum health and condition changes as one scalar damage amount. Repeated flamer contacts use the retained lifetime3 label, but the creation ambiguity below prevents interpreting that label as verified component identity.

The zero-health region14 flamer contact is transaction4. It queues one bounded callback-gap registry check; both callbacks are still positively present and both Set attempts report unchanged/refused. This is not evidence of lost registration or successful recovery. Session1 callback totals12pre-hit/11pre-health and session2 totals1/1 agree with the observed calls. The original earlier callback-gap cause remains unproven.

## Blocking flight finding

The first flamer CREATE is line206, reference `FF001736`, tracked under lifetime3. Twelve later CREATE notifications reuse that tracked address/reference and report `tracked=0 replaced=1` (first at line246). Session1 totals are `reused_live_address=12 overflow=12`. Here overflow counts failed slot assignment too; it is not proof that the512-entry pool filled.

The existing `NativeObserver.cpp` OnCreate path latches `Fault::Lifetime` whenever an address is already tracked. `FlightAdmission.hpp` maps that fault to6 and deliberately preserves it across reload. Both sessions' flight and physics admission summaries report `process_fault=6`. `ReserveSpawn` and `PrepareProjectile` refuse admission when this latch is set.

Consequently the post-reload9mm shot is forwarded unchanged as stock projectile `0008F20F`: no reservation/base substitution, followed by `untracked_profile` speed status. The normal profile was loaded. This is explained by the process-wide safety latch, not an unsupported critical-hit profile. The diagnostic labels do not explicitly identify the latch at selection time, so clearer blocked-selection reporting is also needed.

The original flame weapon has no NVO flight profile, yet its observation ambiguity disables supported ballistic admission. The next fix must separate non-admitted flame notifications from ownership of projectiles whose flight NVO actually controls. It must preserve a hard stop for genuine admitted ownership corruption; simply clearing the fault on reload or ignoring all repeated addresses would be unsafe. The capture establishes the false coupling; exact creation/reuse semantics still require source tracing and focused fixtures.

## Limits on secondary-effect coverage

All monitored AV intervals were inside HitMe scopes. This does **not** prove that all continuing effects were captured. Session1 also reports356 foreign-thread provider entries passed through. That counter is incremented before active/AV/delta filters, so356 must not be described as356 damage or burn events.

The same target's observed health also falls between some monitored flamer health windows (about0.5–1.0 between several pairs). Those changes lack a captured owning call. They establish incomplete coverage of the intervening health changes, not a diagnosed burn source or unique application. Exact values are retained in `health_changes_between_windows` in the JSON. Primary/secondary ownership, committed-write identity and timed-effect coverage remain unresolved.

Damage, armour wear and stagger authority stayed disabled. No exact contact speed or coherent impact protection was accepted. The first9mm has an engine-segment speed estimate only; the grenade has no projectile-speed query, and flame/final9mm speed remains unavailable. No new total-damage arithmetic follows from these observations.

## State and next action

Fresh read-only verification matched all three installed files and21 protected game/dependency/configuration files to installation evidence; RD.esm remains absent. No native source edits, DLL builds, fixture reruns, installation, game-file changes or game/GECK process actions occurred during this review.207 offline checks remain prior preparation evidence.

Next proposed packet: **4J1, repeated flame-creation handling and explicit flight-block diagnostics**, prepared only after approval. Use this pinned recording first, preserve admitted-projectile ownership guards and keep damage disabled. Then use a short flame-to9mm check before and after reload. Do not request an unchanged repeat now or advance to gameplay damage from the narrow route pass.

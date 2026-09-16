# Packet 2B4 follow-up review - 15 September 2026

Result: accept the outstanding same-process reload and outgoing-melee observation checkpoint. This capture also supplies separate Tri-beam projectile contexts and additional incoming shotgun evidence. No further repetition of the version-203 startup/reload test is requested. Proceed to passive BallistX data preparation (packet 3A), keeping runtime flight and damage replacement disabled.

## Evidence

Archive: `captures/2026-09-15-2B4-c8d11d3a5471/`. NVOCombatCore.log SHA256: `c8d11d3a5471c604e0832026c451500510d59cc93a3171a902d5629dcfc8d394`. Original timestamp: 15 September 2026, 08:40:30 local; 163,334 bytes. The original file was stable during reading. The adjacent analysis.json preserves parsed streams, record identities, checks and user/video evidence separately.

The user reports laser shotgun, Multiplas, Tri-beam and Super Sledge. Runtime weapon IDs resolve to Multiplas Rifle, Tri-beam Laser Rifle, Fists, Super Sledge and Sleepytyme (GRA) for player attacks. Incoming weapons include Hunting Rifle, Single Shotgun, 9mm Pistol and Sledgehammer. No additional transcription is necessary to identify those weapons. A distinct weapon called Laser Shotgun is not identified by these rows; do not invent another record or treat all reported names as separate weapons.

## Capture result

| Capture session | Provider rows | Copy contexts | Hit inputs | Health inputs |
|---|---:|---:|---:|---:|
| Initial load | 176 | 10 | 10 | 10 |
| First reload | 37 | 4 | 3 | 3 |
| Second reload | 582 | 35 | 32 | 29 |

All streams have consecutive sequences within their sessions. All three capture initializations registered their handlers and delivered new events. The two later sessions contain both incoming and outgoing hit inputs, including Super Sledge attacks. This resolves the prior unexercised reload check.

- There are 49 valid copy contexts, 45 hit inputs and 42 health inputs. The capture reports zero invalid contexts/argument contracts, tracking overflow, live-address reuse, unmatched events or read failures.
- All 38 linked projectile contexts match their live creation's projectile identity, source, weapon and ammo. None required assuming the actor's currently equipped ammo was the projectile's ammo.
- The Tri-beam supplies nine creations. A group of three separate lifetimes (23, 24, 25) supplies three copy contexts with distinct beam carriers and three matching ITR hit inputs. The Multiplas supplies 12 creations and one observed actor-hit context. This is evidence for individual carriers, not proof that every beam or projectile must damage an actor.
- Incoming Single Shotguns supply 42 separately tracked creations/impacts/destructions and four hit contexts with their own linked carriers. 7 projectile impacts name the player, but only four appear in the hit-input stream. The log does not explain each non-emitting impact. Do not convert impact counts into damage counts, infer lost damage, or certify complete pellet damage coverage.
- Outgoing melee includes one Fists input and three Super Sledge inputs. They have null projectile carriers/ammo, as expected for this observed path. Four incoming Sledgehammer inputs are also present.
- Total projectile creations are 183, with 177 impacts and 182 destructions. One Hunting Rifle projectile is still tracked when the first reload begins. This is a load boundary, not an observed memory leak: the observer clears its transient table before the next capture. Sessions 2 and 3 each close with zero outstanding lifetimes, and all printed events match independently.
- Four creature hit inputs resolve to Snuffles. No robot or nonplayer-versus-nonplayer hit inputs are demonstrated in this capture. VATS and god-mode state are not tagged by version 203.

The proximity rule used in the previous review again finds 42 unique candidate hit/health pairs. Twenty-five outgoing candidates show approximately 2x scaling, and 17 incoming candidates approximately 0.5x. These are different observation stages, not duplicate applications or verified committed HP loss. Three Weapon-region inputs have no candidate health row. Keep the user's combat/health settings unchanged.

## Recording value and limits

The video is 286.46 seconds long (about 4 minutes 46 seconds), 1282 by 742 at 30 fps, and about 150 MB. Six still frames were sampled at 8.59, 57.29, 108.85, 160.42, 211.98 and 263.54 seconds. No continuous playback or audio transcription was performed. Frame files and decoder metadata are in the archive's video-frames folder. File size is not a measure of billed model usage.

The sampled frames corroborate version 203, a functioning Pip-Boy display, Tri-beam selection, a live hostile Gun Runner Guard and displayed player HP changing from 590/590 to 437/590 across the sample. That HP change is not a controlled single-hit measurement. The console's mismatched-parenthesis output follows `Nice :)` entered at the console, consistent with the engine parsing that input; it is not evidence of a new NVO script compile failure. The previously investigated JohnnyGuitar EDID warning is also visible.

The log establishes post-reload event delivery. The sampled frames alone do not establish the entire reload sequence or VATS/god-mode toggles and were not used to assign individual rows to video timestamps.

For routine checks, the log plus brief weapon/ammo, target, VATS/god-mode and reload notes is more economical than reviewing a whole recording. A short timestamped clip remains useful for visible problems, shot timing or behaviour the log cannot show. There is no need to transcribe this recording.

## Next scope

The user's request to continue is used to prepare **packet 3A: a passive BallistX pilot dataset**, not to enable damage authority. The installed version-203 DLL/PDB remain unchanged. The next native packet will need its own confirmation and user check: read profiles, verify live identities and preview initial speed without changing flight. Committed damage, full pellet coverage, robots/NPC-to-NPC and identified VATS remain gates before the later damage system.

Only workspace evidence, documentation and packet-3A source data changed. A local video decoder was downloaded into tools/.video-reader to extract the six frames; it was not installed as a game mod. No game or GECK launch, gameplay test, native rebuild or installed-file modification occurred in this review.

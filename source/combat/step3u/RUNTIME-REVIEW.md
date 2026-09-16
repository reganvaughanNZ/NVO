# Packet3U runtime review — partial pass, terrain classification fix required

Captured completed native324 test: six creations, six contacts, six natural retirements, one reload and normal exit. One startup banner; zero movement rejections, accounting pairing failures, transaction invalid/open entries or pool leaks. All ten inspected installed identities unchanged; RD absent. No game files changed or process started/stopped during review.

| Shot | Actual logged weapon | Result |
|---|---|---|
| 1 | 9mm pistol, standard ammo | Head in both collision and hit data. Observed first-segment mean387.109m/s available and paired. |
| 2 | 9mm pistol, standard ammo | World/ground contact with zero target ID. Complete snapshot rejected by !s.target. Pre-clamp and final values support a40.252-unit Z raise. |
| 3 | 9mm pistol, standard ammo | Same zero-ID rejection. Observations support an89.069-unit Z raise. |
| 4 | 9mm pistol, standard ammo | Same zero-ID rejection; final movement matches normally, floor difference22.584 does not cross30-unit clamp threshold. |
| 5 | Hunting rifle, standard .308 | User-reported VATS torso aim. Collision region3=left arm1; hit-data region0=torso. Observed engine-segment mean849.771m/s available and paired. Keep the disagreement, do not remap. |
| 6 after reload | 9mm pistol, standard ammo | Wall contact. First-segment mean387.109m/s available. Fresh session, no stale state. |

51 applied steps comprise48 verified clear-flight steps and3 collision-ending steps. Those three impact steps are not additional clear-flight passes. Their contact snapshots, reset observations and flags were read successfully, but EvaluateContactSpeed returns snapshot_unavailable at its !s.target gate before considering the new terrain proof. ReadForm deliberately allows a null form to be read as absent; zero form ID is not itself proof of a failed collision read. The existing log does not distinguish a null target pointer from a nonnull zero-ID form; preserve that distinction in any future classification.

The three distant ground shots used9mm in the actual log, not the rifle originally requested. This is useful diagnostic evidence and requires no repeat merely for weapon choice. Shots2/3 reproduce the sought terrain branch naturally. Offline arithmetic matches their pre-clamp expected endpoints, same contact, strict height condition and final corrected Z/accounting within original tolerances. Native324 itself accepted neither clamp because of the earlier zero-ID rejection; do not mark the speed path passed.

Next proposed3U1: explicitly represent valid world contacts separately from unread contact data and actor/reference identity, retain actor guards, and replay this capture first. Do not globally remove identity validation or manufacture a target ID. No further gameplay needed to diagnose this bug. Ask user before preparing the next packet.

Damage remainsOFF; Ultra317HOLD. Exact contact-time, off-curve point association, region disagreement and pre-movement coverage remain separate unresolved gates. Source/build/install unchanged.

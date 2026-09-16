# Packet 4D live review

**Exact-origin and authored-coverage functional checkpoint passed.** No further repetition of this test is needed.

Pinned log: Evidence/LIVE-4D-20260917-010933.log; SHA256 02f55dd6afa9999a85a595025c06c89f66a674f861a239f6a459335448fd5862. Native327, two load sessions, one reload and one submitted startup banner. Normal exit.

| Load / hit | Equipment observed | Classification result | Log line |
|---|---|---|---|
| 1 / 1 | Combat Armor and Combat Helmet | Two independent FalloutNV.esm profiles | 82 |
| 1 / 2 | Combat Armor only | Helmet row absent | 147 |
| 1 / 3 | No worn armour observed | Empty classification, bare authority remains0 | 209 |
| 2 / 1 | Both pieces restored | Fresh successful classification after reload | 328 |

Both activations resolved12 loaded mod names and loaded2 profiles. All4 snapshots were complete and stable. All5 item rows agree across raw identity, copied owning-plugin/local-ID, call-local instance token and profile mapping. Body coverage stays partial torso/limbs with no head; helmet coverage stays partial head only. All conditions were full. Item traversal order reverses after reload, with correct profile identity retained.

Zero classification holds, unresolved origins, reader rejects, unstable snapshots, scope failures or logging failures. Lifecycle, hit-transaction and projectile summaries report no open calls/lifetimes, read failures, movement mismatches or admission faults. Contact-speed rows remain non-authoritative observed engine segments; no exact-energy approval follows from them.

All4 landed hits used the hunting rifle00004333 and standard .3080006B53C, with hit-data region0 on the same humanoid. This differs from the requested9mm, but adequately exercises the requested inventory and reload states. No repeat is needed for this checkpoint.

All15 pinned installed files match the installation receipt and protected baseline. RD.esm is absent. This review copied the log and wrote workspace documentation only; it did not change game files, launch a process, install KEYWORDS or enable any damage/stagger authority.

Scope: successful live base-game identities and provisional authored coverage only. Custom gear, altered load order, unknown equipment, creatures, NPC-to-player cases, condition changes and stress timing were not exercised here. The existing offline cases remain separate evidence. Actual hit-surface coverage, ordered materials, winning overrides, anatomy, modifier ownership and contact-speed authority still gate damage.

Proposed next packet, subject to approval:4E keyword-to-profile authoring support for custom armour. Establish validated mappings and exact-record exceptions, refuse conflicting tags, and decide a bounded cached integration using the available JIP/KEYWORDS sources. Begin with offline resolution checks; do not presume a native keyword API or read private donor containers without a reviewed interface. No game installation or damage enablement is approved by this test-completion message.

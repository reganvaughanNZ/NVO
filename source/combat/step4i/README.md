# Packet 4I: native diagnostic copy capture

Native 0.3.28/328 is prepared and compiled, **not installed or live-tested**. The previous accepted runtime checkpoint is 0.3.27/327. This packet connects contact and armour diagnostics to the same observed hit-data copy. It does not connect MaterialPreview or enable damage, armour wear or stagger.

## Purpose and implementation

The existing `CopyHitData` wrapper obtains one scalar transaction scope. It now includes a transaction generation and a distinct copy ordinal, independent of logging limits. The armour observer returns a small receipt with that exact key, its own reader epoch/sequence, status and bounded item-count/completeness metadata. No armour pointers or item arrays escape the reader.

After armour observation, the transaction scope is revalidated. The current-hit observer independently rereads identity, actual region, flags, ammunition and process ownership, checks the current thread/session/lifetime, and forwards the original scope and receipt to flight diagnostics. It does not reconstruct producer keys from log order or cached collision data.

Old-generation frames cannot qualify or alter newly reset return counters. Their original continuations still unwind normally. Transaction and copy counters refuse wrap. Nested/tainted, changed, unsupported, omitted and stale observations remain explicit. This adds no new engine hook, provider call, projectile motion change or event handler.

## What to look for after a separately approved installation

The game-root `NVOCombatCore.log` gains:

- `HIT_TX_STAGE ... stage=copy_input ... generation=... copy=...`: exact diagnostic copy identity. The old `ordinal` remains a log-stage number, not the copy number.
- `ARMOUR_COPY_SCOPE`: links the existing armour snapshot sequence to that same generation, transaction and copy.
- `HIT_COPY_CAPTURE`: reports independent scope validation, armour receipt status and whether that receipt belongs to this copy.
- `IMPACT_COPY_CAPTURE`: carries the same scope into the projectile/contact observer, retaining separate collision pairing and unresolved impact authority.

`armour_joined=1` means that the receipt came from the same diagnostic copy. A rejection, unsupported creature or sample-limit receipt can also join; this is **not** a successful snapshot or verified protection. Inspect status and completeness flags. `scope_session` preserves the original scope session even when it differs from the current observation. Counts remain diagnostic budgets: 200 hit contexts, 64 contact queries and 64 supported armour attempts. Missing logs or data cannot authorize gameplay or reuse old evidence.

## Deliberate limits

This is copy-bound diagnostic association. `component_verified=0` and `application_verified=0` remain explicit. A transaction, copy number or projectile lifetime is not proof of one attack component or committed damage application. Mechanical, melee, explosive, beam and flame behavior is not reclassified as ballistic by this packet.

Speed intervals, segment means and model candidates retain their existing labels. `hit_position_associated=0`, `exact_contact_speed=0` and `at_impact_verified=0` remain explicit. Stable armour reads are not atomic impact state; empty worn inventory is not verified bare anatomy. No 4H reserved producer is implemented or asserted, and MaterialPreview/ImpactBinding remain outside the DLL.

## Checks and review

[Evidence/VERIFICATION.json](Evidence/VERIFICATION.json) records fresh compilation, static DLL/PDB identity, suite results, source hashes and limits. Standalone fixtures run production armour observation and transaction-scope code against synthetic memory/stubs. They do not install hooks, call game addresses, load the DLL or establish live acceptance. The real bounded armour reader is checked separately. Unchanged model suites are hash-verified rather than rerun as new evidence.

The package keeps donor credits and applicable component licenses. All active native code needed to rebuild is under `Source`; use `Source\NVOCombatCore\BUILD.cmd --no-pause` with an installed x86 MSVC toolchain. Dedicated check runners are in `Source\NVOCombatCore\tests`. The checkout packaging tool is `tools/prepare_combat_4i.py`.

## Installation, test and reversal

No files in the game folder changed. There is no GECK step or new ESP/ESM/configuration. The proposed installation contains only `NVOCombatCore.dll` and its matching PDB, with backup and hash checks before replacement. Installation requires separate approval.

After installation, the proposed short test is two landed standard-9mm torso hits on one living armoured human target, reload the saved setup, then one more landed torso hit. No VATS, stress test or video is needed for this specific copy-association checkpoint. Report completion and I will inspect the log. This does not certify accuracy of impact speed or damage.

Before installation, reversal simply means not using this package. After an approved installation, restore the backed-up DLL/PDB pair with the game closed. No saves, game records, load order or configuration should need changing for this packet.

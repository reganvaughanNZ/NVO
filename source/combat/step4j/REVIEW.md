# Packet 4J review and interpretation limits

Native 0.3.30/330 is prepared, not installed or live accepted. The last accepted live checkpoint remains Packet 4I1/native329. This review concerns the new diagnostic evidence and its boundaries; actual fresh check counts and binary/source results belong in [Evidence/VERIFICATION.json](Evidence/VERIFICATION.json).

A separate bounded review of the final production diffs found no actionable blocker. It checked unchanged assembly/provider chaining, generation cancellation and parentage, three-slot callback reads, original metadata and conservative route labels. The synthetic checks also exposed an old-generation taint/nesting inheritance case; the production fix and a nested reactivation regression are included. This is source/fixture evidence, not live acceptance.

## What can be associated

The actor-value observer keeps engine caller route, active HitMe context and matching ITR pre-health arguments separate. A route label requires the exact recognized caller, a compatible AV argument and a matching retained code-window fingerprint. The two HitMe condition callers share a route category; neither becomes a unique component or application. Unrecognized or failed route witnesses remain unclassified. [SOURCE-TRACE.md](SOURCE-TRACE.md) records the retained source and capture provenance.

Transaction matching requires the current valid, untainted frame on the main thread with the exact original receiver/source and current session/generation. The returned context contains scalar copies of entry metadata. It exposes no engine pointer, performs no new hit-data read and changes no event count. Its generation and lifetime retain their producer scope. Copy-attempt counts are observations of attempted stages, including rejected copies; they cannot identify which copy caused an AV call.

The return path independently checks retained transaction identity. AV before/after validity also depends on the observed actor, class/owner tables, effective AV and process remaining compatible. These checks qualify a diagnostic call window. They do not prove a coherent impact snapshot, one storage write or committed damage ownership.

## Callback and nested-call semantics

The existing ITR pre-health handler forwards the observation to the AV observer. A matched callback requires an active current-generation untainted health frame, identical receiver/source arguments and an equal finite negative requested delta. Only the three immutable slots are read. The mutable multiplier remains untouched. A matching callback therefore witnesses the provider's input at this boundary; other handlers and subsequent work can still affect the outcome.

Callbacks that fail these conditions remain mismatches, and callbacks with no current AV frame remain separately unscoped. Their absence or rejection must not be relabeled as a secondary effect, a successful application or proof of no damage. Registry membership and callback emission retain the distinct meanings established in 4I1.

Nested activity is counted even when its AV is not sampled. An enclosing before/after net may include that activity, so `net_kind=inclusive_nested_window` is explicitly non-additive. Pre-hit input, pre-health requested delta, net AV differences and callback/copy counts are different observations. Summing them would risk double-counting. `additive_net=0`, `component_verified=0`, `application_verified=0` and `primary_or_secondary=unresolved` remain required interpretations throughout.

## Source and validation boundary

Existing engine hook sites and assembly bridges are retained. No additional engine hook, dependency, damage setter or model integration is introduced. Lifecycle cancellation, main-thread guards, fixed depth/detail limits and original continuation unwinding bound the observer. Initial hit flags and critical-effect reference presence are recorded as metadata only; no family or applied effect is inferred from them.

Production-code standalone tests exercise synthetic fixtures and stubs. Their results cannot establish real engine/provider dispatch, timing, effect ownership or live acceptance. The verification record is the source for fresh counts and compiler/binary evidence; historical model/reader counts must not be represented as newly run checks.

The optional inventory kit uses base records verified by a read-only inspection of `FalloutNV.esm`, recorded in [Evidence/TEST-KIT-FORMS.json](Evidence/TEST-KIT-FORMS.json). Preparation did not write game files, launch or close game/GECK processes, or load/install the DLL. Running the optional batch after installation is a separate user action that adds inventory.

## Next evidence and reversal

After separate approval, the proposed deployment contains the reviewed DLL/PDB pair and optional kit file. Fresh state checks and backups must preserve the previous native pair and whether the kit existed before deployment. Reversal restores the pair and restores or removes the kit according to that prior state.

The bounded user check is one standard9mm torso hit, one frag detonation near a living target, one very short flamer tap followed by three seconds unpaused, then a saved-setup reload and another standard9mm torso hit. Each sample needs a living target. No VATS, GECK or stress test is required. Review will examine caller-route witnesses, original HitMe context, matched callback arguments, nested windows and reload continuity without expecting a fixed application count.

Even useful, consistent diagnostic rows will leave primary/secondary ownership and actual component/application identity unresolved. Damage, wear and stagger remain disabled; no gameplay authority follows from this preparation or the proposed check.

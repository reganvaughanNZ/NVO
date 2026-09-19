# Packet 4I source and validation review

A separate reviewer traced transaction, copy, observer, flight and armour boundaries before implementation. The implementation preserves provider chaining, naked-wrapper assembly and existing hook installation/fingerprints. It changes scalar identity propagation and diagnostic receipts only.

The review identified a lifecycle issue that the new generation explicitly addresses: a returning TLS frame from a suspended capture must not decrement a freshly reset open-call counter, even if the session number is reused. Before also checks the generation around unlocked snapshot/lifetime reads. Current, IsCurrent, MatchScope and After check frame generation. TLS frames themselves remain intact until their original return bridge pops them.

Copy ordinal is the provider frame's copy counter, not the log-capped stage counter. Transaction and copy identity saturation refuses reuse. No transaction lock is acquired under the observer/physics lock; post-reader revalidation occurs at the outer Capture boundary. Existing armour recursion taints the outer observation and rejects its payload.

Production-scope fixtures exercise these boundaries with synthetic memory and inert stubs. Separate production-armour fixtures test receipt identity, reentrancy, reload during a read, unsupported targets, rejected reads and diagnostic capacity. The full reader's standalone regression suite is also rerun. Fresh results are recorded in Evidence/VERIFICATION.json; old model pass counts are not presented as new results.

The binary is statically inspected for x86 PE format, the two expected NVSE exports, matching PDB GUID/age and imports. Source checks pin unchanged modules and disabled model linkage. None of this proves compatibility in a running game or atomic impact state. Exact speed, actual struck surfaces, component/application semantics and committed damage remain open.

Final review tightened refusal labels so a lifecycle change before snapshot reservation is not reported as diagnostic capacity exhaustion. The DLL and affected receipt suite were rebuilt/rechecked after that adjustment; unrelated successful suites were not repeated. Scope review found no remaining concrete blocker within this bounded packet.

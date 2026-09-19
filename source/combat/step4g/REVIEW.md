# Packet 4G review

Two bounded independent reviews supported this packet: a requirements/evidence review and a read-only implementation review. The requirements reviewer then authored the new bridge fixtures independently of the main implementation, using manually calculated expected values rather than the function under test as an oracle.

The initial requirements review identified three constraints addressed in the implementation:

- The legacy model's humanoid region enum cannot represent arbitrary creature regions. The new bridge retains literal authored engine IDs; only the numerical kernel is shared.
- Natural/chassis losses cannot be disguised as worn-item condition changes. Outputs retain distinct owners, target/region identity and surface keys.
- `AuthoredCurve` must not silently become the old condition multiplier. The new binding validates explicit curves or declared condition independence, retaining real condition for wear limits.

The extracted shared evidence gates preserve the old identity/path/mode/profile/speed predicates and their order in the original shadow adapter. The numerical kernel is common to both paths. A separate code reviewer reported no actionable issues in the bridge, arithmetic core or evidence extraction. This is a source review, not proof of game correctness.

New fixtures cover independent hand arithmetic, nonlinear condition response, duplicate profile IDs across distinct instances, changed verified order, unknown evidence and numeric rules, natural/robot ownership, unsupported families, real-time/VATS equality, pellet accounting, overflow and empty outputs after late failure. Existing model, shadow-adapter and 4F definition checks are run afresh by the packet runner. Exact fresh counts, compiler logs and source hashes are in `Evidence/VERIFICATION.json`.

Important unresolved limitation: the transmitted-impact fraction remains the earlier coarse direct-to-target approximation; it is not a layered stress-wave or impulse calculation. No production material values or runtime authority are certified by these checks.

## Documentation review, 19 September 2026

The user supplied Claude's review of the 4G README (which builds on 4F). Source cross-check confirmed an actual wording error: the unsupported-family list substituted the delivery categories Melee/Thrown for the families Piercing/Cutting/Blunt. `nvo::responses::Family` has eleven attack entries, excluding Count/Unknown. README and the review page now name the actual ten non-Ballistic families and distinguish them from `Delivery`. No additional damage family was missing from the enum.

The penetration warning is valid: false does not mean protected, blocked or ineligible for a wound. MODEL-RULES now states the status-first consumer rule explicitly and notes that the legacy `armourPenetrated` flag is not semantically interchangeable with `protectionPenetrated`. Source inspection and existing bare-hit fixtures confirm the intended difference.

Condition wording now specifies the legacy linear formula and the new authored scaling, with both retaining actual item condition for wear. Neither implementation forces condition to one; an independent response sets only its protection scale to one. The numerical formulas in MODEL-RULES were cross-checked against the shared kernel and bridge and match those implementations.

This was a documentation correction and read-only source/fixture inspection. Native code and fixtures were unchanged. The prior 416-check result remains historical evidence from packet preparation, not a new test run for these text edits. Release documents and archive hashes were refreshed after checking the existing source/evidence hashes. No compilation, game access or 4H work was performed.

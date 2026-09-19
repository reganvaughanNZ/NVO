# Packet 4F bounded review

Scope: original offline response-definition selector and design contract. No game execution, source donor implementation, physical calibration or numerical material resolver was reviewed as part of this packet.

An independent read-only review checked the active new module against the existing ArmourModel/ShadowAdapter boundaries. It identified that repeated worn profile IDs could appear as repeated surface rows even though the query carried no item-instance identity. The selector now defines that input as a unique set of surface-profile IDs and rejects duplicates with an empty result. A focused regression check covers that case. A future equipment-instance adapter must preserve distinct real items separately.

The follow-up review found no functional issue within the stated definition-selector scope. Wording was corrected to distinguish surface-profile IDs from response-definition IDs and to describe missing completeness clearly.

Local review also added explicit natural-profile completeness, tissue-specific bindings and delivery-aware timing, and checked that failed selection after a successful first surface discards the partial result. Family/delivery acceptance is checked against an independent fixture matrix, not computed with the function under test.

This review does not certify actual hit identity, coverage or contact energy. The runtime and earlier numeric model are unchanged. Fresh build/check counts and input hashes are recorded separately in `Evidence/VERIFICATION.json`; deterministic repetitions are not a runtime performance benchmark.

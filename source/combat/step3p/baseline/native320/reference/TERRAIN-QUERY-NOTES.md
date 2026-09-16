# Verified terrain-query path and efficient follow-up

Established in packet3F2 using the user's running FNV image, timestamp4E0D50ED, base00400000, size0107B000. Use source/combat/step3f2/ENGINE-FINDINGS.json and its runtime manifests as the address/hash evidence. Do not derive hook bytes from the installed on-disk executable: its code differed from the running image in this investigation.

Generic movement00930150 calls TES::GetTerrainHeight004572E0. CandidateXYZ is `[generic EBP-30h]`; the query's output float is `[generic EBP-2B4h]`. Saved generic EBX is the incoming argument frame, with caller at+4. The projectile caller is009BF416. Query initializes default at0045738A from float01017824=-2048 and returns false at004573DC when terrain lookup fails. Generic code ignores AL and raises candidateZ at00930171 when height minus candidateZ exceeds double0101DB88=30.

The packet scopes its correction to existing private tracked applied steps and failed default results. All exact fingerprints are in FlightPhysics.cpp. Successful terrain, collisions, the initial baseline and unrelated movement stay unchanged. An end position of-2048 alone is insufficient evidence to suppress any guard.

For later reviews:

1. Archive the user's current log once and verify its SHA before another launch. Preserve user shot/VATS context separately from native evidence.
2. Read PHYSICS_TERRAIN_SUMMARY and correlate REJECT_DEFAULT with REJECT_DEFAULT_VERIFIED for the same session/lifetime/step. Those labels refer to rejecting the invalid terrain default; PHYSICS_REJECT still denotes an actual track failure.
3. Check actual displacement against the unchanged tolerance, and compare correction counts with verification/collision exclusions. A test without the path executing is inconclusive.
4. Reuse saved engine captures while their identity/ownership guards match. Only capture additional code if a concrete new question requires it. tools/inspect_runtime_capture.py checks manifest hashes and produces offline disassembly; tools/read_height_route_runtime.ps1 and read_terrain_route_runtime.ps1 are bounded read-only capture helpers.
5. For a new native packet, keep specific source/assembly checks separate from the existing hash-pinned two-file installer. Preserve backups, protected records/configs/activation and donor notices. Do not repeat old ammunition cycles unless the change affects them.

This is an implementation notebook, not a claim that packet3F2 has passed gameplay. The VATS-miss correlation is pending the user's next test.

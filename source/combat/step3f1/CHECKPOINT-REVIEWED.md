# 3F1 reviewed: diagnostic capture accepted, height adjustment unresolved

See [REVIEW-1.md](REVIEW-1.md) and `captures/2026-09-15-3F1-77ebadbd30fd/review-data.json`.

User reported shots1-3 misses, shot4 an unintended hit, shot5 close HP VATS, shot6 farther HP VATS. Log confirms six correct standard/AP/standard/AP/HP/HP identities across one reload. Linked actor hits4/5/6; farther HP supplies one matching edited flight segment. Close HP collides on the initial unchanged segment.

One complete failure report: standard shot3 at step392, engine age5.8456s. Requested downward Z=-39.298344; actual upward Z=17.9736328 to exact end Z=-2048. XY matches within tolerance; position residual0; local request unchanged; no contacts/impacted flag observed. Suspect engine height/terrain boundary, not yet a confirmed cause. No report omissions/write failures.

400 matching edited movements and5 baselines reported;72 edited comparisons independently verified in routine detail. No identity/lifetime/reset errors. Diagnostic observability accepted; underlying flight and full3F acceptance still pending. Keep displacement tolerance/guards and damage authority unchanged. HP persistence remains unresolved.

Current installed packet remains3F1/native312. Review changed only workspace evidence/documentation. Await user permission before preparing the next packet to identify and handle the exact height-adjustment path. Do not request another gameplay repeat before that work.

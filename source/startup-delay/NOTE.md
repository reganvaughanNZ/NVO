# Reported new-game menu delay

2026-09-16: user reports approximately55 seconds between finishing the new-game intro and the Alternate Start menu. Optimization requested as a note; no startup files changed here.

Installed NVO.esm VCG00 stage source calls PlayBink ALTIntro.bik, then ALTStartUDF, stops VCG00 and starts ALTStartQ. ALTStartUDF moves the player to ALTCellMarker and prepares world/quest state. ALTStartQ stage0 calls ALTBackgroundMenu once its GameMode block reaches that state. Its explicit8-second timer is AFTER character creation and cannot explain this pre-menu delay. Quest custom-delay data is0.001s, not55s. A large ALTIntro.bik exists, but file size is not evidence of post-video waiting.

No timestamps exist across video completion, UDF/cell transition and first menu call in this capture. Need narrowly timed startup instrumentation or examination of the upstream VCG00 script before choosing a fix. Do not remove fades/initialization or change global quest processing based on the duration alone. Possible avenues: remove a proven redundant wait or defer work that the menu does not need, preserving safe scene/quest setup. Hypotheses only. Keep separate from combat damage work.

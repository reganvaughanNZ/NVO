# Packet 3I: quiet startup and Player baseline

Prepared for your GECK compile. Open **START-HERE.html** for three complete scripts with copy buttons and the apply-helper link. Native318 and its flight/diagnostic settings remain installed. This packet adds no native code, damage replacement, new quest or ESP.

The staged **NVO.esm** is a copy of your current 449,067-byte ESM with one added override: the base-game Player record `00000007`. All 819 existing records are byte-identical. The five NVO health game settings and master list are preserved. It restores base health 100, SPECIAL 5, fatigue 200, speed multiplier100, default skill offsets and base inventory, overriding RD's inherited test values. Character creation and background scripts still choose the character's actual stats and gear. This does not promise 100 displayed HP or repair values already stored in an existing save.

The three script replacements correct both JIP name checks and remove startup dependency popups. The bootstrap reports missing requirements once per game process, through the console only; healthy reloads produce no bootstrap success/status messages. The two Alternative Start controllers check requirements quietly before proceeding. Existing compatibility checks report through the console, while actual choice menus remain unchanged.

**Apply the staged ESM before compiling scripts.** Running the helper afterward would discard the compiled edits; it deliberately refuses an unexpected/newer NVO hash. It backs up NVO/RD outside Data, blocks while game/editors/Vortex are open, and replaces only NVO.esm. Nothing is installed by merely opening this packet. RD remains a required master, carrying the original quest/script identities until a later migration.

See GECK-INSTRUCTIONS.md for the checkpoint and reversal; OWNERSHIP.md records remaining RD and Brahmin Baron work. PLAYER-RECORD-AUDIT.json and SCRIPT-DIFF.txt show the exact prepared changes. GECK compilation and gameplay are not yet verified.

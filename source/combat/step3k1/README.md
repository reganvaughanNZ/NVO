# Packet 3K1 — launch banner

Native320 prints `NVO [0.3.20] - The Mojave is yours.` to the console once per game process. It runs on the first main-loop message after deferred initialization. The inspected xNVSE source prints its version before deferred initialization; JIP prints during deferred initialization, so the NVO line follows both.

The attempted flag lives only in DLL process state. Loads, new games and returns to the main menu cannot reset it. Closing the game and launching again permits a new banner. No popup, HUD message, GECK script or save variable is added. The displayed version follows the native development build. A failed submission is logged once without retries or intrusive warnings.

Packet 3K's requested rifle/reload/punch checkpoint passed on native319. This update changes the startup message and version only; combat observer, damage, projectile, configuration and ESM bytes are unchanged. Damage replacement remains disabled.

No repeat combat test is needed for this update. Check the line on your next normal launch; report any duplicate. The assistant's load check establishes one successful console-script submission at the main menu, not a visual screenshot or an automated gameplay/reload test.

Reversal: close New Vegas and restore only the DLL and matching PDB from the backup identified by Installation/INSTALL-3K1-result.json. Retain the current NVO.esm, pilot and configuration.

Next proposed combat packet: identify the existing factor-of-two health scaling before designing the replacement armour calculation. This remains pending user approval; no new damage authority is enabled by this banner update.

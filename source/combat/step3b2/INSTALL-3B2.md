# Packet 3B2 installation receipt

Installed and enabled on 15 September 2026. NVOCombatCore **0.3.2 / 302**. The game was already closed and was not relaunched. No gameplay or GECK testing was performed by the assistant.

Replaced three files (DLL, matching PDB, flight INI). Added the isolated six-record NVOFlightPilot.esp and the reserved empty game-root NVOFlightPilot.txt, which the native module rebuilds with the current load indices when the test save loads. Added only NVOFlightPilot.esp to plugins.txt; all existing activation bytes/order were preserved. loadorder.txt was not changed. Vortex staging/profile settings were not edited; if a later deployment rewrites activation, enable the pilot there too.

All five installed file hashes verified, all 46 protected files unchanged. JIP, ShowOff and ITR binaries matched the inspected dependency hash preconditions. NVO.esm, health/game settings, saves and unrelated extenders are preserved.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3B2-20260915-100035-16ae504b`

The backup includes originals/Data/NVSE/Plugins for the prior 301 DLL/PDB/INI, originals/activation/plugins.txt, prior logs, the exact install plan and before/result inventories. The new ESP and batch did not exist before installation.

- `Data/NVSE/Plugins/NVOCombatCore.dll` â€” SHA256 `f20f053f06de510902b550e1827c7d1fbe033f49958e6b401df9374d8167e332`
- `Data/NVSE/Plugins/NVOCombatCore.pdb` â€” SHA256 `b7ad5c6b3620885ced5453ade2f80f9021122c4faf6a027343364ebde77bf06a`
- `Data/NVSE/Plugins/NVOFlightPreview.ini` â€” SHA256 `3b7789bf53407a3427f61941ff7c3a81a4aac4fe074bea6f95ba6ba7bf299107`
- `Data/NVOFlightPilot.esp` â€” SHA256 `f5fd916841ebf5aafae5c467a7e17dd67fdf1faf1abc9368f66e936f146244ab`
- `NVOFlightPilot.txt` â€” SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

Activation SHA256 after appending the pilot: `17c94eb4e77bfcc9273aa45f5de4f7c14c5e06ea8c8aaccd952c8724a2484ee2`.

To reverse, close the game, restore prior DLL/PDB/INI, remove Data/NVOFlightPilot.esp and NVOFlightPilot.txt, and remove the pilot's activation entry. The original plugins.txt can be restored if there have been no later activation changes. Load the pre-pilot test save. Keep this backup outside NVSE/Plugins.

Gameplay acceptance is pending. Follow START-HERE.html and send the resulting game-root NVOCombatCore.log. Do not proceed to the next packet before review and confirmation.

Post-install documentation correction: updated only INI comments to identify packet 3B2 and distinguish private record flight from native writes. All settings compared unchanged; previous comment copy retained in the backup. Final installed INI hash shown above. Original plan/result retain initial transaction hashes; final-result.json records the correction.

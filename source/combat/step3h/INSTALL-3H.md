# Packet3H / native318 installed

Installed only NVOCombatCore.dll and its matching PDB. 53 protected entries remain byte-identical. No game was running or closed, and no assistant game launch, gameplay or GECK operation occurred.

Backup: C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3H-20260915-235606-6b7a5abb

DLL SHA256: 6f53637f281243bbc9e1d2566adf6cc850e8bee5cf7c70299ca03709891455f6

PDB SHA256: 292ee2664af3a68298b4229a2665778a79124fafcfccb69d6501db7a9e89ee64

Reversal: close New Vegas and restore both files from this backup's originals/Data/NVSE/Plugins to the matching game folder. That restores native317. ESM/ESP, profiles, activation and saves require no change.

Expected: native version318 / phase3H, HIT_TX_HOOK_READY, HIT_TX_READY and HIT_TX_BEGIN/STAGE/RETURN/SUMMARY in game-root NVOCombatCore.log. Readiness and call ordering still require the user's live check. Damage replacement remains disabled. Follow START-HERE.html for the ordinary shot, VATS shot and punch after one reload.

# Packet 3B3 installation receipt

Installed 15 September 2026: **NVOCombatCore 0.3.3 / 303**. Game was already closed; it was not launched by the assistant. No gameplay or GECK testing performed.

Replaced only the DLL and matching PDB. Both installed hashes match the compiled release. Verified **50 protected files** unchanged, including other NVSE files, existing flight INI, NVO assets, private test ESP/batch and plugins.txt/loadorder.txt. Three inspected dependency binary hashes passed before installation. No activation edits, source-donor installation or settings changes.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3B3-20260915-110406-3d353fd4`

The backup preserves the version 302 pair under `originals/Data/NVSE/Plugins/`, the previous logs, exact plan and before/result inventories.

DLL SHA256: `e1f59d8e2f1860b170a3853ce252fca3179ae1c0abfb6da75a5368bf9ab7e93e`

PDB SHA256: `c5e512de583c0e62bcc63dddcfc5d4d658a714cf639b5564f20608a52e7eb8df`

Build: `native/NVOCombatCore/out/build-30121-28121`. Zero compiler warnings/errors. PE32 exports and matching PDB checked; timing/copy wrapper assembly inspected. These are build/static checks, not runtime acceptance.

Reversal: close New Vegas, replace the current DLL and PDB with the backed-up **302 pair together**. When restoring, unlink deployed files before copying if a mod manager uses hardlinks. Leave the existing NVOFlightPilot.esp, INI and activation in place. No save conversion is required by this diagnostic observer.

Guide: `START-HERE.html`. Await the user's six-shot/reload capture before further flight work. Read the game-root log directly when the user reports completion; do not require an attachment or repeat startup/version checks already established.

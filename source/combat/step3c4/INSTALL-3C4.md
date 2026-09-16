# Packet 3C4 installation receipt

Installed NVOCombatCore 0.3.9 / 309. The two installed files match the compiled release and debug pair. 52 protected entries were verified unchanged, including the ESM, pilot ESP, INIs, activation and other extenders.

The game was already closed. No game launch, gameplay, GECK work, load-order or configuration edit occurred. Runtime diagnostic acceptance remains pending.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3C4-20260915-145131-c45a6f28`

With the game closed, reversal restores these matching version 308 files from the backup's `originals/Data/NVSE/Plugins` directory to the same relative directory in the game folder:

- NVOCombatCore.dll
- NVOCombatCore.pdb

Installed DLL SHA256: 8b2765db4ee25950a127f356d07193467fe8dabc5535f112e7c02c88761c801d

Installed PDB SHA256: a4ee9d0028ac50573a2fbe00d4ba661c5b063b651e8afb13944d630bcc43f1dd

Build: native/NVOCombatCore/out/build-9235-26601. Zero warnings/errors, PE32 x86, two NVSE exports and matching PDB GUID 98b76d7c-6923-4ffa-acec-752bb4e592a7, age 1. Static bridge review confirms the virtual load/call wrapper preserves the original target and argument cleanup; request observations add no controller or position writes.

See INSTALL-3C4-plan.json for immutable prior hashes and INSTALL-3C4-result.json for actual transaction output. Do not rerun packaging to rewrite preimages after installation.

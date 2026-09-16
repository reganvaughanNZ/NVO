# Packet 3C5 installation receipt

Installed NVOCombatCore 0.3.10 / 310. The installed DLL/PDB match the compiled release. 52 protected entries were verified unchanged, including NVO.esm, NVOFlightPilot.esp, configuration, activation and other extenders.

The game was already closed. No game launch, gameplay, GECK work or configuration edit occurred. Runtime correction acceptance is pending.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3C5-20260915-154450-101c1fd2`

With the game closed, restore both previous version 309 files from the backup's `originals/Data/NVSE/Plugins` to the same relative game directory to reverse:

- NVOCombatCore.dll
- NVOCombatCore.pdb

DLL SHA256: 82e1fded44a347362965d836f6687baea5ab226ad062fc0e9310a4afd8dc6932

PDB SHA256: e632c3607672210f01ee1757c14a98c490f117e0e7e64fe3890019d7ccf6ff3f

Build: native/NVOCombatCore/out\build-19979-32186. Zero warnings/errors, PE32 x86, exactly the two NVSE exports and matching PDB GUID 0834b27d-631d-439b-9cfa-169f27248994, age 1.

The new bridge preserves a verified pilot's working local Z only at the engine's conditional reset. Untracked calls and failed checks replay the original instructions, with the CALL stack offset accounted for. Integration and displacement tolerance are unchanged. Actual gravity/drag success must be established from the user's next log.

INSTALL-3C5-plan.json preserves prior hashes; INSTALL-3C5-result.json records the actual transaction. Do not regenerate packaging preimages after installation.

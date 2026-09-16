# Packet 3D1 implementation boundary

## Correct the source identity, retain the native guards

The 3D user capture `489fa598bd90b87bd8cfe285f980e7bc3bbcea56dee0661b9a047b1da11a1c90` recorded four ordinary SMG shots with projectile `0017A2C6`. The original preparer instead used `0008F20F`. Base-game `WEAP 0008F217` DNAM offset 36 independently confirms `0017A2C6` (`AutoTracerProjectile`). This was a preparation error; the exact-match runtime guard correctly left those shots alone.

`prepare_combat_3d1.py` distinguishes each weapon's **actual engine projectile** from its **BallistX cartridge-data key**. It audits all four regular weapon relationships against the verified FalloutNV.esm, checks for source-form overrides in the installed NVO.esm, and verifies existing barrel/velocity/drag tuning against the supplied BallistX 5.4 archive. Standard 9mm tuning still comes from the donor row keyed by `08F20F`; `17A2C6` has no corresponding donor row. No new external reference or binary is needed.

## Exact changes

- INI: only the `[9mm-smg] source_projectile` value changes to `FalloutNV.esm:17A2C6`; the leading comment identifies packet 3D1. All six profiles, their tuning and enable flags remain intact.
- ESP: replace the payload of private `PROJ 01000808` using base-game `PROJ 0017A2C6`. Keep the existing private Editor ID and display name. Preserve the actual source model and other subrecords, clear only the hitscan flag, set gravity to zero for native flight, and set launch speed to the existing profile's muzzle speed times 70 units/metre. Preserve every other source DATA byte.
- All other ten parsed records, including the TES4 header, remain byte-identical. Group sizes change only as required by the rebuilt payload. No records are added or removed; no stock overrides or new dependencies.
- Audit all four private clones against their actual source, checking model/other subrecords, allowed flag change, projectile type, gravity, muzzle speed and unchanged DATA bytes after offset 12. These checks mirror the native loader's source/clone contract and additionally cover the omitted weapon-to-source relationship.

SMG muzzle speed remains `453 * 8 / (8 + 2 * 0.4) = 411.8181818... m/s`; G1 coefficient remains 0.155. These are retained donor tuning assumptions, not new calibration measurements.

## Native boundary

The DLL and matching PDB remain the installed build 311 pair. No C++ or assembly changes, recompilation, new hook sites, altered tolerances, damage authority, shared-record writes or cleanup rules. Only the canonical preview configuration changes under the native project. The log header still reports `0.3.11 | phase=3D`; the logged SMG source projectile and the installed file hashes distinguish this update.

Required DLL SHA256: `f91a5e6e363443a9a0ce0be6803cdb05b758122cb9e0486ad4805b5ebfb99255`.

The new release is deliberately an **Update** package with two installable files; it is not a standalone native build. Older packet source/config/releases and installation receipts remain historical snapshots. The original 3D preparer is retained for provenance; do not rerun it to build the corrected packet. Use the 3D1 preparation tool and its explicit source/cartridge mappings.

## Verification and remaining checkpoint

`RECORD-AUDIT.json` records hashes, source rows, all four mapping checks and the original/rebuilt SMG subrecords. Preparation is read-only with respect to the game; installation is a separately constrained two-file transaction with preimage verification, backups, hardlink-safe replacement, rollback and protected-file hash checks.

No game/DLL execution or GECK work is performed by the assistant. The existing pistol flight pass is preserved. Corrected SMG flight and the longer-distance rifle/Service Rifle VATS follow-up require the user's next capture. Unknown or changed equipment still uses the existing fallback. Precise contact trajectory/energy and later damage/armour integration remain outside this packet.

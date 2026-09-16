# Packet 3I: explicit record ownership

| Area | Packet disposition | Remaining work |
|---|---|---|
| Player00000007 | NVO override copies the complete FalloutNV.esm base record. RD health550/SPECIAL9/fatigue400/speed155/skill offsets100/ReganGear and the extra No Low Level Processing flag stop winning in plugin records. Original bounds/AI bytes/faction ordering are restored too; faction membership was the same set. | A normal new-game check is required. Existing saves may retain actor changes. |
| Five NVO health GMSTs | Exact existing records retained: fPCBaseHealthMult1; fAVDHealthLevelMult approximately0.1; fAVDNPCHealthLevelMult0; fAVDHealthEnduranceMult5; fAVDHealthEnduranceOffset-1. | These remain the user's balance choices. No fixed displayed HP claim. |
| RD bootstrap script000DBE | Edit the existing identity as an override in NVO, with full compiled source supplied. Original ten variable declarations remain in their order; bReportMissing is appended. Missing dependency reporting lives here. | Verify NVO contains the override and changed SCDA after user compile. Native hook readiness is still owned by the DLL/log, not bFrameworkReady. |
| RD bootstrap quest000DBF | Keep the existing start-enabled quest and its reference to script000DBE. No second bootstrap. | Later RD migration must retain/remap both quest and script references deliberately. |
| ALTQscript / ALTStartQscript | Keep their identities, declarations, menu flow, background callbacks and gameplay body. Quiet prerequisite gates accept either JIP name; compatibility diagnostics use PrintC. | GECK compile then a normal new-game/reload check. No claim these gates can diagnose absence of the script extender required to execute them. |
| Brahmin Baron background53 | Equipment, caps and theme retained; existing OnHit handler/registrations are not changed in this startup repair. | Explicitly excluded from any future coordinated-damage activation until ALTRichKidHit is migrated and both registration sites are retired. This exclusion is a future activation requirement, not a currently implemented gate. |
| RD PlayerHelp / Regan perk / ReganGear / PowerArmorTraining override | No edits or deletion in this packet. Restoring Player removes its ReganGear base-inventory link. Player had no direct SPLO/PRKR assignment of the separate help spell/perk in the audited record. | Inspect actual references and choose keep/migrate/remove for each during master removal. Do not infer these separate records were automatically applied to this test character. |

RD is deliberately retained as a master. A later migration must identify references by schema (including script SCRO lists, quest assignments and overrides), allocate/remap owned records, and verify saved-record behavior before master removal. Deleting RD.esm or removing its MAST entry would not perform that migration. This packet does not certify every legacy record clean.

The independent Ultra317 audit is already complete. This packet addresses findings03/04 and records a disposition for02; findings are not closed until the user's compiled/deployed records and startup behavior are checked. Finding01 still needs a terminal application contract. Actor speed/units/mass, region policy, first-contact and failure/admission rules remain ahead of damage. Native318 damage replacement stays off. No new full audit or live fire repetition is required here.

## Source basis

The packet uses fresh byte snapshots of the installed NVO/RD ESMs, matching the prior audit hashes, plus the installed FalloutNV.esm Player record. PLAYER-RECORD-AUDIT.json describes the exact binary change. No Bethesda whole-game source/binary is distributed; only the Player override is carried in the prepared mod.

Local xNVSE source: `NVSE-master (1)/NVSE-master/nvse/nvse/Commands_Game.cpp`, GetGameLoaded/GetGameRestarted implementations and `Hooks_SaveLoad.cpp` show the per-script loaded set is cleared on loads, while restarted is per process. PluginManager.cpp's IsPluginInstalled checks plugin registration names. JIP `functions_ln/ln_fn_game_data.h` confirms IsFormOverridden compares the overriding index to the calling script's owner. These implementations motivated preserving script identities and using GetGameRestarted only for the bootstrap report latch. Plugin presence does not imply a supported native hook/version; native318 retains its own guards.

Existing donor notices/credits accompany the packet. No additional donor gameplay code is introduced.

# Combat packet 1: startup foundation

Status: **startup and dependency checks accepted by the user** ("Packet 1 initialises successfully no more dependency errors"). No GECK compilation, DLL build or gameplay testing has been performed by the assistant. The assistant has not edited the installed NVO.esm or game Data directory. Proceed to the separately prepared packet 2A instructions; do not recreate this quest.

Historical repair: the original run showed three legacy NVOCombat UDF precompile failures, recorded in REVIEW-1.md. The prepared source corrected the JIP presence check to recognize both `JIP LN NVSE` and the older `JIP NVSE Plugin` name, and a manual dependency repair packet followed. The user's successful startup report supersedes those pending observations. Instructions below document the original packet rather than a request to repeat it.

## Your task now

1. Back up the current NVO.esm that you have been saving in GECK. Keep that backup outside the game Data directory. Do not replace it with the older workspace release copy.
2. In your GECK Extender session, use your working NVO.esm as the file receiving these changes. Create a **new script**, set **Script Type = Quest**, and paste the whole contents of `NVOCombatBootstrapScript.txt`. Its name is **NVOCombatBootstrapScript**. Compile/save that script.
3. Under **Actor Data > Quest**, create a **new quest** with Editor ID **NVOCombatBootstrapQ**. Leave its displayed Name empty, set Priority to **0**, check **Start Game Enabled**, and select **NVOCombatBootstrapScript** in its Script field. Leave stages, objectives and quest conditions empty. Keep **Run Once unchecked**, if that option is shown. Let GECK allocate the FormID.
4. Save your working NVO.esm. Tell me whether the script compiled and the quest saved. This is the checkpoint before packet 2.

Use `COPY-STARTUP.html` for a **Copy complete script** button. That page contains the same complete source as the TXT file. Create a separate quest and script: this source does not belong inside ALTStartQscript, ALTQscript or ALTBackgroundMenu. If either new Editor ID already exists, stop and report it rather than overwriting an unknown record.

**No loose files need copying into Data for this checkpoint.** The native project, dependency manifest and inventory are preparation materials. A compiled NVOCombatCore.dll is not included or required to compile this script.

## What the script does

The quest runs in GameMode and checks once per new game or successful save load, with an inexpensive guard on subsequent quest updates. Both xNVSE load/restart flags are consumed independently so they do not cause two initialization passes on adjacent frames. A new game also starts with a fresh unchecked quest variable.

It prints one console report per initialization. It does not open the console or show a message box. It uses only xNVSE commands, including IsPluginInstalled and PrintC, so missing JIP, JohnnyGuitar or ShowOff cannot break compilation of the checker itself. GECK still needs its working xNVSE/Extender script compiler; a script cannot diagnose the absence of the extender needed to execute it.

The xNVSE foundation floor is 6.3.0. The three addon checks establish presence only, not version compatibility for later packets. Future packets will declare their actual command requirements instead of claiming every older addon version is supported.

This report cannot suppress a warning emitted by another quest. The existing Alternative Start JohnnyGuitar message requires the separate edit already prepared in `source/step7/README.md`. Installing this controller alone does not remove that older message or install its missing dependency.

## Optional checks for you

When you choose to test, start a game or load a save, wait a few seconds in normal gameplay, then open the console yourself. Expect one `NVO Combat: foundation packet 1 initialized.` line followed by readiness information and `NVO Combat: packet 1 does not change combat.`

Missing-plugin lines are expected if those plugins are absent. `native plugin not installed. Expected for packet 1.` is also expected. The inspection snapshot found only jip_nvse.dll and ZeGaryHax.dll in the active NVSE/Plugins directory; that snapshot is not proof of what is currently loaded in your running game.

To inspect the quest, enter:

```text
sqv NVOCombatBootstrapQ
```

Expected variables:

| Variable | Meaning |
|---|---|
| iPacket | 1 |
| bChecked | 1 after reporting |
| iMissingCount | Count of unmet foundation prerequisites |
| bFrameworkReady | 1 if the xNVSE floor and addon presence checks pass |
| bCorePresent | 0 unless the optional prepared native project has been built and installed |
| bCombatEnabled | Always 0 in this packet |
| iRunCount | Increases once each time this saved quest state initializes |

Remain in gameplay to check that output does not repeat each second. Reload once to check that it reports once again. Loading the same older save may show the same iRunCount each time because quest variables are restored from that save; it is not a session-wide counter.

Changing readiness variables is diagnostic only: none of them can enable hit hooks in packet 1. Your usual combat, VATS and weapon statistics are not adjusted by this controller.

## Reversal

For temporary suspension, use `StopQuest NVOCombatBootstrapQ` in the console. To request a fresh report after restarting the quest, set `NVOCombatBootstrapQ.bChecked` to 0. For full reversal, restore the backup of NVO.esm and use a save from before adding this quest. Do not delete donor files to reverse this packet: it has not installed any.

## Preparation files

- `dependencies.json`: phase-specific dependencies and native build prerequisites.
- `donor-inventory.json`: archive hashes, plugin master lists and startup script evidence.
- `OWNERSHIP.md`: how to prevent overlapping donor systems as later packets are introduced.
- `CREDITS.md`: donor attribution and reuse conditions.
- `../../../native/NVOCombatCore/`: separate passive native project, also included in the packet ZIP.

The next packet is hit diagnostics. Neither donor gameplay loaders nor native damage replacement should be activated as part of this checkpoint.

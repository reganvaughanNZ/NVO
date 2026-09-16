# Step 7: console-only JohnnyGuitar warning

Prepared following the user's request to remove the intrusive new-game dependency message. This is a presentation change, not removal of the dependency.

Apply the same one-line replacement in both current GECK scripts, ALTStartQscript and ALTQscript. Preserve all surrounding checks, Return statements and existing modifications.

Find:

```text
messageboxex "Alternate Start requires JohnnyGuitarNVSE. Make sure you have it installed or this mod will not work."
```

Replace with:

```text
PrintC "NVO: JohnnyGuitarNVSE was not detected. Check the NVSE plugin installation."
```

PrintC writes to the console without displaying a message box or opening the console. Reference: https://geckwiki.com/index.php/PrintToConsole

The IsPluginInstalled registration name JohnnyGuitarNVSE matches the documented name: https://geckwiki.com/index.php/IsPluginInstalled

Read-only diagnostic observation: the inspected game-root nvse.log has LastWriteTime 2026-09-13 20:22:30, reports xNVSE 6.3.10 and lists jip_nvse.dll and ZeGaryHax.dll as loaded. It does not list JohnnyGuitar. This differs from older setup observations and does not establish the reason for the missing load. Quieting the warning does not install or restore a missing plugin. No installation was changed.

The user handles compilation and saving NVO.esm. This edit has not been compiled or tested by the assistant. No installed ESM or runtime file was edited.

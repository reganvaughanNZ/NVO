# Native load review - 14 September 2026

The user confirmed GetPluginVersion "NVOCombatCore" returned 200 after correcting a typing error. The installed DLL SHA-256 matched the compiled packet: aa91b95494d5426944b245d50024df05133a2e4b2c46f15e3a1f464077a54208.

The native log initially contained registration, post_load_plugins, post_post_load_plugins and deferred_init. A later read added exit_game. nvse.log independently said NVOCombatCore version 200 loaded correctly. Neither native snapshot contained new_game, pre_load_game, load_game or post_load_game; save/reload handling is still unconfirmed.

The user reported a crash, then reported that relaunching worked, video settings reset, and the game was working fine. The cause has not been established. Windows Application events recorded FalloutNV.exe failures at 21:15:51 (0xc0000409, FalloutNV.exe offset 0x00360ce3) and 21:17:32 (0xc0000005, ntdll.dll offset 0x00092fd9). These fault-module entries do not identify the underlying cause. The later observed log includes exit_game and the Steam loader says returned from winmain (0), consistent with shutdown reaching those points. WER archive contents could not be read with current Windows permissions; no elevation or further crash instrumentation was requested after the user's recovery report.

No game files, DLLs or settings were changed during this review. The assistant ran no gameplay tests. The user performs the remaining check: load a save, reload in the same running game, exit normally, then send the native log before another launch overwrites it. Review that result and ask before adding native hit observation. Startup success alone does not finish Step 2 or authorize damage replacement.

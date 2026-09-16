# Packet 3K inspection evidence

`actor-av-tables.json` records on-disk vtable metadata. `ITR-DamageActorValue.txt` is the deployed ITR thunk disassembly checked against the installed DLL by `tools/prepare_combat_3k.py`.

The three `actor-damage-*.obj` and `actor-damage-*.txt` pairs are exploratory disassemblies of encrypted on-disk engine bytes. They are **not valid engine instruction evidence** and must not supply hook guards or behavioral conclusions. Retained only to explain why runtime capture is needed.

Loaded engine code is captured in `../runtime-20260916-100050`, with bounded callable fingerprints in `../ENGINE-GUARDS.json`. The new replay substitutes engine reads, while checking the actual wrapper instructions and lifecycle handling. Its successful result does not establish live getter values or damage semantics.

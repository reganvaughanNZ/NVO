# On-disk code excluded from engine tracing

The on-disk controller entry C73170 starts 29 5D ED 4A, while the previously validated runtime starts with a conventional function prologue. Its disassembly does not describe the running function. Treat this disk evidence only as an identity/mismatch record, not as a valid instruction listing or a source for patch bytes. No engine code is to be included in the release packet.

A bounded read-only runtime capture is prepared in tools/read_height_route_runtime.ps1. It reads fixed movement/controller code, the projectile vtable, and two engine-code targets obtained from that vtable. It does not scan actors, invoke game functions, launch the game or write process memory.

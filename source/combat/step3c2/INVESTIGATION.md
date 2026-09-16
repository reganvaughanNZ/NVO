# Packet 3C2: direction/movement correction in progress

User authorized the next correction with “Continue” after the accepted 3C1 route review. This is the same two-private-weapon flight checkpoint, not a new combat system. Do not ask for that authorization again. User handles all gameplay; no assistant game launch or gameplay test.

Read-only investigation so far, 2026-09-15:

- Reviewed the archived 306 capture and the decoded 3C movement snapshots. The confirmed 009BF411 call supplies a caller-stack vector (0, engine speed times original timestep, 0), plus a potentially time-adjusted movement timestep. The original timestep is retained in the enclosing 009BF300 frame.
- Existing generic movement contains multiple conditional rotation/addition paths. 00930255 is only one final yaw rotation. Its preceding projectile-specific pitch rotation occurs at 009301E5. Accepting the unrelated sampled caller 008A633E would not establish ownership.
- The 0092F260 prologue saves the original argument frame in EBX and receiver at EBP-18. Existing compiled bridges preserve the relevant registers and x87/SSE state. No confirmed register-offset fix has been identified.
- Corrected interpretation of virtuals from supplied JIP headers: +214 is GetSitSleepState, +224 IsProjectile, +22C HasHealth. Earlier `queuedController` variable naming is not a verified interpretation of that virtual result.
- Need verify actual installed runtime helper bodies (pitch, heading, virtuals and process accessor), and compare movement code with the earlier capture, before choosing the write boundary. A source-derived formula must match the engine's direction convention and retain engine collision bookkeeping. Do not write projectile +104 as velocity: the existing setter stores actual step displacement there.

Prepared `tools/read_flight_direction_runtime.ps1`, derived from the earlier approved read-only capture helper. It reads fixed engine-code/vtable ranges twice from the exact FalloutNV.exe process and saves only stable bytes inside this workspace. No process writes, injection, execution, launching, suspension or gameplay. The original helper remains unchanged. Captured engine bytes must not be included in release/source archives.

Requested the user leave the game at the main menu and reply “open”; that input is pending. Game was closed at the latest check. No native source changes, compilation, installation, configuration or plugin changes have been made in this correction yet. Installed 306 remains. Once the needed evidence is obtained, finish this packet, compile and statically inspect it, install with the existing backup/protected-file workflow, then stop for the user's new gameplay result. Closing the exact game process for installation is already authorized.


## Completed this continuation

User replied open; fixed-range captures and the correction build/install are complete. See IMPLEMENTATION.md and INSTALL-3C2.md. The earlier pending request above is historical. Installed 307 now awaits the two-shot gameplay result. No further permission or main-menu capture is needed for this packet.

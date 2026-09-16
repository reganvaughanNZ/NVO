# Packet 3C4: controller request diagnostics (309)

Purpose: identify the concrete movement implementation and compare its request before and after processing. Packet 308 proved that the caller's written local Z survives, while the movement candidate omits its contribution. It did not identify the controller's actual dispatched implementation. This packet closes that evidence gap; it does not assert a gravity correction.

The only native movement write remains the previously guarded 12-byte input for two exact private pilot combinations. Integration, one unchanged baseline, displacement tolerance, collision handling and mismatch retirement remain unchanged. No armour, damage, VATS expansion, ordinary-ammunition changes or new dependencies. Existing six hit/observer/timing/preview/log source modules remain identical to 308. No GECK record change.

The three new observer spans are taken from the previously captured and decoded generic movement body (step3c3/runtime-20260915-141533/movement-0092F260). Its complete existing fingerprint still guards them:

| Span | Original operation | Observation |
|---|---|---|
| 0092FFEA, 8 bytes | MOV EAX,[EDX+C8]; CALL EAX | Actual virtual target, controller and request immediately before dispatch |
| 0092FFD4, 5 bytes | CALL 00C70B60 | Alternate direct-call request |
| 0092FFFB, 5 bytes | CALL 009304B0 | Both branches have returned, before the existing listener flag query |

The generic argument frame is saved EBX, distinct from aligned EBP. Require return 009BF416, the pending private owner, original bullet input pointer and thread. Request must be generic EBP-208; receiver must match frame-local controller (post-call receiver is controller+410). Pair request entry/return using controller, frame and argument-frame identities. Reads use the initialized request fields at +00 (dt), +04 (rotation), +10 (input), +1C (flags), +20 (uninterpreted auxiliary float), +24 (byte). Padding is not logged. Failed contracts stop subsequent edits for that track; they cannot undo a previously attempted segment.

PHYSICS_CONTROLLER and PHYSICS_CONTROLLER_ARGUMENT record the request, original caller input and concrete vtable/target. PHYSICS_SHOT includes controller entry/return/pending counts. Absence of controller rows is evidence that this observed branch did not execute, not proof of a corrected trajectory.

To avoid requiring another main-menu memory capture solely to identify the target, PHYSICS_CONTROLLER_CODE records up to 2,048 executable bytes at each of at most two observed targets per process. VirtualQuery requires committed executable MEM_IMAGE memory belonging to the game executable, and the read never crosses its region. No jump/call following, arbitrary heap dump or code execution. Length, offsets, FNV64 and end marker let the review detect incomplete captures. These diagnostic reads share the existing log limits; no additional console output. Captured executable bytes are generated in the user's log and are not included in the distributed packet.

All bridges retain GP registers, EFLAGS, x87/SSE/MXCSR and original arguments/receiver. The eight-byte virtual span uses CALL bridge plus three NOPs: the bridge recreates the original target load, observes saved state, then tail-jumps to that exact EAX. The original callee pops its argument and returns through those NOPs to 0092FFF2. Other bridges tail-jump to the original direct functions. No extra engine calls and no lock spanning the engine call.

Seven owned spans occupy three pages. Variable-length normalization requires a fully contained exact owned patch; partial/foreign modifications fail. Protection, restoration and rollback cover all spans including the eight-byte load/call. The new observers never set controller state, request fields, object positions or angles, and never substitute the final position after collision.

Install the matching DLL/PDB only. Retain NVO.esm, NVOFlightPilot.esp, private ammunition, INIs, load order and dependencies. Backup and actual hashes are recorded separately in INSTALL-3C4.md and INSTALL-3C4-result.json. Compilation/static source/assembly/PE/PDB review is performed by the assistant; runtime acceptance belongs to the user.

User checkpoint: load the prepared save, wait three seconds, fire one private Hunting Rifle shot and one private 9mm shot at the same distant solid scenery outside VATS, pause between shots, exit normally and report finished. God mode is fine. No additional reload, stress test, video or GECK work. The known mismatch may recur. Review request entry/return, dispatched target/code, candidate and actual displacement. Do not accept physics on the basis of an armed message or a successful compile. Ask before another packet.

Reversal: with the game closed, restore the matching prior DLL/PDB from the installation receipt's backup. The existing NVOFlightPhysics.ini enabled=0 also disables this movement pilot for the next capture. Console-spam cleanup remains separate pending one exact repeated message; this packet adds no console notices.

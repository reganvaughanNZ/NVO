# Packet 3O: offline admission and application simulation

`AdmissionLedger` wraps the existing pure `Resolve` model with bounded identity and lifecycle bookkeeping. It is **not linked into NVOCombatCore**. There are no NVSE calls, engine callbacks, projectile setters, health/limb/armour setters, serialization, logging interfaces or real application functions. `BeginSimulatedApplication` and `AcknowledgeSimulation` only change an enum in this offline object.

## Contract

- One immutable owner thread. Foreign-thread operations return before reading mutable ledger state. Runtime multi-thread support, marshalling and engine continuation lifetime are not implemented by this class.
- A session has a strictly increasing nonzero epoch. Every reset invalidates earlier tokens; it does not undo gameplay or cancel engine stack frames.
- The key is `(session, component, application, target form ID)`. Source/target incarnation IDs, source, mode, actual region, component kind, family and five snapshot revisions must also match on repeated observation. A mismatch is a conflict, not a second admitted hit. Providers must supply verified IDs: these are not weapon/frame/time heuristics.
- Each pellet, beam component or exposure interval needs a verified distinct component/application identity. A blast may share a component while addressing different targets. A piercing carrier can have distinct applications. The class cannot establish any of these identities from game memory.
- `Reserve` consumes one of at most128 retained slots. Invalid capacity closes admission. Duplicate/conflicting identity is checked even when capacity is full. No active entry is evicted; diagnostic budgets are absent from this decision.
- Tokens carry a ledger cookie, session, slot and monotonically increasing generation. Reset/reuse/cross-ledger access cannot revive a stale token. Cookies/generations fail closed rather than wrap.
- `ResolveReserved` validates matching revisions/family, limits the supplied armour snapshot to16 layers, then calls the existing pure model. Unsupported inputs, changed revisions or allocation failure reject before a simulated application. The caller is responsible for obtaining a coherent snapshot and truthful verification/revision fields; this is not an engine snapshot reader. Model output is retained by value.
- Only `Reserved -> Resolved -> SimulationStarted -> Acknowledged` reaches completion. Repeating a start/acknowledgment is rejected. Rejection before simulated start becomes `Rejected`; failure afterward becomes `Faulted`, preventing retry and retaining uncertain ownership until the next session.
- Completed/rejected entries remain as duplicate history. `RetireThrough` requires explicit verified producer closure and preflights the entire requested range before freeing anything. Active/faulted entries block that range. A retained monotonically increasing component boundary rejects delayed lower-ID events after slots are reused. **A runtime adapter must prove this ordered closure; it must not pass true from elapsed time or a log limit.** Without closure the ledger fills and denies new work; bounded memory takes priority over inventing a safe lifetime.

Kinetic and plasma admit projectile contexts, laser admits beam or projectile contexts, flame requires an exposure context, and blast requires a blast context. Unsupported/miscellaneous families remain unsupported. This classification is for fixtures only and is not evidence of live family support.

## Validation

`run_admission_checks.cmd` compiles x86 MSVC C++17 with `/W4 /WX` and runs47 checks. They cover duplicate/history preservation, identity conflicts, snapshot changes, capacity exhaustion without eviction, stale/cross-ledger/reused-slot tokens, partial-application faults, atomic retirement, reload epochs, foreign-thread rejection, distinct pellets/applications/blast targets, family separation, invalid model inputs and1000-component traces with external logging absent/failing/succeeding. The ledger itself has no logger API. Allocation failure and numeric counter exhaustion are guarded in code but were not induced by these fixtures.

This does **not** close the real projectile reservation problem in Ultra317-07 or convert diagnostic caches to gameplay storage. Flight selection presently changes the private projectile before live physics admission; a separate runtime fix must reserve that actual tracking capacity before substitution and handle post-selection failures. This hit ledger cannot reserve pre-flight target/armour information that does not yet exist.

Engine component identity, contact speed and70-units/metre calibration, actual region/VATS interpretation, modifier ownership, critical/ammo effects, per-family adapters, exact application boundary and eventual engine acknowledgment remain open. No fixture result authorizes damage replacement. Native320 remains installed, with damage replacement disabled.

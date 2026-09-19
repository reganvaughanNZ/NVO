# Packet 4I1 review

Independent source tracing checked xNVSE callback equality, removed/revived state, deferred cleanup, flush ordering, ITR listener caching and the public API table. The normal deferred-removal theory was rejected. Public query false remains ambiguous, and registration is never called emission readiness.

Production changes are confined to the event prefix/lifecycle monitor, a scalar post-transaction notice, version labels and documentation. The notice leaves the transaction lock before calling the monitor. No registry API runs in the hit; no arbitrary event is dispatched. API calls stay outside the monitor lock, reentrant Tick is refused, and every external-call sequence is cancelled by a changed lifecycle generation or invalid epoch. Lifecycle cancellation does not reuse old counters. Scheduled checks and gap checks are bounded per session.

The pure query is positive-only. A Set call may safely be attempted with ambiguous prior presence, since the inspected implementation does not duplicate active registrations. It may also refuse; this remains explicit. A monitor-active flag means diagnostics are enabled, not that registrations or emission are proved.

Standalone tests compile the production DamageEvents translation unit against synthetic module/form memory and a source-derived registry mock. They exercise contracts and cancellation, not real xNVSE or ITR execution. Existing production transaction tests cover the new notice boundary; copy receipt regressions remain separate. See Evidence/VERIFICATION.json for fresh counts and compiler/binary evidence. Unchanged model/reader tests are not repeated or presented as new results.

No live fix, timing improvement, atomic impact state or damage authority is inferred. Installed328 and its prior live evidence remain separate from prepared329. After installation approval a short three-hit, one-reload check will establish whether registrations and real callbacks survive together.

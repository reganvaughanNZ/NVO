# Packet 3G: collision-step speed diagnostics

Native 315 / 0.3.15 records the collision step before the delayed impact callback. It distinguishes the starting speed, proposed full-step speed and a possible model-based contact-speed estimate. This is preparation for armour inputs; estimates do not control damage.

The prior terrain correction is accepted and retained. Only NVOCombatCore.dll and its matching PDB are replaced. Keep NVO.esm, NVOFlightPilot.esp, their masters and all current configuration. No GECK work or new dependency is needed.

Follow START-HERE.html for three shots: very close solid-object impact, normal hit on a live target, and a farther VATS hit on another live target. No reload cycle, stress test or deliberate long miss is required.

Look for IMPACT_STEP, IMPACT_GEOMETRY, IMPACT_VELOCITY, IMPACT_MODEL, IMPACT_CALLBACK and IMPACT_SUMMARY in the game-root NVOCombatCore.log. The assistant will read the log directly when you finish. A candidate estimate is not an authoritative or directly measured contact speed. First-step collisions and ambiguous geometry are explicitly left without an accepted estimate.

Installation/IMPLEMENTATION.md describes the observations, limits and reversal. Installation/INSTALL-3G.md records the exact two-file backup after installation. Donor notices and complete native source remain included.

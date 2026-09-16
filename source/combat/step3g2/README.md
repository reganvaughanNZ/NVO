# Packet3G2: collision and current-hit diagnostics

Native317 /0.3.17 records the physical contact region beside the engine's current hit-data region, with any supported speed candidate. It does not choose an armour region, change hit outcomes, enable damage or assume a VATS targeting rule. The user's possible torso strike after a head aim remains a hypothesis.

The record is taken at the existing CopyHitData input observer. It verifies source, target, weapon, ammunition, projectile identity and fresh contact before linking the earlier candidate. Contacts before movement are labelled explicitly. Invalid geometry stays unavailable and tolerances are unchanged. The later impact callback remains independent confirmation, not a prerequisite for a hit already processing.

Only NVOCombatCore.dll and its matching PDB are replaced. No GECK work, new dependency or configuration change. Keep NVO.esm, NVOFlightPilot.esp and their current masters active.

Follow START-HERE.html:1 close rock outside VATS,2 live target aimed at the head in VATS at your previous farther distance,3 live target aimed at torso outside VATS at similar distance. A kill is not required; another live target if needed. Wait3 seconds between impacts, at most1 replacement per missed check, then20 seconds after the last shot and exit normally. Report aim/mode and observed result; uncertainty is useful. No reload or stress test. I will read the game-root NVOCombatCore.log directly.

New rows: IMPACT_HIT, IMPACT_HIT_MODEL, IMPACT_HIT_POSITION and IMPACT_HIT_SUMMARY. The joined diagnostic has a64-query/192-row limit; existing impact detail covers32 lifetimes. All speed/region/damage authority remains0. Offline replay and negative checks pass; live317 confirmation is pending.

PRE-DAMAGE-REVIEW.md records the requested Ultra review gate and full plan reminder. That review has not yet run. Source, notices, build/replay evidence and two-file rollback instructions are included.

"""Write the bounded source-review findings; does not edit either runtime."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'reference/legacy-nvo-review'
OLD=Path('C:/Users/regan/Documents/Codex/2026-08-16/can-you-explore-and-create-a')
V09=OLD/'outputs/nvo-realism-hybrid-v0.9.0'
V10=OLD/'outputs/NVO-Realism-v1.0.0-dev-staged'
WORK=OLD/'work/nvo-realism-hybrid-v1.0.0-dev'
def udf(name,line=1,root=V09):
    return f'[{name}](<{(root/"Data/NVSE/user_defined_functions/NVOCombat"/name).as_posix()}:{line}>)'
summary=json.loads((DEST/'inventory.json').read_text())['summary']
report=f'''# Legacy NVO source evaluation — 15 September 2026

**Verdict: preserve it as a reference library and selectively port its data and design safeguards. Do not merge or reactivate the old runtime.** It has sensible file boundaries, but shared state and overlapping damage/recovery authority make the combined system difficult to reason about. “Structured prototype with tightly coupled behavior” is more accurate than calling all of it spaghetti.

This is a static source review, not a compile, gameplay or performance test. No installed files, native source, old scripts or load order were changed. Combat packet 3C4/309 remains awaiting the user's separate test result.

## Scope and provenance

Reviewed the relevant history in **Explore NVSE scripting context**, including the user's August test reports of repeated collapse and a crash, and the distinction between the profile named “NVO Realism v0.9 Runtime Test” and the later “NVORealism-Milestone1-hotfix2” package. Also consulted **Summarise NVO Project** for historical design context, not as proof of implementation.

Located the actual v0.9 output, v1.0 staged output and v1.0 work tree under `{OLD.as_posix()}`. Inventory: {summary['v09_udfs']} v0.9 UDFs, {summary['v10_staged_udfs']} staged v1.0 UDFs, {summary['v10_work_udfs']} work-tree UDFs. **33 of 39 v0.9 UDFs are byte-identical in staged v1.0**, including the collapse, wound tick, organ tick, recovery and armour/ballistics resolvers. The later version therefore retains the central problems described below.

Reviewed the key control paths rather than claiming a line-by-line audit of every historical version. The exact hotfix2 deployed archive has not been byte-matched to these trees. The source can explain a credible collapse mechanism; it does not establish the cause of the historical crash. File hashes and variant differences are recorded in [inventory.json](inventory.json).

## Important findings

**1. Repeated collapse is deliberately maintained by the control flow.** {udf('NVO_ApplyFunctionalState.txt',136)} targets fatigue damage whenever the actor is collapsed. {udf('NVO_ReconcileActorValue.txt',27)} detects outside healing, reduces its recorded ownership, then reapplies damage to reach the desired target. {udf('NVO_WoundTick.txt',219)} explicitly keeps the timer alive while collapsed. Together, these can counter recovery from fatigue until the underlying injury clears. This matches the reported symptom; a crash would need separate runtime evidence. Replace with bounded reactions and an explicit recovery/cooldown policy when implementing current Step 6.

**2. The armour resolver cannot make the original engine hit obey its penetration result.** {udf('NVO_OnHit.txt',58)} reads engine hit damage and subsequently dispatches extra blunt, wound and organ processing. Its comments explicitly preserve the engine transaction. A stopped NVO penetration result therefore is not a veto on the original damage. Wound, mechanism and organ tick modules also call DamageAV Health separately, with separate limits rather than one coordinated total. Keep the current plan's single direct-hit authority and separately attributed continuing effects; do not import this additive damage pipeline.

**3. Its ballistics are an estimate at hit time, not projectile flight.** {udf('NVO_ResolveBallistics.txt',47)} uses the attacker's current ammunition, falling back to the weapon's default. Lines 130–149 estimate velocity from current attacker-to-target distance and a linear drag fraction. That can disagree with the ammunition fired and distance travelled after movement or an equipment change. The resolver is useful for finding old equipment mappings; it is not a substitute for BallistX or the native projectile tracking we are developing. Its unknown-equipment fallbacks also conflict with the current policy of retaining unknown equipment's existing behavior.

**4. Medical recovery is more restrictive than the current design.** {udf('NVO_ProcessOrganTick.txt',42)} continually enforces bleeding floors from organ deficits and critical organ consequences. {udf('NVO_ApplyOrganTreatment.txt',14)} excludes treatments other than Doctor's Bags and clinical care; viable organs alone can receive clinical repair. Waiting on the ordinary recovery routine does not repair the organ channels. These restrictions help explain why ordinary healing could leave an actor trapped in impairment. Keep wound categories as reference, but design treatment around familiar New Vegas medicines and the agreed scarce advanced treatment. Do not silently reinstate ten mandatory organ pools.

**5. File separation exists, but state ownership is tangled.** The hit path passes intermediate results through actor AuxVars such as `_NVO_State`, `_NVO_OrganState`, `*_NVO_BallisticResult` and `*_NVO_ArmorResult`, with positional numeric slots. The wound timer coordinates mechanisms, organs, recovery, functional impairment and morale. Separate health/AP writes and tick-based effects interact with game-time recovery. Port named, versioned data structures and explicit results, not this shared mutable state layout. The ownership-reconciliation idea is worth preserving, but its measurement limits and interaction with medicine require redesign.

**6. Several later features are APIs rather than completed gameplay.** {udf('NVO_EmitImpactFeedback.txt',72,V10)} dispatches an event and records state; the inspected staged text scripts contain no subscriber implementing HUD/sound feedback. {udf('NVO_CreateJobOffer.txt',1,V10)} stores an offer for a future presentation/acceptance module. The work-tree civic activation observer also emits a signal without opening a menu or assigning a quest. These are useful contracts, not a finished jobs/economy system. The older Courier bridge explicitly looks up AltStart.esm; it cannot be transplanted unchanged into the merged NVO.esm setup.

## What to salvage

| Area | Decision | Destination in current plan |
|---|---|---|
| Ammo/weapon EditorID mappings and construction categories | Extract and verify against current records; treat numbers as unvalidated tuning | Step 3 loose profiles |
| Armour material, coverage and helmet tables | Useful seed data; re-evaluate protection and condition math | Step 4 |
| Biological versus mechanical anatomy | Keep the distinction and explicit exceptions; simplify biological injury state | Step 5 |
| Save schema, death cleanup and bounded treatment budgets | Reuse the safeguards as requirements, rewrite for native serialization and current medicine | Step 5 |
| Ownership-aware restoration | Retain the goal of not healing unrelated damage; do not reuse collapse enforcement | Steps 5–6 |
| Separate contact/explosion handling | Keep as a checklist; rely on current verified native event evidence | Steps 2 and 6 |
| Local tactical impact memory and doctrine tables | Useful starting concepts for perceived danger; reassess thresholds and control ownership | Step 7 |
| Impact-feedback event and cooldown | Adapt to one resolved-hit result with an actual presentation consumer | Steps 5–6 |
| Civic roles, needs, memory and job-offer schemas | Retain for later sandbox design; unfinished implementation | Later, outside combat packet scope |
| Old startup loaders, additive trauma, persistent fatigue collapse | Do not reactivate | Retire from executable integration |

The loader's remove-then-register approach, profile readiness checks, one actor timer, migration, cleanup, bounded values and companion/essential surrender exclusions show real defensive effort. The old tests also contain useful invariant ideas. However, the inspected organ test recreates formulas in PowerShell: passing those assertions does not execute NVSE callbacks, actor-value recovery, VATS, saves or ragdoll behavior. Historical “validated” wording must not substitute for runtime acceptance.

## Integration decision

No additional DLL or dependency is needed merely to salvage this work. Keep an indexed reference to it, then extract only the relevant profiles when the existing combat plan reaches their owner. Do not run both old and new injury controllers. Packet 3C4's projectile/controller test remains the immediate combat checkpoint; this review does not advance or replace it.
'''
# Resolve the one local artifact link to an absolute path for Codex rendering.
report=report.replace('[inventory.json](inventory.json)',f'[inventory.json](<{(DEST/"inventory.json").as_posix()}>)')
(DEST/'REVIEW.md').write_text(report,encoding='utf-8')
print(str(DEST/'REVIEW.md'))

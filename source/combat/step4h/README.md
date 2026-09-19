# Packet 4H: bind impact evidence before numerical preview

Prepared offline. The purpose is to prevent contact information and armour state from different hits, copies, or reloads being combined into one plausible result. This packet adds an evidence gate to the kinetic material preview. It does not supply a live capture implementation.

## What changed

`ImpactBinding` compares independently captured producer stamps with the current consumer's expected scope: generation, session, transaction, copy ordinal, projectile lifetime, component, application, profile, actor/projectile/weapon/ammunition identities, literal region and mode. Missing or mismatched data stops the preview before arithmetic. Successful results retain the scope of their call-local item tokens.

Producer types explicitly distinguish segment means, owned-step intervals, point estimates and muzzle estimates from a reserved verified exact-contact contract. Stable equipment copies are likewise separate from the reserved verified-at-impact contract. Current diagnostic producers cannot qualify simply by setting the old generic verified flags. These checks supplement all existing region, units, condition, complete-surface, order, anatomy and modifier gates.

MaterialPreview contract version is now 2. Numeric formulas, provisional coefficients, other-family support and the native DLL are unchanged. The native source version remains 0.3.27/327. Damage, wear and stagger remain disabled.

## What the audit found

Current flight evidence provides speed estimates or bounds, not an exact calibrated speed at the proven contact. Collision reread agreement is not proof of agreement with the hit-data position. Current armour reads establish bounded consistency but not atomic impact state. The flight query also lacks a complete binding to the armour copy and component/application.

Those live requirements remain open. The new gate makes these missing requirements explicit; synthetic passing fixtures do not complete them. See [INPUT-AUDIT.md](INPUT-AUDIT.md) for the source trace and [BINDING-CONTRACT.md](BINDING-CONTRACT.md) for the caller contract.

## Offline checks and evidence

Run `native\NVOCombatModel\run_binding_checks.cmd` and `run_material_checks.cmd` in the checkout; in this package the same runners are under `Source`. They compile standalone x86 executables with MSVC, then run binding, material, model, shadow and definition checks. No DLL is loaded or installed. `tools/prepare_combat_4h.py` runs those checks, verifies baseline hashes and creates the review package; it is a checkout tool, not a game installer.

Fresh results and source hashes are recorded in [Evidence/VERIFICATION.json](Evidence/VERIFICATION.json). These are synthetic correctness checks, not measured physics, balance, performance, or live acceptance. Rejected preview cases must expose no partial numerical result.

## User action and reversal

No installation, GECK edit or gameplay test is required for this packet. Nothing in the game folder changes. Review [START-HERE.html](START-HERE.html); the next packet needs approval.

To reverse offline development, restore the four changed 4G input files from the retained 4G package as one set: MaterialPreview.hpp/.cpp, material_preview_tests.cpp and run_material_checks.cmd. Remove the new ImpactBinding files, their dedicated tests and runner only if no later work depends on them. No save or game rollback is needed. Do not mix the version-2 consumer with version-1 fixtures.

## Next proposed packet

Define and implement component-bound **diagnostic** capture, carrying transaction/copy scope consistently through contact and armour observations. Capture must preserve separate actual evidence and unknown fields, with reload, duplicate and reentrancy handling. It must not assign synthetic component/application identities or declare exact speed/atomic equipment state merely to pass this gate. Prepare the native change separately; building, installing and live acceptance remain distinct checkpoints.

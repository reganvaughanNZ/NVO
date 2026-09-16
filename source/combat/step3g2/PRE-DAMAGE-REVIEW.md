# Ultra review before damage: agreed checkpoint

User request2026-09-15: continue3G2; use Ultra to check everything relevant before adding damage, as efficiently as possible. This requirement is part of the development plan. **Review status: not yet performed; damage replacement stays disabled.** It is not a scheduled automation or a claim of review approval.

## Plan reminder

1. Foundation: dependencies, ownership and quiet startup (completed for the current pilot).
2. Observe hits: bullet/pellet/melee/explosion identity and current hit context (existing diagnostic checkpoints; limitations remain explicit).
3. Projectile flight: BallistX-derived drag/velocity, private profiles, collision/lifecycle handling. **Current work:3G2 pairs collision diagnostics with hit-data input.** Unit calibration, immediate-contact ownership, supported-input coverage and pre-damage handoff still need decisions/evidence.
4. Armour and coordinated damage: penetration, transferred impact, health/limb damage, helmet/body coverage and wear. **Ultra reviews the foundation before we implement damage replacement.** After that review and its material fixes, damage code can be developed disabled or as diagnostics. Check only the new damage code and affected interfaces before a separate user-approved activation packet.
5. Physiology, wounds and medicine: biological versus mechanical injuries, bleeding, treatment and persistence; build around the game's powerful medicines without excessive treatment complexity.
6. Weapon behavior: remaining damage types, energy/flame/explosives, poison, spread and controlled impact effects.
7. AI and morale: decision timing, retreat, then surrender separately.
8. Starting backgrounds/loadouts balanced against the finished combat rules. Permadeath is a design assumption; no forced save deletion/loading restrictions.

## Efficient review workflow

Freeze the exact current pre-damage source/build/configuration after the3G2 live checkpoint and any required foundation decisions, before starting damage implementation. Prepare a compact indexed manifest of hashes and evidence. Run **one independent reviewer at reasoning_effort=ultra**, using the existing model unless the user chooses another. The current task tools expose this effort; do not claim this task silently switched effort. Use a fresh/minimal context with this review brief and indexed files, not the entire conversation or every historic packet. User authorization for this review is already given; do not ask again merely to run it at the agreed gate.

Review all active combat code and interfaces once, then follow specific unresolved references. Preserve a findings register with severity, exact file/line, evidence, confidence, consequence and the smallest necessary fix/check. Report code defects separately from unsupported assumptions, planned features and missing gameplay evidence. Fix material issues in the normal development task. Ask the same reviewer to check only changed code, affected invariants and unresolved findings. Do not pay for repeated full audits or duplicate reviewers without a concrete reason. Routine builds, packaging and log extraction do not need Ultra.

Scope/stopping rules matter more than an open-ended instruction to think harder. This workflow follows the official guidance to calibrate checks to the change and stop broadening once relevant checks pass: [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model#testing-and-verification). It is a chosen project workflow, not a guarantee that an effort setting proves correctness.

## Review input index

- Current native source: native/NVOCombatCore/include and src; BUILD.cmd, CMakeLists.txt, manifest.json and config. Inspect all active files, including hook guards, memory reads, register/FPU preservation, lock ordering, bounded tables/logging and resets.
- Source provenance: native/NVOCombatCore/reference, THIRD-PARTY-NOTICES.md and donor licenses/credits. Read the referenced donor functions/data actually used, not every unused donor repository.
- Active records/loaders: source/combat/step1 foundation manifest/startup script and its repair review; the latest installer plan/result and protected-file backup manifest enumerate the deployed state. Inspect current NVOFlightPilot record/profile sources and any active damage-changing loader; preserve one owner per enabled feature. NVO.esm/RD.esm master removal remains separate work, but any current combat dependency or duplicate loader is in scope.
- Build/install: current packet STATIC-CHECKS.json, SOURCE-DIFF.txt, build-evidence, replay result, DLL/PDB hashes and transaction receipt. A source review alone does not establish that matching bytes are deployed.
- Hit observation history: source/combat/step2/REVIEW-5-current-hit-capture.md, REVIEW-6-body-hit-capture.md, REVIEW-7-reload-melee-energy.md, and step3b3a body-region evidence. Read underlying captures only where an assertion needs checking.
- Flight/lifecycle evidence: latest reviewed checkpoints from3C/3D/3E/3F; step3f3/REVIEW-1.md is the accepted failed-terrain/range exercise (capture3130ae056efd).
- Collision evidence: step3g/REVIEW-1.md (018ec6d9b0b6); step3g1/REVIEW-1.md (9a54c6410f44); step3g2 implementation, source findings, offline replay and pending live review. The latest user says their VATS attempt may have missed the intended head and struck torso: preserve that as a hypothesis alongside both recorded regions, not a resolved explanation.
- Product contract: this plan and current packet. Do not demand finished wounds, economy, morale or all donor integrations as if they already exist. Identify their interfaces and future risks separately.

## Questions the review must settle before activation

1. Is there one supported, guarded damage application path, preserving attacker and ammunition identity without duplicated health/limb damage? Can it act at the required time, before the observed late callbacks?
2. Are collision contact, intended/observed aim and engine hit-data region distinct? What determines helmet/body protection under VATS and ordinary shots? Which producers and fallback cases are actually verified?
3. Are model units, mass, energy, velocity/contact-time estimates and numerical tolerances justified? Are immediate contacts, unavailable geometry and unknown equipment handled honestly with an explicit policy?
4. Do reload, quit, destruction, pointer reuse, threaded callbacks, nested hooks and log/cap limits leave no stale state or ownership conflict? Are native guards and unload/shutdown assumptions safe?
5. Are pellets, explosive impact versus explosion, melee, energy/flame, robots and critical effects classified without double processing or unsupported anatomical precision? Separate completed evidence from remaining checks.
6. Do editable records/profiles and planned treatment/save interfaces stay modular? Does the implementation preserve the agreed gameplay loop and future compatibility?

Completion means a written review and resolved material findings plus explicitly accepted limitations for the enabled scope. Record exact version/hashes and outstanding user gameplay checks. Do not mark everything safe because compilation passed, do not enable damage automatically, and do not claim this gate has run until the Ultra review actually returns.

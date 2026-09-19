# Packet 4G - Offline kinetic material preview

Prepared offline. Native core remains 0.3.27 (327). No game installation, GECK edit or gameplay test is required for this packet.

This packet connects 4F's material/target definitions to numerical ballistic previews: stopping/penetration, transmitted impact, condition-dependent protection, worn-item wear, and separate natural/robot structure losses. It preserves actual authored engine-region IDs instead of forcing creatures into the older humanoid region enum. Numerical profiles and game evidence in the checks are **synthetic**, not production tuning or measured armour behavior.

## What changed

`MaterialPreview.hpp/.cpp` selects definitions itself, verifies evidence, binds exact numeric response IDs, evaluates condition curves and returns one component's preview. It is a pure offline function with no hooks, mutation callback or application API. Every accepted result remains `PreviewOnly`.

The stopping/transmission arithmetic was extracted into `ArmourModel::ResolveKineticLayers`, shared by the old kinetic preview and this bridge. The old preview calculates stopping capacity as resistance multiplied by actual item condition. The new path uses an authored condition curve or an explicitly condition-independent response. Both paths preserve actual condition for wear limits; neither forces item condition to one. Independence sets the protection scale to one, not the item's condition. Shared identity/mode and projectile/speed evidence checks were extracted from `ShadowAdapter` without relaxing them.

Worn instances with the same profile remain separate, with distinct keys and wear. Natural protection and chassis entries require their own complete mapped set and return different owner channels. Empty inventory cannot certify a creature as unprotected. Actual contact flags and independently verified ordering are mandatory. Bypassed surfaces contribute no protection or wear; an unprotected contact requires explicit bare evidence.

For a positive-energy bare hit, `protectionPenetrated` stays false because no protective surface was crossed. A false value does **not** mean the target was protected or the attack was blocked. Consumers must first check result status, then interpret contacted surfaces, residual energy and the separate wound/payload flags. Biological penetrating-wound/payload eligibility is separate from mechanical health/structure damage. These are preview flags only, not injury scripts.

## Attack scope

The new numerical bridge admits only the 4F `Ballistic` family with verified per-projectile inputs. Its accepted delivery categories are `Projectile`, `Pellet` and `Fragment`, subject to all evidence gates; the packet creates no fragments and does not provide a live fragment adapter. A profile's mass belongs to one projectile/component, never a whole shell copied onto every pellet. The other ten families return explicit unsupported results through this bridge, even though the older model contains provisional dose examples.

Those ten families are `Piercing`, `Cutting`, `Blunt`, `Blast`, `Laser`, `Plasma`, `Flame`, `ExternalHeat`, `Electrical` and `EMP`. Together with `Ballistic`, they are the eleven entries before the `Count` sentinel in `nvo::responses::Family` in `ResponseDefinitions.hpp`; `Count` and `Unknown` are not attack families. `Melee` and `Thrown` belong to the separate `Delivery` enum. For example, a thrown axe can use cutting or blunt interactions; its delivery is not an additional damage family.

All eleven family definitions remain in 4F. Separate measurements/rules are needed before introducing the other ten numerical paths. Existing game behavior is unchanged by this offline work. There is no cast between the 11-family definition enum and the old five-family model.

Read [MODEL-RULES.md](MODEL-RULES.md) for formulas, units, assumptions, evidence gates and the link to future stagger. Read [REVIEW.md](REVIEW.md) for review findings and limits. Fresh results and source hashes are in `Evidence/VERIFICATION.json`.

## Validation and files

Active implementation is under `native/NVOCombatModel/`; release copies live under `Source/`.

```bat
native\NVOCombatModel\run_material_checks.cmd
```

The runner discovers installed MSVC x86 tools, builds standalone checks with `/W4 /WX`, and runs the new bridge tests plus the existing model, shadow-adapter and response-definition regressions. An extracted release uses `Source\run_material_checks.cmd`. Outputs go to `out-material/`. No DLL is built or loaded. The fixtures are copied with their checked sources, not linked to game libraries.

`tools/prepare_combat_4g.py` runs those checks afresh, records source/evidence hashes and verifies the release/ZIP manifest. It has no game path, installation step or launcher. Previous release snapshots are unchanged; historical preparation scripts pinned to earlier source hashes may correctly refuse newer active source.

## Limits and reversal

This does not prove live speed authority, an atomic impact snapshot, actual struck coverage or engine modifier ownership. The new numeric adapter will reject missing evidence; existing observed speed intervals are not silently converted into exact contact speeds. No runtime damage, wear, wounds or stagger is enabled, and no force/impulse is calculated from energy or HP. Coefficients are intentionally not mapped to actual game records yet.

Nothing was installed. Reversing 4G is a workspace change: revert the shared-core/gate refactor together with the new module and its docs. Game plugins, load order and saves need no action. The existing runtime DLL and coverage configuration remain outside this packet.

After approval, the next useful checkpoint is to address the remaining authoritative contact-input and impact-snapshot integration gates before considering a live shadow-only bridge. Do not repeatedly test unchanged gameplay or enable replacement damage merely because these offline fixtures pass.

No new runtime dependencies or donor implementations were introduced. Existing credits and component notices are preserved. The packager copies the repository's mixed-license notices without assigning a new blanket license.

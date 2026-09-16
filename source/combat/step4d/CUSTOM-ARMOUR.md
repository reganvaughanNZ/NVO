# Custom armour and power armour

Step4D supplies extensible identification and authored coverage. Actual protection and stagger are later work.

## Adding a set later

1. Import the resource as actual ARMO records in GECK. A mesh or texture alone has no record identity. Keep body suits and helmets separate where the design calls for independent protection. Retain donor credits and notices with the source package.
2. Record the owning plugin and local FormID. For a record originally defined in NVO.esm, use NVO.esm plus its new local ID. A copied/merged donor record needs a new mapping. An override of an existing record retains the original owning key, but its changed geometry/material must still be reviewed.
3. Capture one diagnostic hit on a wearer. ARMOUR_ORIGIN reports plugin and six-digit local ID; ARMOUR_ITEM reports the observed equip mask. The displayed runtime FormID's load-order byte must not be saved into the local ID. Unknown records are expected to hold at this point.
4. Add a profile to profiles/armour-coverage.json. Use its exact JSON schema: descriptive id, plugin, eight-digit zero-prefixed local_id, positive revision, eight-digit expected_equip_mask, all six coverage fields and rationale. Only none/partial/full/unknown are valid. Use unknown when evidence is absent. A power-armour flag or large silhouette does not justify full coverage.
5. Compile the authored JSON to a workspace output, review it, then install that one TSV when the corresponding packet is approved. No DLL rebuild is needed. Restart the game for the diagnostic check. Confirm separate helmet/suit rows, removal and condition changes, unknown-item holds and load-order-independent identity.

From the release root, with Python available:

```powershell
python Tools/compile_armour_coverage.py profiles/armour-coverage.json prepared/NVOArmourCoverage.tsv
```

The runtime destination is Data/NVSE/Plugins/NVOArmourCoverage.tsv. Despite the filename, fields are separated by the pipe character `|`, not tabs. The shipped source JSON has explanatory rationale; the compact runtime file contains only classification data. Do not overwrite a working runtime file with an unreviewed example. The accompanying .example is deliberately invalid until real IDs and masks are supplied.

A changed equip mask produces record_mismatch. An unchanged mask is only a narrow check: it does not prove the mesh, material or winning override is unchanged. There is no automatic profile inheritance, fuzzy display-name matching, durability-to-strength conversion or universal power-armour protection.

## How damage and stagger will connect

The planned flow is:

```text
Verified hit + equipment identity + target anatomy
    -> region/surface coverage and ordered material response
    -> one resolved hit: penetration, residual energy, transmitted impact,
       biological/mechanical injury input and armour wear
    -> damage/injury consumer + separate stagger consumer
```

Each consumer must use the same hit/component identity. Direct damage enters the engine once. Shotgun pellets and projectile-impact/explosion components remain distinct. Reaction cooldowns and burst limits prevent repeated hits from trapping an actor in knockdown animations.

Stagger will not simply equal lost HP. A stopped projectile may transmit enough impact to disturb balance; a penetrating wound need not create dramatic knockback. Proposed response inputs include mechanical impact, stance, target stability, current injuries and explicitly authored powered-suit support. These are design inputs, not implemented or calibrated coefficients. A suit's appearance cannot reveal whether its servos are powered.

Material response will distinguish bullets, melee, laser heating, plasma, sustained flame and blast rather than assigning them all a bullet-like impulse. No universal energy-weapon immunity is implied by power armour. Robots need mechanical target profiles; animals need their own anatomy and natural protection. Baked BIP/model armour is not a worn inventory instance and requires explicit target-profile evidence.

Presentation modules may supply animations and sound. NVO's shared result must own protection, damage and hit-triggered stagger, with other mods' overlapping effects accounted for before those paths activate. Detailed physiology and treatment remain scheduled for Step5.

## Scale and limits

This version supports up to256 explicitly mapped records, including custom sets, in one file. It copies names and validates once per session, then performs bounded matching against the prepared table. Exceeding a cap disables classification instead of silently dropping records. Runtime timing and many-actor readiness are not proven by offline repeated-call tests or the previous bounded 4B stress checkpoint.

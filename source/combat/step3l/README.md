# Packet 3L — damage scaling audit

Prepared 2026-09-16. Purpose: explain the existing twofold health loss before adding NVO damage rules. This is an evidence packet, with no DLL, GECK script, plugin or configuration installation.

## Result

The loaded game is on difficulty index **0 (Very Easy)**. Both `iDifficulty:GamePlay` and the cached `PlayerCharacter.gameDifficulty` used by the damage helper were 0 at the main menu. The loaded health multiplier is **2.0 against a non-player receiver**, and **0.5 against the player**. The corresponding Normal settings are both 1.0.

The engine code applies this multiplier before the health request observed by native319/320. That gives the exact arithmetic seen in the completed 3K checkpoint:

| Attack | Earlier hit health | Current non-player multiplier | Health request | Observed HP |
|---|---:|---:|---:|---:|
| Hunting rifle | 29.5 | 2.0 | -59 | 65 → 6 |
| Punch, after reload | 0.450000018 | 2.0 | -0.900000036 | 65 → 64.0999985 |

**Evidence limit:** the multiplier and cached difficulty were captured in a later main-menu session, not at the instant of those earlier hits. We have verified the current mechanism and a matching explanation for the observed factor of two; we have not retroactively measured the old setting values. No additional gameplay test is needed for this audit. Any future damage-authority test must record its settings at hit time.

## What stays installed

- Native320, including the once-per-process `NVO [0.3.20]` console banner.
- The RD-free NVO.esm and its five user health Game Settings.
- Existing flight profiles and the pilot ESP.
- Your current difficulty selection and damage multipliers.

No compilation, installation or GECK work is required. Damage replacement remains disabled. Reversal: none; this packet changes only workspace documentation and read-only inspection tools. Do not copy the evidence `.bin`/`.obj` files into the game.

## What the settings mean here

| Difficulty index | Setting suffix | Health multiplier, non-player receiver | Health multiplier, player receiver |
|---:|---|---:|---:|
| 0 | VE | 2.0 | 0.5 |
| 1 | E | 1.5 | 0.75 |
| 2 | N | 1.0 | 1.0 |
| 3 | H | 0.75 | 1.5 |
| 4 | VH | 0.5 | 2.0 |

These are actual loaded values, not assumed defaults. The traced helper selects on the **receiver's** `IsPlayerRef()` result; it does not inspect the attacker argument. The `ByPC` names therefore must not be treated as proof that this helper only scales player-origin attacks. NPC-to-NPC execution still needs its own live checkpoint before authority is enabled.

Maximum-health settings are a separate layer. All five NVO health overrides matched their loaded values: `fPCBaseHealthMult=1`, `fAVDHealthLevelMult≈0.1`, `fAVDNPCHealthLevelMult=0`, `fAVDHealthEnduranceMult=5`, `fAVDHealthEnduranceOffset=-1`. This packet does not rebalance them or attribute the old 596 HP issue to difficulty.

`fDamageWeaponMult=1` and `fDifficultyDamageMultiplier=10` were also captured. Neither is read by the specific health-scaling helper traced here. Their names/values alone are not a reason to change them; their other consumers were not exhaustively traced. Limb damage, DT/DR, criticals, perks and VATS modifiers remain separate concerns.

## Your difficulty idea

We can neutralize the ten `fDiffMultHPByPC*` / `fDiffMultHPToPC*` settings to 1.0, while keeping the difficulty selection as input to NVO presets. That is a proposed later implementation, **not applied in this packet**. Merely neutralizing these settings would remove their health-damage scaling; it would not by itself implement the replacement presets or prove every other difficulty-dependent behaviour neutral.

Recommended direction: consistent penetration and anatomical vulnerability, with configurable ammunition/medicine availability, believable enemy accuracy/reaction time, and recovery/treatment forgiveness. Keep medicine recognizable and powerful, respecting the earlier decision to avoid an elaborate treatment minigame. Permadeath remains a design assumption, never save deletion or loading restrictions. Distribution and AI changes belong to their own later systems and must not be smuggled into the ballistic damage calculation.

## Next proposed packet

**3M: define the disabled armour model's inputs and damage handoff.** Specify units and ammunition mass/provenance, trustworthy impact/contact data, unsupported-hit fallback, and exactly which existing modifiers NVO owns or preserves. Include the proposed difficulty policy and the separate Brahmin Baron damage path. Use existing Ultra317 findings and current evidence; do not repeat the full review or the old VATS stress tests.

This does not enable damage. Ask before preparing 3M. The overall pre-damage gate remains HOLD until the input/ownership contracts, supported paths and targeted review pass.

## Evidence

- `runtime-20260916-124233/manifest.json`: canonical final capture; named settings, cached difficulty and stable code/table hashes. Earlier captures retain the bounded discovery trail.
- `ENGINE-TRACE.md`: exact call chain, table mapping and interpretation limits.
- `inventory/GMST-OVERRIDES.json`: relevant record chains across all 12 active plugins. Settings without a record are explicitly shown as such; this does not rule out runtime script/plugin changes.
- `RESULT.json`: machine-readable multiplier mapping and verification result.
- `main-menu-inspection/SESSION.json`: log archived, assistant's exact main-menu process closed; no save/gameplay loaded.
- `../step3k/captures/reload-1930643b54d3/REVIEW.md`: completed rifle/reload/punch evidence, retained unchanged.

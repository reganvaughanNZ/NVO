# Loaded engine trace — Packet 3L

Read-only main-menu capture of FNV PE32 at base00400000, timestamp4E0D50ED, image size0107B000. The helper requested QUERY_LIMITED_INFORMATION|VM_READ; no injected calls, process writes or suspension. The assistant separately launched NVSE and closed its own main-menu instance. The manifest's `game_launched=false` describes the read helper, not that surrounding session.

## Health request route

1. `0089D6F0` retains the target as `this`, incoming health magnitude at stack+8 and source at stack+10h. After its early check, `0089D722–0089D72E` negates the incoming magnitude and calls `008808A0` with target/source.
2. `008808A0` reads receiver virtual slot0360 (`IsPlayerRef`, corroborated in JIP `nvse/GameObjects.h:508`). It calls `005BE4D0` on the global player at011DEA3C, then passes cached difficulty, AV16 (Health) and receiver-is-player into `00648CB0`.
3. `005BE4D0` returns the int at player+07B8. JIP `GameObjects.h:1023` names it `gameDifficulty`. The capture reads exactly this field after validating the player primary vtable0108AA3C and form00000014; it equals0. This is distinct from assuming the INI value is necessarily the runtime value.
4. For AV16, `00648CB0` selects a Setting pointer from0119B310 if receiver-is-player, otherwise0119B324, indexed by difficulty. `00403E20` returns Setting+4, whose float it reads. The ten captured pointers resolve exactly to the independently name-validated GMST objects below.
5. `008808DC–008808E2` multiplies the signed input by that float and returns it. The supplied source argument is not read in this helper. This is a receiver-based selection, including non-player receivers regardless of the source if execution reaches it.
6. `0089D733–0089D735` negates/stores the scaled magnitude. Its positive branch has additional bookkeeping calls. `0089D80E–0089D82B` then sends source, negative scaled magnitude and AV16 to target virtual slot03AC (`DamageActorValue`). The return address **0089D82D** matches the completed 3K rifle/punch health records.

The observed native319/320 interval surrounds the existing ITR provider at this final slot. Its recorded requested delta is already difficulty-scaled on this route. Multiplying it again in NVO would be double application. Net getter change measures the whole provider interval, not an exhaustive count of internal writes. Nothing in this audit authorizes patching these raw addresses or bypassing ITR.

## Exact tables

| Index | Player table at0119B310 | Non-player table at0119B324 |
|---:|---|---|
| 0 | 011D0388 fDiffMultHPToPCVE = 0.5 | 011D0C6C fDiffMultHPByPCVE = 2 |
| 1 | 011D0838 fDiffMultHPToPCE = 0.75 | 011D0D8C fDiffMultHPByPCE = 1.5 |
| 2 | 011D12A8 fDiffMultHPToPCN = 1 | 011D0784 fDiffMultHPByPCN = 1 |
| 3 | 011D052C fDiffMultHPToPCH = 1.5 | 011D0E58 fDiffMultHPByPCH = 0.75 |
| 4 | 011CFEB8 fDiffMultHPToPCVH = 2 | 011D01A4 fDiffMultHPByPCVH = 0.5 |

Setting names and addresses were cross-checked against JIP `internal/settings_enum.h` and then validated in the loaded process. The four-byte float at offset4 is retained in base64 object bytes. The observed selector also has an AV24 branch, which is outside this health claim. Its input index is not visibly range-clamped here; future NVO readers must validate index0–4 and finite values rather than reproduce unchecked array access.

## Scope and remaining work

- Current code/tables and named settings are directly observed; the historical cause of the 3K factor2 is a strongly supported inference because those old logs did not record hit-time difficulty.
- The captured tail and scaling helpers show no NVO jump detour in the relevant instructions. This is not an exhaustive compatibility audit of every engine/provider call.
- This trace is not proof of incoming-player, every creature, explosion, limb, death, VATS or arbitrary modded paths. Preserve those checkpoints before enabling authority.
- Record ordering confirms five NVO health GMSTs win and match current memory. The ten difficulty GMSTs have no records in this active set. Main-menu values cannot exclude later runtime changes.
- No change to health formula, saves, user difficulty, donor scripts, flight, or the native320 DLL. No new hook, no new damage code, no gameplay retest.

## Contract for later implementation

Separate physical inputs, engine-derived hit values, requested deltas and observed net loss. Do not interpret an already-scaled engine number as raw cartridge energy. Give every modifier one explicit owner. Do not compensate with a blind divide-by-two: difficulty/settings may change, the receiver determines the branch, and this route is not every damage path.

For the proposed NVO difficulty presets, neutralize only the agreed health-damage settings under an explicit later configuration policy. Retain the selected difficulty for independent preset inputs; do not change user INI settings silently. Record effective settings at the relevant session/hit boundary, detect changes, and specify conflict/fallback behaviour. VATS must ultimately use the same armour/injury rules with its separate player-protection modifier addressed explicitly. Do not assume neutralizing these ten settings resolves VATS protection, critical bypass or other modifiers.

Before armour implementation, settle the outstanding Ultra317 physical input/admission contracts and the Brahmin Baron extra DamageAV/Kill owner. Before activation, verify the supported boundary, exact-once application/attribution and diagnostic-independent behaviour. Unknown/unsupported hits must retain existing behaviour, not receive fabricated energy or partially replaced damage.

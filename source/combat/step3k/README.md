# Packet 3K — observe actual HP and limb changes

Native319 adds a bounded observer around the installed ITR damage chain. It records the requested delta, current actor value and damage component before and after that call. The observations join an existing hit transaction only when its receiver and source match. Nested calls are marked: their enclosing net change must not be counted again as another independent hit.

Damage replacement is disabled. No armour, medicine, projectile tuning, game settings or NVO.esm records change. The healthy `bat NVOFlightKit` console reminder is removed; manual kit commands still work. No GECK work is required.

When available, follow START-HERE.html for three successful close-range hits with one reload. Gameplay validation remains yours. The assistant's main-menu-only inspection does not validate live getter values, hit counts or applied damage.

The log is `C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas\NVOCombatCore.log`. New rows start `AV_APPLY`. A valid net observation is not proof of a single storage write, nor proof that all engine damage paths were intercepted.

Unsupported callable entries or changed providers disable this observer and leave the original chain in place. Positive/zero deltas, other actor values and calls on other threads pass through unsampled. Creature condition remapping is recorded as `effective_av`. Runtime evidence confirms the interface; the offline probe substitutes engine reads and validates the call wrapper, lifecycle and bookkeeping separately.

Reversal: close New Vegas and restore only NVOCombatCore.dll and its matching PDB from the backup identified in INSTALL-3K-result.json. Keep the RD-free NVO.esm and existing pilot/configuration. Do not restore an older ESM or RD.esm.

After this diagnostic checkpoint, resolve the supported ballistic units/mass/contact rules, prepare the disabled armour calculation, then review the affected code before separately authorizing damage activation. The existing Ultra317 review remains the baseline; this packet does not close the overall pre-damage gate.

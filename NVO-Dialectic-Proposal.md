# Dialectic integration proposal

Recorded 14 September 2026 following the user's suggestion. This is a feasibility review and proposed direction, not an implemented integration or a replacement for the approved combat plan.

## Recommendation

Use Dialectic as an optional conversation and NPC roleplay framework alongside NVO. It is a promising fit for personal contacts, companions and reactions to background consequences. NVO should continue to own mechanical outcomes: combat, injuries, medicine, inventory rewards, quest progression and permanent background restrictions.

NVO's core gameplay should remain functional when Dialectic or its server is unavailable. AI conversation must not become a prerequisite for completing an authored job. Generated promises of payment, healing, membership or forgiveness must not themselves grant those outcomes.

## Evidence inspected

Local archive: `C:\Users\regan\Desktop\NVO Mod References (Open Source)\DIALECTIC 99233 1.0.0 2026-08-29T00-18Z ZORC7yeV.zip`.

- Contains `Dialectic.esp`, compiled `NVSE/Plugins/dialectic.dll`, configuration, MCM/UI files, a built-in voices CSV and 52 script files. No C/C++ or PHP source files were found. This is a runtime distribution with readable adapters, not the full native/server source tree.
- `README.txt` requires a matching DialecticServer. `dialectic.ini` defaults to host `127.0.0.1`, port `8085`, path `DialecticServer/main.php`.
- `WorldContextTick.txt` exports location, weather and time. `CollectActorSnapshot.txt` reads actor health and equipment. `RpgEventTick.txt` produces combat, level and sleep/wait events. These provide relevant context machinery, but do not establish an API for NVO's future custom wound or background state.
- The bootstrap assigns native ownership of actions, presentation and trade state to `dialectic.dll`. Any NVO action integration needs an explicit ownership review.
- `RpgEventTick.txt` falls back to the name "The Courier" when the player name is unavailable. Alternative Start integration must check broader player profiles and narration as well: the player has not necessarily accepted the Courier job.

The [author's description](https://www.nexusmods.com/newvegas/mods/99233?tab=description) advertises contextual conversations, memory, relationships, configurable actions and local or hosted models. The [files page](https://www.nexusmods.com/newvegas/mods/99233?tab=files) supplies a separate DwemerDistro server installer and optional CSV samples for custom NPCs and locations. Neither was present in the inspected reference-folder listing. Advertised capabilities have not been tested with NVO.

## Proposed uses

| NVO feature | Proposed Dialectic role | NVO responsibility |
|---|---|---|
| Prospector | Salvage buyer discusses completed work and local opportunities. | Actual salvage, job availability, prices and payment. |
| Brotherhood Exile | A former colleague offers personal sympathy or covert advice. | Exile persists; friendship cannot restore membership or normal services. |
| NCRCF Convict | Contacts respond to wanted status and known actions. | Outlaw restrictions and access checks remain enforced. |
| Companions | Reactions to witnessed danger, losses and shared history. | Recruitment eligibility, survival, quest state and inventory. |
| Injuries and medicine | Dialogue reacts to supported NVO condition summaries. | Damage, treatment costs and healing results. |

These are proposed additions. Future NVO state must be exposed through a verified extension interface; existing actor snapshots alone do not supply it. NPC knowledge should distinguish witnessed/public facts from private background information.

## First proposed prototype

Use the planned Prospector buyer as one bounded conversation prototype after the underlying contact and salvage job exist. Supply an original NVO biography and job context through supported profile/data mechanisms. Begin with conversation only and disable gameplay actions for the prototype through verified controls. Confirm that ordinary quest dialogue and payment still work without the server.

Before preparing that packet, inspect the official CSV samples and matching server documentation, verify how NVO state can be supplied, and establish save/character memory separation. User gameplay checks should cover truthful job status, no assumed Courier history, normal dialogue coexistence, server failure and reloading without memories leaking between characters. Broader NPC coverage and gameplay actions follow only after the small prototype works.

## Dependencies and reuse

The local README lists xNVSE, JIP LN, JohnnyGuitar, ITR NVSE, MCM, MCM Extender, ShowOff, UIO, the x86 Visual C++ runtime and a matching server. The Nexus description additionally lists SUP NVSE and recommends Floating Subtitles. Reconcile those requirements before an installation packet. Provider configuration and any usage costs remain unassessed.

The archive's `LICENSE.txt` identifies MIT licensing and its README explicitly refers to it. The Nexus description instead shows restrictions on modification and asset reuse. Preserve both pieces of evidence; do not assume the reference folder's name resolves that discrepancy. Keeping Dialectic separately installed avoids bundling its files in the proposed NVO integration. Establish the applicable terms before any donor copying or redistribution.

No installed files, ESM records or runtime code were changed. No compilation, server execution or gameplay testing was performed for this review.

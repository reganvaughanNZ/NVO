# 3U1 classification contract

`ClassifyImpactTarget(rawPointer, formId)` is intentionally narrow:

| Raw pointer | Read/form result | ID | Kind | Eligible as world | Eligible for actor join |
|---|---|---:|---|---|---|
| unread | unavailable | any | Invalid | no | no |
| null | complete contact geometry | 0 | World | only with region -1 | no |
| null | inconsistent | nonzero | Invalid | no | no |
| nonnull | unreadable form | unknown | Invalid/unavailable | no | no |
| nonnull | readable form | 0 | Invalid | no | no |
| nonnull | readable form | nonzero | Reference | no | with all existing identity checks |

This distinction is recorded when the contact is read. It is then copied into the bounded collision cache and pre-clamp terrain sample. Terrain reconciliation requires the same kind, ID, region, flags and point. Collision/callback correlation also requires the same kind. The hit observer requires Reference on both collision and live contact, plus nonzero query target and its existing identity checks.

The contact list head itself must exist and point/material/region reads must succeed before either World or Reference is valid. A second contact retains the existing multiple-contact rejection. This packet does not change `nvo::hit::ReadForm`; other modules continue to use its existing null-as-absent behavior.

Old logs contain the numeric target ID only and therefore cannot distinguish null from nonnull zero-ID forms. Replays must label those historical rows ambiguous. Prospective fixtures may select World to test the algorithm, but they cannot certify installed native behavior. Native acceptance requires a fresh target_kind row.

World classification affects only diagnostic segment-speed availability. It does not create an actor, damage target, region authority, exact collision time or damage permission. `ContactSpeed::damageAuthority` remains compile-time false; there is no public application API. Damage remains OFF and Ultra317 remains HOLD.

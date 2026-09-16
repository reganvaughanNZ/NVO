# Ultra audit: Packet 3U1

The requested Ultra review found no production blocker for packaging this diagnostic build with damage disabled.

- A contact is `World` only when the contact target pointer was read successfully and is null. A non-null pointer with form ID zero is `Invalid`.
- World evidence also requires target ID zero and body region `-1`.
- Actor hit pairing still requires a `Reference` contact and a non-zero matching actor ID, alongside the existing lifetime, projectile, source, weapon and ammunition checks.
- Terrain proof and callback correlation carry the contact kind, so equal numeric IDs cannot erase the world/reference distinction.
- `CurrentHit.cpp`, `NativeObserver.cpp`, and the flight point model remain unchanged from 3U. No hook, allocation, movement write, or unbounded container was added.
- The actual production `ReadImpact` body and production classifier are exercised by the reader harness. A direct world-ID-zero/query-ID-zero join regression is also covered.

The 3U recording did not log the raw target pointer, so its old zero-ID rows remain ambiguous. Prospective offline replay is useful evidence, but the fresh 3U1 runtime checkpoint is required. This audit does not close the broader Ultra317 hold or authorize damage replacement.

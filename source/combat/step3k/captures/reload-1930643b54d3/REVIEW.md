# Packet 3K reload checkpoint — passed for the exercised path

Native319 log SHA1930643b54d36b0a2fe63e86cdb5ff0d18176cf3d926cf7c795ffa935eb35ba5,37147bytes, archived after two matching reads.

Session1 loaded successfully. Hunting Rifle00004333 / standard.3080006B53C hit player->target00104C80, reportedtorso0. Health65->6 (requested-59, net-59); torso condition100->24.3589706 (requested/net-75.6410294). Both calls returned valid, exactly scope-matched to hit1.

Save reloaded successfully into session2. Unarmed weapon000001F4, no projectile, same target starts restored at65HP and100condition. Health65->64.0999985 (requested-0.900000036, net-0.900001526); condition100->98.8461533 (requested-1.15384626, net-1.15384674). Both calls returned valid, scope-matched to hit2. Differences are float rounding. No stale scope association, open calls, invalid reads, depth overflow or log failures; no new hook-disable errors. Normal exit.

Together with the earlier96 detailed pistol observations, this completes the requested live net-value and reload checkpoint for player-to-NPC hits. Does not validate all actor classes, incoming-player damage, every attack path or internal single-write authority. The earlier factor2 remains: hit inputs29.5/0.450000018 become59/0.900000036 appliedHP loss. Its source still needs tracing before new damage ownership. Damage replacement remains off and overall Ultra317 gate remains HOLD.

Next proposed combat packet3L: trace the existing scaling to identify what must be replaced/preserved, using captured code/settings first and diagnostics only if necessary; then proceed toward the disabled armour calculation. User approval required before that new packet. The requested once-per-launch console banner is a separate small3K1 update.

"""Record reviewed 309 checkpoint without changing runtime files."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
note='''## Current combat checkpoint: 3C4 diagnostic accepted; local-vector correction proposed

2026-09-15: user finished the instructed 309 test. Archive source/combat/step3c4/captures/2026-09-15-3C4-7e3ad3449a2c/NVOCombatCore.log (SHA256 7e3ad3449a2c959bda7231b06540e132f97bd8a6cb009e094b849248f5f722a5; 37,963 bytes, 194 lines; last-write 15:22:38 local). Review source/combat/step3c4/REVIEW-1.md, review-data.json and controller-00C73170.txt. One load, two private scenery hits/destructions, normal exit; 17 timing samples, no reported identity/read/overlap/nesting/invalid/overflow/unpaired faults or cap. Two baseline matches, two first applied mismatches, zero accepted physics steps; no repeat of unchanged 309.

All four paired controller observations dispatch virtual C8 of vtable01090594 (JIP ProjectileListener) to C73170. Request exactly matches submitted input and remains unchanged on return. Rifle/pistol modified localZ -.326924920/-.326088876. Candidate equals actual; omission residual .00119/.00569 units. Hash-verified complete 2048-byte prefix FNV0193951146A4412C/SHA20a927ae6742fc61e6cdf8f0a52c945051a7a33cf743c1aa7c7a151627e0beac identifies a concrete candidate: request XYZ copied to local ESP+50/+54/+58 at C734EA..FC; C73517 FLDZ and C73519 FSTP[ESP+58] conditionally zero only the working Z, before velocity preparation C7351D..57 and subsequent conditional pitch rotation. Guards: helper9306B0 result (compares5C0880 result with5) and controller+414 bit11. Exact reset-branch execution is not yet independently observed; captured prefix is not whole function. Do not globally change flags/mode or bypass collision. Proposed next packet confirms/preserves the private pending projectile working vector under exact identity/code/frame guards and retains displacement verification. Ask before build/install.

Review-only turn: no native source/build/install/gameplay/GECK/process-memory capture. Game closed when checked; 309 stays installed. Xhigh appropriate; Max unnecessary. Legacy review reference/legacy-nvo-review/REVIEW.md is separate and does not alter the combat plan.

'''
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    data=p.read_bytes()
    if note.splitlines()[0].encode() in data: continue
    data=data.replace(b'## Current combat checkpoint: 3C4 / 309 installed; controller request test pending',b'## Previous combat checkpoint: 3C4 / 309 installed; subsequently reviewed',1)
    first,sep,rest=data.partition(b'\n')
    p.write_bytes(first+sep+b'\n'+note.encode('utf-8')+rest)
print('Recorded accepted 3C4 diagnostic; next correction requires user approval.')

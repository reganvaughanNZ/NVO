"""Prepend the accepted 3U1 checkpoint without decoding legacy status bytes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BODY = """
## Current checkpoint: Packet 3U1 world/reference classification ACCEPTED

Pinned close-landscape log SHA01a7dd5ef0cdaba00a97b950b1e02dd366c4d45ef3f9002a546bc2952a5454ea. Single standard9mm collision read a null target as target00000000, target_kind1 World, region-1, validmask31. Callback retained kind1 and correlated. The contact also exercised strict terrain evidence with explained_clamp1; observed engine-segment speed remained available. One create/impact/destroy, zero read failures/unmatched events/movement mismatches/unpaired accounting/admission failures/open lifetimes/held slots. Damage replacement0.

Combined with prior live3U1 capture SHA7337bf485a5cb219ec4cd4e2bfc37121a0936e3c5bd5091dba801b3ca3de65a2, nonzero environment/wall references and region0 actor stayed target_kind2. Actor join required matching nonzero Reference identity and retained its bounded owned-step speed range. Therefore the 3U1 purpose is accepted: fix null-world coverage without weakening actor identity checks.

This closes Packet3U1 only. Ultra317 damage-authority hold remains; exact contact time/point authority, pre-movement policy and broader damage ownership/scaling gates remain unresolved. No more3U1 firing is needed. NEXT ask before a Step3 closure/Ultra gate audit using existing source and captures; do not activate damage or begin armour silently.

""".encode("utf-8")

for relative, header in [
    ("STATUS.md", b"# NVO project status\r\n"),
    ("source/combat/README.md", b"# NVO combat implementation\r\n"),
]:
    path = ROOT / relative
    data = path.read_bytes()
    if BODY.splitlines()[1] in data:
        continue
    if not data.startswith(header):
        header = header.replace(b"\r\n", b"\n")
    if not data.startswith(header):
        raise RuntimeError(f"unexpected header: {relative}")
    path.write_bytes(header + b"\r\n" + BODY.replace(b"\n", b"\r\n") + data[len(header):])

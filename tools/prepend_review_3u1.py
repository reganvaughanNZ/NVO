"""Prepend the live 3U1 review without decoding legacy status bytes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BODY = """
## Current checkpoint: Packet 3U1 live test PARTIAL PASS; one close-ground recheck needed

Pinned native325 log SHA7337bf485a5cb219ec4cd4e2bfc37121a0936e3c5bd5091dba801b3ca3de65a2. One startup banner; two sessions/one reload; five standard9mm admissions. User followed the requested run, but the first two distant ground shots recorded no collision and retired after3.082s/3.072s. Three actual contacts were all readable nonzero references (`target_kind=2`): an environment reference, a region0 actor, and the post-reload wall/reference. No `target_kind=1` null-world contact occurred, so the central classifier is not yet accepted live.

Reference/actor preservation passes: the actor collision paired only with Reference kind and the same nonzero target; its owned-step speed range remained available. All3 callbacks correlated. Across both sessions:371 applied steps, zero movement mismatches, zero unpaired accounting, zero admission failures/process faults, zero open lifetimes/held pool slots. No terrain clamp occurred. Damage replacement remained0. This is stable but only a partial functional pass.

NEXT within the same packet: one close standard9mm shot directly into bare landscape dirt/rock ground, wait a few seconds, quit normally. No actor, reload, VATS, stress test or video. Read the fresh log for a collision with target_kind1; a referenced ground object may still report kind2 and does not test the null branch. Do not advance or alter code until this minimal recheck is reviewed.

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

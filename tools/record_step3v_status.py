"""Prepend the Packet 3V closeout without transcoding legacy status files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = b"## Current checkpoint: Packet 3V Step 3 closure audit EXECUTED"
BLOCK = (
    b"\r\n\r\n"
    + MARKER
    + b"\r\n\r\n"
    + b"The prepared Ultra-assisted audit was revalidated and formally recorded. All 71 files in the native325/3U1 source snapshot match their pinned SHA-256 values, both raw 3U1 captures match their recorded hashes, the installed pair remains verified, and damage replacement remains OFF with zero damage hooks.\r\n\r\n"
    + b"Step 3 is closed only as a bounded ballistic-flight and diagnostic foundation for the nine exact `select_on_fire` bullet profiles. This does not claim all vanilla ammunition, authoritative contact energy, armour, injury, VATS/critical policy, or laser/plasma/flame/explosive/thrown/melee/pellet support. Unsupported cases retain the complete engine or mod path.\r\n\r\n"
    + b"Ultra317 damage-authority HOLD remains. A future Step 4 packet may begin a guarded read-only armour shadow adapter using the existing pure `NVOCombatModel`; Packet 3V implemented no adapter, DLL, game, GECK, configuration, or `NVO.esm` change and requires no gameplay test. Evidence and decision: `source/combat/step3v`; release: `release/NVO-Combat-Packet-3V-Step3-Closure-Audit`.\r\n\r\n"
    + b"Any older text below saying that the Ultra review or Step 3 closure audit has not yet occurred is historical.\r\n\r\n"
    + b"NEXT: ask before preparing the first Step 4 read-only shadow-adapter packet. Do not activate damage or broaden projectile ownership silently.\r\n"
)

TARGETS = {
    ROOT / "STATUS.md": b"# NVO project status",
    ROOT / "source/combat/README.md": b"# NVO combat implementation",
    ROOT / "source/combat/PRE-DAMAGE-REVIEW.md": b"# Ultra review before damage: agreed checkpoint",
    ROOT / "source/combat/review/REVIEW-STATUS.md": b"# Pre-damage review status",
}

for path, title in TARGETS.items():
    data = path.read_bytes()
    if MARKER in data:
        continue
    if not data.startswith(title):
        raise RuntimeError(f"Unexpected title in {path}")
    end = data.find(b"\n")
    if end < 0:
        raise RuntimeError(f"Missing title newline in {path}")
    path.write_bytes(data[: end + 1].rstrip(b"\r\n") + BLOCK + data[end + 1 :].lstrip(b"\r\n"))

print("Packet 3V status recorded in four superseding project status documents")

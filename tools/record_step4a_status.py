"""Prepend the Packet 4A checkpoint without transcoding legacy status files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = b"## Current checkpoint: Packet 4A offline armour shadow adapter PREPARED"
BLOCK = (
    b"\r\n\r\n"
    + MARKER
    + b"\r\n\r\n"
    + b"Step4A adds a pure typed evidence adapter to `native/NVOCombatModel`; it is not linked into `NVOCombatCore`. A preview now requires exact hit/component/application and carrier/weapon/ammunition/profile identity, verified path and real-time/VATS mode, agreement between collision and hit-data regions, modifier ownership, a coherent complete equipped-armour snapshot in outermost-to-innermost order, exact calibrated contact speed, and verified kinetic/target profiles. Unknown armour cannot become bare skin, region disagreement cannot become torso, and interval speed cannot become a midpoint.\r\n\r\n"
    + b"Standalone x86 `/W4 /WX` checks pass:48 adapter checks and45 existing armour-model checks, with zero failures;10,000 repeated shadow previews are deterministic. All profiles and coefficients remain synthetic. Native325's71-file snapshot is unchanged. No DLL, hook, engine reader, log path, production armour table, game/GECK/configuration/`NVO.esm` change, installation or gameplay test exists in this packet. Damage authority remains HOLD.\r\n\r\n"
    + b"Packet: `source/combat/step4a`; release: `release/NVO-Combat-Packet-4A-Offline-Shadow-Adapter`. NEXT: ask before Step4B, a guarded read-only engine-side equipped-armour snapshot reader. Step4B must still perform no health, limb, condition, inventory or effect writes.\r\n"
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

print("Packet 4A status recorded in four superseding project status documents")

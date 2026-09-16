"""Prepend the installed 3U1 checkpoint without decoding legacy status bytes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BODY = """
## Current checkpoint: Packet 3U1 native325 INSTALLED; live world-contact checkpoint pending

User approved fixing world-contact classification while preserving actor identity checks and requested an Ultra audit. Native325 / NVO0.3.25 now classifies a contact as World only after successfully reading a null raw target pointer; a nonnull pointer with form ID zero is Invalid. Actor hit pairing still requires Reference kind, a nonzero matching actor ID, and the existing lifetime/projectile/source/weapon/ammunition/point checks. Terrain proof and callback correlation also carry target kind. CurrentHit, the point model, flight equations, movement writes, hooks, caps and tolerances are unchanged. Damage replacement remains OFF; Ultra317 remains HOLD.

Ultra found no production blocker. Its requested direct world-ID-zero/query-ID-zero join regression was added. The harness compiles the actual ReadImpact body and extracts the production classifier. Reader11 checks, completed-capture24 checks, broader39484 checks and384/38784 numerical cases/samples pass under /W4 /WX. The old3U log lacks raw pointer presence, so its zero-ID contacts remain deliberately ambiguous; prospective replay is not live acceptance. Full x86 build has zero warnings/errors, matched DLL/PDB, exactly2 exports,9 unchanged bridge bodies and31 unrelated inputs unchanged.

Installed ONLY native325 DLL/PDB;53 protected files verified, no game process closed/launched. DLL963a6f51f8f3539c66f2503d2615eb6aff2849e7d1eb4911e7467059a5c76fce; PDBd39a19ccd39c5d06e36285dbe83168fb8d0982763ae801755424142abdcf96e4. Backup backups/combat-install-3U1-20260916-203125-d52477f6 contains native324. RD.esm remains absent. Source/evidence source/combat/step3u1; release/NVO-Combat-Packet-3U1-World-Contacts.

USER CHECK: two standard9mm shots into distant sloping ground; one close standard9mm living-target hit; reload once; one standard9mm shot into nearby wall; wait and quit normally. No VATS/stress/video/forced clamp. Expect world target_kind1 and actor/reference target_kind2, strict actor pairing, one startup banner and damage_replacement0. A run without a terrain clamp validates classification but not the clamp branch. Read game-root log after user says finished; then ask before another packet.

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

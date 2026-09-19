"""Fresh offline response checks and review packet. No game paths or installation."""
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "native/NVOCombatModel"
STEP = ROOT / "source/combat/step4f"
RELEASE = ROOT / "release/NVO-Combat-Packet-4F-Response-Definitions"
SOURCES = ["ResponseDefinitions.hpp", "ResponseDefinitions.cpp",
           "response_definition_tests.cpp", "run_response_checks.cmd"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path, root):
    return {"path": path.relative_to(root).as_posix(), "sha256": sha(path),
            "bytes": path.stat().st_size}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main():
    # Local historical source manifest, not a live game dependency.
    baseline = json.loads((ROOT / "source/combat/step4d/Evidence/SOURCE-SNAPSHOT.json").read_text())
    unchanged = []
    for item in baseline["files"]:
        path = ROOT / "native" / item["path"]
        if path == MODEL / "README.md":
            continue  # This packet adds a navigation section, not a model change.
        if sha(path) != item["sha256"]:
            raise RuntimeError(f"Existing native source changed: {item['path']}")
        unchanged.append(record(path, ROOT))
    builds = [ROOT / "native/NVOCombatCore" / name for name in ("BUILD.cmd", "CMakeLists.txt")]
    for path in builds:
        if "ResponseDefinitions" in path.read_text():
            raise RuntimeError("Offline response module unexpectedly linked into DLL build")
    source_before = [record(MODEL / name, ROOT) for name in SOURCES]
    check = subprocess.run(["cmd.exe", "/d", "/c", "run_response_checks.cmd"],
                           cwd=MODEL, capture_output=True, text=True)
    if check.returncode:
        raise RuntimeError(check.stdout + check.stderr + "\nSee native/NVOCombatModel/out-response/build.log")
    match = re.search(r"PASS (\d+) checks; (\d+) deterministic selections", check.stdout)
    if not match:
        raise RuntimeError("Missing fresh check result")
    if source_before != [record(MODEL / name, ROOT) for name in SOURCES]:
        raise RuntimeError("Sources changed during build")
    build_log = (MODEL / "out-response/build.log").read_text()
    if re.search(r"\b(?:warning|error) [A-Z]+\d+", build_log, re.I):
        raise RuntimeError("Compiler reported a warning/error")
    copy(MODEL / "out-response/results.txt", STEP / "Evidence/CHECKS.txt")
    copy(MODEL / "out-response/build.log", STEP / "Evidence/BUILD.txt")
    copy(MODEL / "out-response/toolchain.log", STEP / "Evidence/TOOLCHAIN.txt")
    verification = {
        "packet": "4F", "status": "PREPARED_OFFLINE",
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_version_unchanged": 327, "gameplay_authority": False,
        "native_dll_built": False, "installed": False, "game_accessed": False,
        "geck_required": False, "playtest_required": False, "new_runtime_dependencies": [],
        "checks_passed": int(match[1]), "deterministic_selections": int(match[2]),
        "compiler": "MSVC x86 /std:c++17 /W4 /WX /permissive-", "pointer_size_asserted": 4,
        "source_inputs": source_before,
        "existing_native_files_unchanged": len(unchanged),
        "existing_native_documentation_updated": ["native/NVOCombatModel/README.md"],
        "build_definitions_unchanged": [record(p, ROOT) for p in builds],
        "test_executable": record(MODEL / "out-response/response_checks.exe", ROOT),
        "limitations": [
            "Symbolic response definitions only; no new numeric material/damage calculation.",
            "All test profiles are synthetic; no production armour or creature record mappings.",
            "No actual-hit evidence, engine integration, application or runtime stress benchmark.",
            "Previous model/adapter/energy/flight implementations unchanged; old checks were not rerun.",
            "No game files inspected; unchanged source build definitions do not prove current live installation."
        ]
    }
    write(STEP / "Evidence/VERIFICATION.json", verification)
    write(STEP / "Evidence/UNCHANGED-NATIVE.json", {"baseline": "4D", "files": unchanged})
    for name in ("README.md", "RESPONSE-DESIGN.md", "REVIEW.md", "START-HERE.html"):
        copy(STEP / name, RELEASE / name)
    for name in SOURCES:
        copy(MODEL / name, RELEASE / "Source" / name)
    for path in sorted((STEP / "Evidence").glob("*")):
        if path.is_file():
            copy(path, RELEASE / "Evidence" / path.name)
    copy(ROOT / "CREDITS.md", RELEASE / "CREDITS.md")
    copy(ROOT / "LICENSE", RELEASE / "LICENSE")
    for name in ("THIRD-PARTY-NOTICES.md", "LICENSE-GPL-3.0.txt", "LICENSE-ITR-MIT.txt"):
        copy(ROOT / "native/NVOCombatCore" / name, RELEASE / "Notices" / name)
    for link in re.findall(r'href="([^"]+)"', (RELEASE / "START-HERE.html").read_text()):
        if not (RELEASE / link).is_file():
            raise RuntimeError(f"Missing page link: {link}")
    for name in SOURCES:
        if sha(MODEL / name) != sha(RELEASE / "Source" / name):
            raise RuntimeError("Packaged source differs from checked source")
    # Explicit deliverables only. Do not sweep a user's later build outputs into the packet.
    deliverables = [RELEASE / name for name in ("README.md", "RESPONSE-DESIGN.md", "REVIEW.md", "START-HERE.html", "CREDITS.md", "LICENSE")]
    deliverables += [RELEASE / "Source" / name for name in SOURCES]
    deliverables += list((RELEASE / "Evidence").glob("*")) + list((RELEASE / "Notices").glob("*"))
    write(RELEASE / "MANIFEST.json", {"packet": "4F", "status": "PREPARED_OFFLINE",
          "files": [record(p, RELEASE) for p in sorted(deliverables) if p.is_file()]})
    bundle = RELEASE.with_suffix(".zip")
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(deliverables + [RELEASE / "MANIFEST.json"]):
            if path.is_file():
                archive.write(path, str(Path(RELEASE.name) / path.relative_to(RELEASE)))
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP integrity failure")
        for item in json.loads((RELEASE / "MANIFEST.json").read_text())["files"]:
            if hashlib.sha256(archive.read(RELEASE.name + "/" + item["path"])).hexdigest() != item["sha256"]:
                raise RuntimeError("Archive hash mismatch")
    write(STEP / "PACKAGE.json", {"path": str(bundle), "sha256": sha(bundle),
          "bytes": bundle.stat().st_size, "status": "PREPARED_OFFLINE"})
    print(json.dumps({"packet": str(RELEASE), "checks": int(match[1]),
                      "repetitions": int(match[2]), "unchanged_native_files": len(unchanged),
                      "game_accessed": False, "zip_sha256": sha(bundle)}))


if __name__ == "__main__":
    main()

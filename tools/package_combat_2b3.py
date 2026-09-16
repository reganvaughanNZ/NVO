"""Package the compiled 2B3 checkpoint. Does not install or execute game code."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
project = root / "native/NVOCombatCore"
build = project / "out/build-10490-9131"
release = root / "release"
name = "NVO-Combat-Packet-2B3"
compiled = release / (name + "-Compiled")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

expected = {
    "NVOCombatCore.dll": "befcede7a6faec5032ea333bb0ae8a1777d78aeb01620e4ee65aa1699ed975b0",
    "NVOCombatCore.pdb": "cf0d20b2a21c2ca52701bd86feb349f847bc733992a540b5a02387699187e792",
}
for filename, sha in expected.items():
    if digest(build / filename) != sha:
        raise SystemExit("Build artifact changed: " + filename)

source = [project / n for n in (
    "BUILD.cmd", "CMakeLists.txt", "README.md", "START-HERE.html",
    "BUILD-RESULT.md", "SDK-BOUNDARY.md", "sdk-reference.json",
    "THIRD-PARTY-NOTICES.md", "LICENSE-GPL-3.0.txt",
)]
source += sorted((project / "include").glob("*.hpp"))
source += sorted((project / "src").glob("*.cpp"))
source += [project / "src/Exports.def"]
manifest = {
    "packet": "NVO combat 2B3", "version": "0.2.2", "plugin_version": 202,
    "prepared": "2026-09-14", "status": "Compiled/static inspection complete; awaiting user current-hit capture",
    "assistant_built": True, "assistant_game_tested": False, "installed_by_assistant": False,
    "current_hit_observer": "Guarded JIP CopyHitData input wrapper, two process vtable slots",
    "engine_damage_calculation_hooks": False, "damage_replacement_enabled": False,
    "native_event_handlers": 6, "event_limit_per_capture": 600,
    "current_context_limit_per_capture": 200, "process_log_row_limit": 8192,
    "lifetime_slots": 512, "license": "GPL-3.0-only",
    "dependencies": ["Inspected normal FNV 1.4.0.525 PE32 build", "xNVSE >=6.4.8 major 6",
                     "Inspected JIP LN 57.30 build with matching function/slot guards", "ShowOff provider events (184 inspected)"],
    "additional_dependencies_added": [],
    "installed_files": [{"path": "Data/NVSE/Plugins/" + n, "sha256": sha} for n, sha in expected.items()],
    "build_output": str(build.relative_to(project)),
    "generated_log": "Game root/NVOCombatCore.log",
    "source_files": [{"path": p.relative_to(project).as_posix(), "sha256": digest(p)} for p in source],
    "limits": "Copy-input fields are not final HP loss or damage-application counts. No flight, injury or native save-state implementation.",
}
(project / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
source.append(project / "manifest.json")
compiled.mkdir(parents=True, exist_ok=True)
destination = compiled / "Data/NVSE/Plugins"
destination.mkdir(parents=True, exist_ok=True)
for filename in expected:
    shutil.copyfile(build / filename, destination / filename)
for p in source:
    target = compiled / "Source/NVOCombatCore" / p.relative_to(project)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, target)
    if p.parent == project:
        # Build helpers belong in corresponding source, not the install guide root.
        if p.suffix not in (".cmd",) and p.name != "CMakeLists.txt":
            shutil.copyfile(p, compiled / p.name)
evidence = compiled / "build-evidence"
evidence.mkdir(exist_ok=True)
for filename in ("build.log", "toolchain.log", "dll-details.txt", "wrapper-disassembly.txt"):
    shutil.copyfile(build / filename, evidence / filename)
shutil.copyfile(project / "BUILD-RESULT.md", evidence / "BUILD-RESULT.md")

source_archive = release / (name + "-Source.zip")
with zipfile.ZipFile(source_archive, "w", zipfile.ZIP_DEFLATED) as archive:
    for p in source:
        archive.write(p, "NVOCombatCore/" + p.relative_to(project).as_posix())
compiled_archive = release / (name + "-Compiled.zip")
with zipfile.ZipFile(compiled_archive, "w", zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(compiled.rglob("*")):
        if p.is_file():
            archive.write(p, p.relative_to(compiled).as_posix())
print(json.dumps({"compiled": str(compiled_archive), "source": str(source_archive),
                  "guide": str(compiled / "START-HERE.html"),
                  "source_files": len(source), "compiled_bytes": compiled_archive.stat().st_size,
                  "compiled_zip_sha256": digest(compiled_archive)}, indent=2))

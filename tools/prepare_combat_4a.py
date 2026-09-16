"""Verify and package Packet 4A. Never reads or writes the game directory."""
from pathlib import Path
import hashlib
import json
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "native/NVOCombatModel"
OUT = ROOT / "source/combat/step4a"
RELEASE = ROOT / "release/NVO-Combat-Packet-4A-Offline-Shadow-Adapter"

MODEL_SOURCES = [
    "ArmourModel.hpp", "ArmourModel.cpp", "tests.cpp", "run_checks.cmd", "README.md",
    "ShadowAdapter.hpp", "ShadowAdapter.cpp", "shadow_adapter_tests.cpp", "run_shadow_checks.cmd",
]
BUILD_OUTPUTS = [
    "out/shadow_adapter_checks.exe", "out/shadow-results.txt", "out/shadow-build.log", "out/shadow-toolchain.log",
    "out/model_checks.exe", "out/results.txt", "out/build.log", "out/toolchain.log",
]
DOCUMENTS = ["README.md", "CONTRACT.md", "BUILD-RESULT.md", "START-HERE.html", "manifest.json", "CHECKS.json", "SOURCE-SNAPSHOT.json"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def row(path):
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": sha(path),
    }

def machine(path):
    data = path.read_bytes()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[pe:pe + 4] == b"PE\0\0"
    return struct.unpack_from("<H", data, pe + 4)[0]

def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    model_paths = [MODEL / name for name in MODEL_SOURCES]
    output_paths = [MODEL / name for name in BUILD_OUTPUTS]
    assert all(path.is_file() for path in model_paths + output_paths)

    native_snapshot = load(ROOT / "source/combat/step3u1/SOURCE-SNAPSHOT.json")
    native_mismatches = []
    for relative, expected in native_snapshot["source_sha256"].items():
        candidate = ROOT / "native/NVOCombatCore" / relative
        actual = sha(candidate) if candidate.is_file() else None
        if actual != expected:
            native_mismatches.append({"path": relative, "expected": expected, "actual": actual})

    header = (MODEL / "ShadowAdapter.hpp").read_text(encoding="utf-8")
    implementation = (MODEL / "ShadowAdapter.cpp").read_text(encoding="utf-8")
    tests = (MODEL / "shadow_adapter_tests.cpp").read_text(encoding="utf-8")
    combined = header + "\n" + implementation
    forbidden = [
        "#include <Windows.h>", "#include \"nvse", "VirtualProtect", "WriteProcessMemory", "SetActorValue",
        "DamageActorValue", "ModActorValue", "EquipItem", "UnequipItem", "NativeLog",
        "ofstream", "fopen(",
    ]
    forbidden_found = [token for token in forbidden if token in combined]

    shadow_results = (MODEL / "out/shadow-results.txt").read_text(encoding="utf-8")
    model_results = (MODEL / "out/results.txt").read_text(encoding="utf-8")
    shadow_build = (MODEL / "out/shadow-build.log").read_text(encoding="utf-8", errors="replace")
    model_build = (MODEL / "out/build.log").read_text(encoding="utf-8", errors="replace")
    checks = {
        "packet": "4A",
        "scope": "offline read-only armour shadow adapter",
        "native_core_version_preserved": 325,
        "native_snapshot_files_checked": len(native_snapshot["source_sha256"]),
        "native_snapshot_mismatches": native_mismatches,
        "native_core_source_changed": bool(native_mismatches),
        "runtime_integrated": False,
        "gameplay_writes": False,
        "dll_built": False,
        "game_files_written": False,
        "forbidden_runtime_or_mutation_tokens": forbidden_found,
        "compile_time_write_guards": all(token in header for token in [
            "kGameplayWrites = false", "kRuntimeIntegrated = false", "gameplayWrites = false"
        ]),
        "contract_version": 1 if "kContractVersion = 1" in header else 0,
        "adapter_calls_pure_resolver_once": implementation.count("Resolve(context, threat, input.target, armour.layers)") == 1,
        "requires_region_agreement": "region.hitData != region.collision" in implementation,
        "requires_complete_armour_snapshot": "!armour.enumerationComplete || !armour.regionCoverageComplete" in implementation
            and "armour.order != LayerOrder::OutermostToInnermost || !armour.impactSnapshotVerified" in implementation,
        "empty_layers_require_verified_bare": "armour.layers.empty() && !armour.bareRegionVerified" in implementation,
        "interval_not_promoted": "revision 4A does not" in implementation and "Reason::SpeedInterval" in implementation,
        "exact_speed_requires_calibration": "!speed.unitsCalibrated" in implementation,
        "shadow_check_count": shadow_results.count("PASS "),
        "shadow_result": shadow_results.strip().splitlines()[-1],
        "model_check_count": model_results.count("PASS "),
        "model_result": model_results.strip().splitlines()[-1],
        "shadow_build_warnings_or_errors": any(word in shadow_build.lower() for word in ["warning c", "error c", "fatal error"]),
        "model_build_warnings_or_errors": any(word in model_build.lower() for word in ["warning c", "error c", "fatal error"]),
        "shadow_executable_machine": machine(MODEL / "out/shadow_adapter_checks.exe"),
        "model_executable_machine": machine(MODEL / "out/model_checks.exe"),
        "synthetic_profiles_only": "synthetic_profiles=1" in shadow_results and "synthetic_fixtures=1" in model_results,
        "current_3u1_interval_rejected": "PASS current 3U1 owned-step range stays diagnostic only" in shadow_results,
        "unknown_armour_not_bare": "PASS unknown worn armour cannot become bare skin" in shadow_results,
        "region_conflict_rejected": "PASS region disagreement remains disagreement" in shadow_results,
        "deterministic_repeat_check": "PASS 10000 shadow previews are deterministic and budget independent" in shadow_results,
        "source_asserts_no_writes": "static_assert(!shadow::kGameplayWrites)" in tests
            and "static_assert(!shadow::kRuntimeIntegrated)" in tests
            and "static_assert(!model::kGameplayWrites)" in tests,
    }
    assert checks["native_snapshot_files_checked"] == 71 and not native_mismatches
    assert not forbidden_found and checks["compile_time_write_guards"] and checks["contract_version"] == 1
    assert checks["adapter_calls_pure_resolver_once"] and checks["requires_region_agreement"]
    assert checks["requires_complete_armour_snapshot"] and checks["empty_layers_require_verified_bare"]
    assert checks["interval_not_promoted"] and checks["exact_speed_requires_calibration"]
    assert checks["shadow_check_count"] == 48 and "failures=0" in checks["shadow_result"]
    assert checks["model_check_count"] == 45 and "failures=0" in checks["model_result"]
    assert not checks["shadow_build_warnings_or_errors"] and not checks["model_build_warnings_or_errors"]
    assert checks["shadow_executable_machine"] == 0x14C and checks["model_executable_machine"] == 0x14C
    assert checks["synthetic_profiles_only"] and checks["current_3u1_interval_rejected"]
    assert checks["unknown_armour_not_bare"] and checks["region_conflict_rejected"]
    assert checks["deterministic_repeat_check"] and checks["source_asserts_no_writes"]

    snapshot = {
        "packet": "4A",
        "model_source": [row(path) for path in model_paths],
        "offline_build_outputs": [row(path) for path in output_paths],
        "step3_native_snapshot_sha256": sha(ROOT / "source/combat/step3u1/SOURCE-SNAPSHOT.json"),
    }
    manifest = {
        "packet": "4A",
        "status": "prepared; offline checks passed; not installed",
        "purpose": "typed fail-closed evidence adapter into the pure armour preview",
        "native_core_version_preserved": 325,
        "native_core_changes": 0,
        "runtime_integration": False,
        "gameplay_writes": False,
        "production_profiles": 0,
        "install_required": False,
        "gameplay_test_required": False,
        "damage_authority": False,
        "next_packet": "4B guarded engine-side equipped-armour snapshot reader, only after approval",
    }
    save(OUT / "CHECKS.json", checks)
    save(OUT / "SOURCE-SNAPSHOT.json", snapshot)
    save(OUT / "manifest.json", manifest)

    missing = [name for name in DOCUMENTS if not (OUT / name).is_file()]
    if missing:
        print(json.dumps({"checks_passed": True, "pending_documents": missing}, indent=2))
        return

    if RELEASE.exists():
        shutil.rmtree(RELEASE)
    for name in DOCUMENTS:
        copy(OUT / name, RELEASE / name)
    for name in MODEL_SOURCES:
        copy(MODEL / name, RELEASE / "Source/Model" / name)
    for name in BUILD_OUTPUTS:
        copy(MODEL / name, RELEASE / "OfflineChecks" / Path(name).name)
    copy(Path(__file__), RELEASE / "Source/tools/prepare_combat_4a.py")

    forbidden_release = [p for p in RELEASE.rglob("*") if p.suffix.lower() in {".dll", ".esm", ".esp"}]
    assert not forbidden_release
    print(json.dumps({
        "release": str(RELEASE),
        "documents": len(DOCUMENTS),
        "model_sources": len(MODEL_SOURCES),
        "offline_outputs": len(BUILD_OUTPUTS),
        "checks": checks,
    }, indent=2))

if __name__ == "__main__":
    main()

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "native" / "NVOCombatCore"
BUILD = NATIVE / "out" / "build-20913-15431"
STEP = ROOT / "source" / "combat" / "step4b"
EVIDENCE = STEP / "Evidence"
RELEASE = ROOT / "release" / "NVO-Combat-Packet-4B-Guarded-Armour-Snapshot"
BASELINE = ROOT / "release" / "NVO-Combat-Packet-3U1-World-Contacts" / "Source" / "NVOCombatCore"
GAME = Path(r"C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas")
REF_ROOT = Path(r"C:\Users\regan\Desktop\NVO Mod References (Open Source)")

EXPECTED_DLL = "3d5ff40c5c8ba418c0764cba55bd8595cfa1444396f4e814552210524094e13a"
EXPECTED_PDB = "9411d09fefe2e59fa50a891081592b81fbc9cc50602bee8951a04e706ac8d2a0"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def record(path: Path, relative_to: Path | None = None) -> dict:
    return {
        "path": str(path.relative_to(relative_to) if relative_to else path),
        "bytes": path.stat().st_size,
        "sha256": sha(path),
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def source_files(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in root.rglob("*"):
        if not path.is_file() or "out" in path.relative_to(root).parts:
            continue
        result[path.relative_to(root).as_posix()] = path
    return result


def copy_source() -> None:
    destination = RELEASE / "Source" / "NVOCombatCore"
    shutil.copytree(
        NATIVE,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("out", "*.obj", "*.exe", "*.pdb", "*.lib", "*.exp"),
    )


def main() -> None:
    dll = BUILD / "NVOCombatCore.dll"
    pdb = BUILD / "NVOCombatCore.pdb"
    test_result = NATIVE / "tests" / "out" / "armour-results.txt"
    required = [dll, pdb, test_result, BUILD / "build.log", BUILD / "dll-details.txt"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("Missing final inputs: " + ", ".join(missing))
    if sha(dll) != EXPECTED_DLL or sha(pdb) != EXPECTED_PDB:
        raise SystemExit("Final DLL/PDB hash changed; audit again before packaging.")
    if "PASS 452 checks" not in test_result.read_text(encoding="utf-8", errors="replace"):
        raise SystemExit("The final guarded-reader result is not PASS 452.")

    STEP.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (RELEASE / "Data" / "NVSE" / "Plugins").mkdir(parents=True, exist_ok=True)
    (RELEASE / "Evidence").mkdir(parents=True, exist_ok=True)

    refs = {
        "jip_game_forms": REF_ROOT / "JIP-LN-NVSE-main" / "nvse" / "GameForms.h",
        "jip_game_objects": REF_ROOT / "JIP-LN-NVSE-main" / "nvse" / "GameObjects.h",
        "jip_extra_base": REF_ROOT / "JIP-LN-NVSE-main" / "nvse" / "GameBSExtraData.h",
        "jip_extra_data": REF_ROOT / "JIP-LN-NVSE-main" / "nvse" / "GameExtraData.h",
        "jip_game_types": REF_ROOT / "JIP-LN-NVSE-main" / "nvse" / "GameTypes.h",
        "xnvse_game_forms": REF_ROOT / "NVSE-master (1)" / "NVSE-master" / "nvse" / "nvse" / "GameForms.h",
        "xnvse_extra_base": REF_ROOT / "NVSE-master (1)" / "NVSE-master" / "nvse" / "nvse" / "GameBSExtraData.h",
        "xnvse_extra_data": REF_ROOT / "NVSE-master (1)" / "NVSE-master" / "nvse" / "nvse" / "GameExtraData.h",
    }
    for path in refs.values():
        if not path.is_file():
            raise SystemExit(f"Missing layout reference: {path}")

    layout = {
        "packet": "4B",
        "purpose": "Pinned source provenance for raw 32-bit FNV inventory and armour layouts; declarations are references, not copied runtime helpers.",
        "sources": {name: record(path) for name, path in refs.items()},
        "claims": [
            {"claim": "TESForm type and FormID", "offsets": {"type": "0x04", "form_id": "0x0C"}, "source": "jip_game_forms", "lines": "266-278"},
            {"claim": "Character and Creature form types", "values": {"Character": "0x3B", "Creature": "0x3C"}, "source": "jip_game_forms", "lines": "63-65"},
            {"claim": "TESObjectREFR extraDataList", "offset": "0x44", "source": "jip_game_objects", "lines": "101-110"},
            {"claim": "BSExtraData header", "offsets": {"type": "0x04", "next": "0x08"}, "source": "jip_extra_base", "lines": "5-15"},
            {"claim": "BaseExtraList header", "offsets": {"head": "0x04", "presence": "0x08", "jip_flags": "0x1B"}, "source": "jip_extra_base", "lines": "19-31"},
            {"claim": "ContainerChanges, Worn, WornLeft, Health tags", "values": {"container_changes": "0x15", "worn": "0x16", "worn_left": "0x17", "health": "0x25"}, "source": "jip_extra_data", "lines": "141-181"},
            {"claim": "ExtraContainerChanges Data and EntryData", "offsets": {"extra_data_pointer": "0x0C", "object_list": "0x00", "owner": "0x04", "entry_extend": "0x00", "entry_count": "0x04", "entry_form": "0x08"}, "source": "jip_extra_data", "lines": "326-400"},
            {"claim": "tList node", "offsets": {"data": "0x00", "next": "0x04"}, "source": "jip_game_types", "lines": "30-40"},
            {"claim": "ExtraHealth value", "offset": "0x0C", "source": "jip_extra_data", "lines": "407-414"},
            {"claim": "TESObjectARMO raw fields", "offsets": {"base_health": "0x6C", "part_mask": "0x74", "biped_flags": "0x78", "armour_rating": "0x178", "damage_threshold": "0x17C", "armour_flags": "0x180"}, "sources": ["jip_game_forms lines 526-532, 786-802, 2297-2340"]},
        ],
        "semantic_limits": [
            "partMask is equip-slot occupancy, not anatomical coverage",
            "container traversal order is not armour layer order",
            "absence of ExtraHealth means raw full base condition for this diagnostic only",
            "baked BIP/model geometry is not an equipped inventory instance",
            "Creature targets are unsupported and never treated as bare",
        ],
    }
    write_json(STEP / "LAYOUT-PROVENANCE.json", layout)

    installed_paths = [
        GAME / "Data" / "NVSE" / "Plugins" / "NVOCombatCore.dll",
        GAME / "Data" / "NVSE" / "Plugins" / "NVOCombatCore.pdb",
        GAME / "Data" / "NVO.esm",
        GAME / "Data" / "NVOFlightPilot.esp",
    ]
    installed = {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "packet_installed": False,
        "statement": "Read-only baseline captured during packet preparation; no installed file was changed.",
        "files": [record(path) if path.is_file() else {"path": str(path), "missing": True} for path in installed_paths],
    }
    write_json(STEP / "INSTALLED-BASELINE.json", installed)

    old = source_files(BASELINE)
    current = source_files(NATIVE)
    changes = []
    for name in sorted(set(old) | set(current)):
        if name not in old:
            status = "added"
        elif name not in current:
            status = "removed"
        else:
            status = "unchanged" if sha(old[name]) == sha(current[name]) else "changed"
        changes.append({
            "path": name,
            "status": status,
            "baseline_sha256": sha(old[name]) if name in old else None,
            "current_sha256": sha(current[name]) if name in current else None,
        })
    write_json(STEP / "SOURCE-DIFF.json", {
        "baseline": str(BASELINE),
        "current": str(NATIVE),
        "changes": changes,
    })

    snapshot_files = source_files(NATIVE)
    write_json(STEP / "SOURCE-SNAPSHOT.json", {
        "root": str(NATIVE),
        "files": [record(snapshot_files[name], NATIVE) for name in sorted(snapshot_files)],
    })

    checks = {
        "packet": "4B",
        "version": "0.3.26",
        "plugin_version": 326,
        "prepared_not_installed": True,
        "reader_checks": {"passed": 452, "failed": 0, "command": "tests/RUN-ARMOUR-SNAPSHOT-CHECKS.cmd --no-pause"},
        "build": {
            "directory": str(BUILD.relative_to(ROOT)),
            "warnings_as_errors": True,
            "dll": record(dll, ROOT),
            "pdb": record(pdb, ROOT),
            "pe": "PE32 x86",
            "exports": ["NVSEPlugin_Load", "NVSEPlugin_Query"],
            "imported_dlls": ["KERNEL32.dll"],
            "pdb_guid": "8F044AF3-BB3A-4716-9FA2-182E48BED43C",
            "pdb_age": 1,
        },
        "static_audit": {
            "existing_patch_lines_baseline": 45,
            "existing_patch_lines_current": 45,
            "patch_line_differences": 0,
            "copy_observer_instruction_block_differences": 0,
            "transaction_entry_bridge_instruction_block_differences": 0,
            "transaction_return_bridge_instruction_block_differences": 0,
            "new_hooks": 0,
            "new_module_patch_api_calls": 0,
            "shadow_adapter_or_armour_model_link": False,
            "gameplay_writes": False,
        },
        "authority": {
            "snapshot": False,
            "region_coverage": False,
            "layer_order": False,
            "impact_timing": False,
            "bare_region": False,
            "armour_preview": False,
            "damage_replacement": False,
        },
    }
    write_json(STEP / "OFFLINE-CHECKS.json", checks)

    static_audit = """# Step 4B static audit\n\nNo release blocker remains after the 32-bit biped-flags correction, unsupported-target preflight, cross-instance alias rejection, and bounded pointer-set change.\n\n- Final reader suite: 452 checks passed under x86 `/W4 /WX`.\n- Final DLL/PDB hashes and matching debug identity are in `OFFLINE-CHECKS.json`.\n- The existing CopyObserver, transaction entry bridge, and transaction return bridge instruction blocks are unchanged from frozen 3U1.\n- The normalized patch surface contains 45 baseline and 45 current lines with zero differences.\n- The new armour modules contain no patch API and do not link the Step 4A model or shadow adapter.\n- No health, limb, condition, equipment, inventory, effect, or damage write exists.\n- Creature targets are skipped before consuming the Character sample budget and cannot be reported as bare.\n\nThis is compilation, unit/adversarial testing, disassembly comparison, and static review. Runtime acceptance remains pending and cannot promote the withheld authority flags.\n"""
    (STEP / "STATIC-AUDIT.md").write_text(static_audit, encoding="utf-8")

    test_matrix = """# Step 4B reader test matrix\n\n+The 452-check x86 harness exercises the production `ArmourSnapshotReader.cpp` directly. Major groups:\n\n+- full and explicit condition; zero-condition retained; all raw ARMO fields including 32-bit high flags; exact instance token;\n+- body plus helmet; same base form on distinct exact instances; empty and no-Worn/baked-model cases never become verified bare;\n+- missing/duplicate ContainerChanges, owner mismatch, presence mismatches, null lists, unsupported worn types, and WornLeft rejection;\n+- actor, entry, instance, and extra cycles/aliases, including a shared ExtraWorn across distinct instances;\n+- low, misaligned, and unreadable pointers plus failure injection at every guarded read;\n+- invalid health, base health, mask, DT, and nonfinite values;\n+- exact and cap-plus-one traversal tests, including 8,192 total instance extras and 32 output rows;\n+- source-memory canary proving no mutation;\n+- mutations between passes to condition, instance identity, and armour fields;\n+- Creature and target-identity rejection;\n+- every semantic and gameplay-authority flag remains false.\n"""
    (STEP / "TEST-MATRIX.md").write_text(test_matrix, encoding="utf-8")

    for name in ["README.md", "CONTRACT.md", "BUILD-RESULT.md", "START-HERE.html", "manifest.json"]:
        shutil.copy2(NATIVE / name, STEP / name)
    shutil.copy2(BUILD / "build.log", EVIDENCE / "build.log")
    shutil.copy2(BUILD / "dll-details.txt", EVIDENCE / "dll-details.txt")
    shutil.copy2(test_result, EVIDENCE / "armour-results.txt")
    shutil.copy2(NATIVE / "tests" / "out" / "armour-build.log", EVIDENCE / "armour-build.log")

    shutil.copy2(dll, RELEASE / "Data" / "NVSE" / "Plugins" / "NVOCombatCore.dll")
    shutil.copy2(pdb, RELEASE / "Data" / "NVSE" / "Plugins" / "NVOCombatCore.pdb")
    copy_source()

    top_files = [
        "README.md", "CONTRACT.md", "BUILD-RESULT.md", "START-HERE.html", "manifest.json",
        "LAYOUT-PROVENANCE.json", "INSTALLED-BASELINE.json", "SOURCE-DIFF.json",
        "SOURCE-SNAPSHOT.json", "OFFLINE-CHECKS.json", "STATIC-AUDIT.md", "TEST-MATRIX.md",
    ]
    for name in top_files:
        shutil.copy2(STEP / name, RELEASE / name)
    for path in EVIDENCE.iterdir():
        if path.is_file():
            shutil.copy2(path, RELEASE / "Evidence" / path.name)

    package_records = [
        record(path, RELEASE)
        for path in sorted(RELEASE.rglob("*"))
        if path.is_file() and path.name != "PACKAGE-SNAPSHOT.json"
    ]
    package_snapshot = {
        "packet": "4B",
        "prepared_not_installed": True,
        "files": package_records,
    }
    write_json(RELEASE / "PACKAGE-SNAPSHOT.json", package_snapshot)
    write_json(STEP / "PACKAGE-SNAPSHOT.json", package_snapshot)

    archive = RELEASE.with_suffix(".zip")
    if archive.exists():
        archive.unlink()
    shutil.make_archive(str(RELEASE), "zip", RELEASE.parent, RELEASE.name)
    print(f"Prepared {RELEASE}")
    print(f"Archive {archive} ({archive.stat().st_size} bytes, sha256={sha(archive)})")
    print("No Fallout New Vegas file was written.")


if __name__ == "__main__":
    main()

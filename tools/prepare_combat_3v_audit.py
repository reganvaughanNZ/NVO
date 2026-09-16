"""Freeze and package the Step 3 closure audit. Never loads or writes the game."""
from pathlib import Path
import configparser, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "native/NVOCombatCore"
MODEL = ROOT / "native/NVOCombatModel"
OUT = ROOT / "source/combat/step3v"
RELEASE = ROOT / "release/NVO-Combat-Packet-3V-Step3-Closure-Audit"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

def load_json(path):
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return json.loads(data.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    raise ValueError(f"Could not decode JSON: {path}")

def row(path):
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha(path)}

def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    active = []
    for path in CORE.rglob("*"):
        relative = path.relative_to(CORE)
        if path.is_file() and "out" not in relative.parts and (
            relative.parts[0] in {"src", "include", "config", "tests", "reference"}
            or relative.name in {"BUILD.cmd", "CMakeLists.txt", "manifest.json", "SDK-BOUNDARY.md", "sdk-reference.json"}
        ):
            active.append(path)
    model = [p for p in MODEL.iterdir() if p.is_file() and p.suffix.lower() in {".cpp", ".hpp", ".inl", ".md", ".cmd"}]
    evidence_names = [
        "source/combat/PRE-DAMAGE-REVIEW.md",
        "source/combat/PROJECTILE-SCOPE.md",
        "source/combat/review/ULTRA-317-REVIEW.md",
        "source/combat/review/ULTRA-317-FINDINGS.json",
        "source/combat/review/REVIEW-STATUS.md",
        "source/combat/review/FOLLOWUP-3J.md",
        "source/combat/review/FOLLOWUP-3K.md",
        "source/combat/review/FOLLOWUP-3L.md",
        "source/combat/review/FOLLOWUP-3M.md",
        "source/combat/review/FOLLOWUP-3N.md",
        "source/combat/review/FOLLOWUP-3O.md",
        "source/combat/review/FOLLOWUP-3P.md",
        "source/combat/review/FOLLOWUP-3Q.md",
        "source/combat/review/FOLLOWUP-3R.md",
        "source/combat/review/FOLLOWUP-3T.md",
        "source/combat/review/FOLLOWUP-3U.md",
        "source/combat/step3h/CONTRACT.md",
        "source/combat/step3h/REVIEW-1.md",
        "source/combat/step3j/INSTALLED-MASTER-CHECK.json",
        "source/combat/step3j/STARTUP-REVIEW.json",
        "source/combat/step3m/CONTRACT.md",
        "source/combat/step3n/SAVED-CHECKPOINT.md",
        "source/combat/step3n/SAVED-RECORD-REVIEW.json",
        "source/combat/step3o/manifest.json",
        "source/combat/step3q/RUNTIME-RESULT.json",
        "source/combat/step3r/RUNTIME-RESULT.json",
        "source/combat/step3r1/STATIC-CHECKS.json",
        "source/combat/step3s/CONTRACT.md",
        "source/combat/step3s/CHECKS.json",
        "source/combat/step3s/REPLAY-RESULT.json",
        "source/combat/step3t/CONTRACT.md",
        "source/combat/step3t/RESULT.json",
        "source/combat/step3u/CONTRACT.md",
        "source/combat/step3u/REPLAY-RESULT.json",
        "source/combat/step3u/RUNTIME-RESULT.json",
        "source/combat/step3u1/CONTRACT.md",
        "source/combat/step3u1/SOURCE-SNAPSHOT.json",
        "source/combat/step3u1/OFFLINE-RESULT.json",
        "source/combat/step3u1/RUNTIME-RESULT.json",
        "source/combat/step3u1/RECHECK-RESULT.json",
        "source/combat/step3u1/STATIC-CHECKS.json",
        "source/combat/step3u1/ULTRA-3U1-AUDIT.md",
        "source/combat/step3u1/INSTALL-3U1-result.json",
        "source/combat/step3u1/captures/review-7337bf485a5c/NVOCombatCore.log",
        "source/combat/step3u1/captures/recheck-01a7dd5ef0cd/NVOCombatCore.log",
    ]
    evidence = [ROOT / name for name in evidence_names]
    assert all(p.is_file() for p in evidence)

    manifest = load_json(CORE / "manifest.json")
    static = load_json(ROOT / "source/combat/step3u1/STATIC-CHECKS.json")
    offline = load_json(ROOT / "source/combat/step3u1/OFFLINE-RESULT.json")
    runtime = load_json(ROOT / "source/combat/step3u1/RUNTIME-RESULT.json")
    recheck = load_json(ROOT / "source/combat/step3u1/RECHECK-RESULT.json")
    install = load_json(ROOT / "source/combat/step3u1/INSTALL-3U1-result.json")
    energy = load_json(ROOT / "source/combat/step3s/REPLAY-RESULT.json")["summary"]
    capacity = load_json(ROOT / "source/combat/step3r/RUNTIME-RESULT.json")
    baron = load_json(ROOT / "source/combat/step3n/SAVED-RECORD-REVIEW.json")
    snapshot = load_json(ROOT / "source/combat/step3u1/SOURCE-SNAPSHOT.json")
    snapshot_hashes = snapshot["source_sha256"]
    snapshot_mismatches = []
    for relative, expected in snapshot_hashes.items():
        candidate = CORE / relative
        actual = sha(candidate) if candidate.is_file() else None
        if actual != expected:
            snapshot_mismatches.append({"path": relative, "expected": expected, "actual": actual})

    actor_log = ROOT / "source/combat/step3u1/captures/review-7337bf485a5c/NVOCombatCore.log"
    world_log = ROOT / "source/combat/step3u1/captures/recheck-01a7dd5ef0cd/NVOCombatCore.log"

    preview = configparser.ConfigParser(interpolation=None)
    preview.read(CORE / "config/NVOFlightPreview.ini", encoding="utf-8")
    profiles = [s for s in preview.sections() if s != "Preview"]
    selectable = [s for s in profiles if preview.getboolean(s, "select_on_fire")]
    pilot = [s for s in profiles if not preview.getboolean(s, "select_on_fire")]

    plugin = (CORE / "src/Plugin.cpp").read_text()
    contact = (CORE / "src/FlightContactSpeed.inl").read_text()
    join = (CORE / "src/FlightImpactJoin.inl").read_text()
    checks = {
        "packet": "3V",
        "audit_only": True,
        "game_loaded": False,
        "game_files_written": False,
        "native_source_written": False,
        "native_version": manifest["plugin_version"],
        "native_status": manifest["status"],
        "snapshot_source_files": len(snapshot_hashes),
        "snapshot_source_mismatches": snapshot_mismatches,
        "actor_capture_hash_verified": sha(actor_log) == runtime["capture_sha256"],
        "world_capture_hash_verified": sha(world_log) == recheck["capture_sha256"],
        "damage_replacement_off": manifest["damage_replacement"] is False and "damage_replacement=0" in plugin,
        "no_damage_hooks": "damage_hooks=0" in plugin,
        "contact_speed_damage_authority_false": "static constexpr bool damageAuthority=false" in contact,
        "hit_join_speed_authority_false": "speed_authority=0" in join and "region_authority=0" in join,
        "capacity_probe_disabled": static["capacity_probe_enabled"] is False,
        "matching_binary_pair": static["pdb_pair_verified"] is True,
        "new_hooks_in_3u1": static["new_hooks"],
        "profile_count": len(profiles),
        "select_on_fire_profiles": selectable,
        "pilot_only_profiles": pilot,
        "world_reference_reader_checks": offline["reader"]["checks"],
        "reference_runtime_partial_capture": runtime["capture_sha256"],
        "reference_actor_join_preserved": runtime["actor_reference_join_preserved"],
        "world_runtime_capture": recheck["capture_sha256"],
        "world_runtime_pass": recheck["verdict"] == "pass" and recheck["world_contact"]["target_kind"] == 1,
        "terrain_clamp_live": recheck["terrain_clamp_explained"],
        "installed_pair": install["status"] == "installed" and install["version"] == 325,
        "protected_files_verified": install["protected_files_verified"],
        "controlled_capacity_refusal_pass": capacity["checks"]["probe_once_and_actual_full_refusal"] and capacity["checks"]["stock_base_passed_and_returned"],
        "baron_registrations_remaining": baron["remaining_registrations"],
        "rd_free_record": baron["masters_preserved_RD_free"],
        "authoritative_energy_records": energy["authoritative_energy_records"],
        "energy_damage_authority": energy["checks"]["damage_authority"],
        "exact_contact_speed_authority": manifest["exact_contact_speed_authority"],
        "pre_movement_contacts": manifest["pre_movement_contacts"],
    }
    assert checks["native_version"] == 325
    assert checks["snapshot_source_files"] == 71 and checks["snapshot_source_mismatches"] == []
    assert checks["actor_capture_hash_verified"] and checks["world_capture_hash_verified"]
    assert checks["damage_replacement_off"] and checks["no_damage_hooks"]
    assert checks["contact_speed_damage_authority_false"] and checks["hit_join_speed_authority_false"]
    assert checks["capacity_probe_disabled"] and checks["matching_binary_pair"] and checks["new_hooks_in_3u1"] == 0
    assert len(profiles) == 11 and len(selectable) == 9 and len(pilot) == 2
    assert checks["world_runtime_pass"] and checks["reference_actor_join_preserved"] and checks["terrain_clamp_live"]
    assert checks["installed_pair"] and checks["protected_files_verified"] == 53
    assert checks["controlled_capacity_refusal_pass"]
    assert checks["baron_registrations_remaining"] == [] and checks["rd_free_record"]
    assert checks["authoritative_energy_records"] == 0 and checks["energy_damage_authority"] is False
    assert checks["exact_contact_speed_authority"] is False and checks["pre_movement_contacts"] == "unavailable"

    index = {
        "packet": "3V",
        "purpose": "Step 3 closure audit inputs; no build, install or gameplay action",
        "active_native": [row(p) for p in sorted(active)],
        "offline_model": [row(p) for p in sorted(model)],
        "evidence": [row(p) for p in evidence],
    }
    save(OUT / "INDEX.json", index)
    save(OUT / "CHECKS.json", checks)
    manifest3v = {
        "packet": "3V",
        "status": "audit prepared",
        "native_version_reviewed": 325,
        "native_code_changes": 0,
        "game_files_written": False,
        "install_required": False,
        "gameplay_test_required": False,
        "damage_replacement": False,
        "step3_scope": "explicit bullet flight and diagnostics only",
        "step4_shadow_adapter_allowed": True,
        "damage_activation_allowed": False,
    }
    save(OUT / "manifest.json", manifest3v)

    documents = ["README.md", "AUDIT.md", "FINDINGS.json", "GATES.md", "SCOPE-MATRIX.md", "START-HERE.html", "manifest.json", "INDEX.json", "CHECKS.json"]
    missing = [name for name in documents if not (OUT / name).is_file()]
    if missing:
        print(json.dumps({"prepared_inputs": True, "pending_documents": missing, "checks": checks}, indent=2))
        return
    if RELEASE.exists():
        shutil.rmtree(RELEASE)
    for name in documents:
        copy(OUT / name, RELEASE / name)
    copy(Path(__file__), RELEASE / "Source/tools/prepare_combat_3v_audit.py")
    print(json.dumps({"release": str(RELEASE), "indexed_native": len(active), "indexed_model": len(model), "indexed_evidence": len(evidence), "checks": checks}, indent=2))

if __name__ == "__main__":
    main()

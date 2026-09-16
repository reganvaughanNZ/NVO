"""Review the pinned native325 close-landscape recheck without loading the game."""
from pathlib import Path
from collections import defaultdict
import hashlib, json, re

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "source/combat/step3u1/captures/recheck-01a7dd5ef0cd/NVOCombatCore.log"
EXPECTED = "01a7dd5ef0cdaba00a97b950b1e02dd366c4d45ef3f9002a546bc2952a5454ea"
OUT = ROOT / "source/combat/step3u1"

def fields(line):
    return dict(re.findall(r"(\w+)=([^\s]+)", line))

def main():
    assert hashlib.sha256(CAPTURE.read_bytes()).hexdigest() == EXPECTED
    lines = CAPTURE.read_text(encoding="utf-8").splitlines()
    rows = defaultdict(list)
    for line in lines:
        rows[line.split(" ", 1)[0]].append((fields(line), line))
    assert lines[0].startswith("NVOCombatCore 0.3.25 | phase=3U1")
    assert sum(line.startswith("STARTUP_BANNER ") for line in lines) == 1
    assert len(rows["FLIGHT_SELECT"]) == 1 and rows["FLIGHT_SELECT"][0][0]["profile"] == "9mm-pistol"
    step = rows["IMPACT_STEP"][0][0]
    terrain = rows["IMPACT_TERRAIN"][0][0]
    callback = rows["IMPACT_CALLBACK"][0][0]
    speed = rows["IMPACT_SPEED"][0][0]
    assert len(rows["IMPACT_STEP"]) == len(rows["IMPACT_TERRAIN"]) == len(rows["IMPACT_CALLBACK"]) == 1
    assert step["target"] == "00000000" and step["target_kind"] == "1" and step["region"] == "-1"
    assert step["valid_mask"] == "31" and step["more_contacts"] == "0"
    assert terrain["target"] == "00000000" and terrain["target_kind"] == "1" and terrain["region"] == "-1"
    assert terrain["valid"] == "1" and terrain["query_ok"] == "1" and terrain["explained_clamp"] == "1"
    assert callback["status"] == "correlated" and callback["target_kind"] == "1" and callback["target"] == "00000000"
    assert speed["available"] == "1" and speed["status"] == "observed_engine_segment"
    summary = rows["SUMMARY"][0][0]
    impact = rows["IMPACT_SUMMARY"][0][0]
    physics = rows["PHYSICS_SUMMARY"][0][0]
    route = rows["PHYSICS_ROUTE_SUMMARY"][0][0]
    admission = rows["FLIGHT_ADMISSION_SUMMARY"][0][0]
    assert summary["create"] == summary["impact"] == summary["destroy"] == "1"
    assert summary["unmatched"] == summary["read_failures"] == summary["open_lifetimes"] == "0"
    assert impact["collision_samples"] == impact["impact_callbacks"] == impact["correlated_callbacks"] == "1"
    assert impact["unpaired_callbacks"] == impact["optional_read_failures"] == "0"
    assert physics["accepted"] == "1" and physics["rejected"] == physics["overflow"] == physics["open"] == "0"
    assert route["mismatches"] == route["accounting_unpaired"] == "0"
    assert admission["failed"] == admission["slots_held"] == admission["process_fault"] == "0"
    assert sum(line.startswith("PHYSICS_POOL_RESET ") and "slots_held=0" in line for line in lines) == 2
    assert sum(line.startswith("LIFECYCLE_POOL_RESET ") and "slots_held=0" in line for line in lines) == 1
    assert any(line == "LIFECYCLE exit_game" for line in lines)
    assert all("damage_replacement=1" not in line for line in lines)
    result = {
        "packet": "3U1",
        "native_version": 325,
        "capture_sha256": EXPECTED,
        "verdict": "pass",
        "startup_banners": 1,
        "shots": 1,
        "profile": "9mm-pistol",
        "world_contact": {"target": step["target"], "target_kind": 1, "region": -1, "valid_mask": 31},
        "callback_correlated": True,
        "speed_available": True,
        "speed_status": speed["status"],
        "terrain_clamp_explained": True,
        "movement_mismatches": 0,
        "accounting_unpaired": 0,
        "open_lifetimes": 0,
        "pool_resets_zero": True,
        "damage_replacement": False,
        "game_loaded_by_reviewer": False,
    }
    (OUT / "RECHECK-RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    review = f"""# Packet 3U1 close-landscape recheck — PASS

The single standard9mm round produced the missing live evidence. Its completed collision had a successfully read null target represented as `target=00000000`, `target_kind=1`, region `-1`, valid mask31 and one contact. The callback retained the same World classification and correlated with no target-ID substitution.

This contact also exercised the previously observed terrain branch: the pre-clamp candidate, floor, target kind, region, flags and contact matched, so `explained_clamp=1`. The observed engine-segment speed remained available. Creation, impact and destruction each occurred once; there were no read failures, unmatched events, movement mismatches, unpaired accounting, admission failures, open lifetimes or held pool slots. Damage replacement remained off.

Combined with the preceding live run's nonzero environment references, actor pairing and wall reference, Packet3U1 now accepts both World and Reference classification without weakening actor identity checks. This closes the 3U1 runtime checkpoint only; it does not close the broader Ultra317 damage-authority hold.

Pinned log SHA-256: `{EXPECTED}`.
"""
    (OUT / "RECHECK-REVIEW.md").write_text(review, encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

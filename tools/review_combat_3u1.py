"""Review the pinned native325/3U1 live checkpoint without loading the game."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, re

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "source/combat/step3u1/captures/review-7337bf485a5c/NVOCombatCore.log"
EXPECTED = "7337bf485a5cb219ec4cd4e2bfc37121a0936e3c5bd5091dba801b3ca3de65a2"
OUT = ROOT / "source/combat/step3u1"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fields(line):
    return dict(re.findall(r"(\w+)=([^\s]+)", line))

def integer(row, name):
    return int(row[name], 0)

def main():
    assert sha(CAPTURE) == EXPECTED
    lines = CAPTURE.read_text(encoding="utf-8").splitlines()
    rows = defaultdict(list)
    for line in lines:
        rows[line.split(" ", 1)[0]].append((fields(line), line))

    assert lines[0].startswith("NVOCombatCore 0.3.25 | phase=3U1")
    assert sum(line.startswith("STARTUP_BANNER ") for line in lines) == 1
    selections = [r for r, _ in rows["FLIGHT_SELECT"]]
    collision = [r for r, _ in rows["IMPACT_STEP"]]
    callbacks = [r for r, _ in rows["IMPACT_CALLBACK"]]
    hit_join = [r for r, _ in rows["IMPACT_HIT"]]
    hit_speed = [r for r, _ in rows["IMPACT_HIT_SPEED"]]
    summaries = [r for r, _ in rows["SUMMARY"]]
    physics = [r for r, _ in rows["PHYSICS_SUMMARY"]]
    route = [r for r, _ in rows["PHYSICS_ROUTE_SUMMARY"]]
    admission = [r for r, _ in rows["FLIGHT_ADMISSION_SUMMARY"]]
    impacts = [r for r, _ in rows["IMPACT_SUMMARY"]]
    speed_summaries = [r for r, _ in rows["IMPACT_SPEED_SUMMARY"]]
    terrain_summaries = [r for r, _ in rows["PHYSICS_TERRAIN_SUMMARY"]]

    assert len(selections) == 5 and all(r["profile"] == "9mm-pistol" for r in selections)
    assert [integer(r, "lifetime") for r in collision] == [3, 4, 5]
    kinds = Counter(integer(r, "target_kind") for r in collision)
    assert kinds == Counter({2: 3})
    assert all(int(r["target"], 16) != 0 for r in collision)
    assert [integer(r, "region") for r in collision] == [-1, 0, -1]
    assert len(callbacks) == 3 and all(r["status"] == "correlated" and integer(r, "target_kind") == 2 for r in callbacks)
    assert len(hit_join) == 1 and hit_join[0]["status"] == "paired_model_unavailable"
    assert integer(hit_join[0], "contact_kind") == 2 and hit_join[0]["contact_valid"] == "1"
    assert len(hit_speed) == 1 and hit_speed[0]["available"] == "1" and hit_speed[0]["status"] == "owned_step_speed_range"

    timing = [r for r, _ in rows["FLIGHT_TIMING_SHOT"] if r.get("reason") == "destroy"]
    no_contact = [r for r in timing if r["lifetime"] in {"1", "2"}]
    assert len(no_contact) == 2 and all(r["collision"] == "0" and r["impact_callbacks"] == "0" for r in no_contact)
    travel = [r for r, line in rows["FLIGHT_TRAVEL"] if r.get("phase") == "destroy" and r.get("lifetime") in {"1", "2"}]
    assert len(travel) == 2 and all(float(r["life_delta_s"]) > 3.0 for r in travel)

    assert len(summaries) == 2 and all(r["open_lifetimes"] == "0" and r["unmatched"] == "0" and r["read_failures"] == "0" for r in summaries)
    assert len(physics) == 2 and sum(integer(r, "accepted") for r in physics) == 5
    assert sum(integer(r, "applied_steps") for r in physics) == 371
    assert all(r["rejected"] == "0" and r["overflow"] == "0" and r["open"] == "0" and r["damage_replacement"] == "0" for r in physics)
    assert len(route) == 2 and sum(integer(r, "mismatches") for r in route) == 0
    assert sum(integer(r, "accounting_unpaired") for r in route) == 0
    assert len(admission) == 2 and all(r["failed"] == "0" and r["slots_held"] == "0" and r["process_fault"] == "0" for r in admission)
    assert len(impacts) == 2 and sum(integer(r, "collision_samples") for r in impacts) == 3
    assert sum(integer(r, "correlated_callbacks") for r in impacts) == 3
    assert sum(integer(r, "unpaired_callbacks") for r in impacts) == 0
    assert len(speed_summaries) == 2 and sum(integer(r, "available_segment_ranges") for r in speed_summaries) == 3
    assert len(terrain_summaries) == 2 and sum(integer(r, "corrected") for r in terrain_summaries) == 0
    assert sum(line.startswith("PHYSICS_POOL_RESET ") and "slots_held=0" in line for line in lines) == 4
    assert sum(line.startswith("LIFECYCLE_POOL_RESET ") and "slots_held=0" in line for line in lines) == 2
    assert any(line == "LIFECYCLE exit_game" for line in lines)
    assert all("damage_replacement=1" not in line for line in lines)

    result = {
        "packet": "3U1",
        "native_version": 325,
        "capture_sha256": EXPECTED,
        "verdict": "partial_pass_null_world_not_observed",
        "startup_banners": 1,
        "sessions": 2,
        "reload_observed": True,
        "shots_selected": 5,
        "profiles": dict(Counter(r["profile"] for r in selections)),
        "collisions": 3,
        "contact_kind_counts": {"invalid_0": kinds[0], "world_1": kinds[1], "reference_2": kinds[2]},
        "collision_lifetimes": [integer(r, "lifetime") for r in collision],
        "collision_regions": [integer(r, "region") for r in collision],
        "distant_no_contact_lifetimes": [integer(r, "lifetime") for r in no_contact],
        "distant_no_contact_life_s": [float(r["life_delta_s"]) for r in travel],
        "actor_reference_join_preserved": True,
        "actor_join_speed_available": True,
        "correlated_callbacks": 3,
        "unpaired_callbacks": 0,
        "available_speed_ranges": 3,
        "applied_steps": 371,
        "movement_mismatches": 0,
        "accounting_unpaired": 0,
        "open_lifetimes": 0,
        "pool_resets_zero": True,
        "terrain_clamps_observed": 0,
        "damage_replacement": False,
        "game_loaded_by_reviewer": False,
        "repeat_needed": "one close standard-9mm shot directly into bare landscape ground, then quit normally",
    }
    (OUT / "RUNTIME-RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    review = f"""# Packet 3U1 live review — PARTIAL PASS

The native325 run is stable and preserves actor/reference identity, but it does not yet exercise a null world contact. The two intended distant ground rounds (lifetimes 1 and 2) recorded no collision and retired after {travel[0]['life_delta_s']}s and {travel[1]['life_delta_s']}s. All three actual contacts were readable nonzero references (`target_kind=2`): one environment reference, one region-0 actor, and the post-reload wall/reference.

The actor contact paired with the same nonzero target and Reference kind. Its bounded owned-step speed range remained available. All three callbacks correlated; there were no unpaired callbacks. Across two sessions and one reload: five admissions, 371 applied steps, zero movement mismatches, zero unpaired accounting, zero admission failures/process faults, zero open lifetimes, and zero held pool slots. Damage replacement remained off. No terrain clamp occurred.

Verdict: **partial pass**. Reference preservation and runtime stability pass. `target_kind=1` remains untested because no collision in this run had a null target pointer. One close shot directly into bare landscape ground is the smallest useful recheck; no actor, reload, VATS, stress test, or video is needed.

Pinned log SHA-256: `{EXPECTED}`.
"""
    (OUT / "RUNTIME-REVIEW.md").write_text(review, encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

"""Validate NVO's source-credit ledger against the external reference folder."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "reference" / "source-credit-ledger.json"
INVENTORY_PATH = ROOT / "reference" / "source-folder-inventory.json"
VALID_STATUSES = {"adapted", "contract", "dependency", "research", "planned"}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def main() -> int:
    ledger = load_json(LEDGER_PATH)
    inventory = load_json(INVENTORY_PATH)
    errors: list[str] = []

    projects = [item["project"] for item in ledger["sources"]]
    duplicate_projects = sorted(name for name, count in Counter(projects).items() if count > 1)
    if duplicate_projects:
        errors.append("duplicate ledger projects: " + ", ".join(duplicate_projects))

    ledger_projects = set(projects)
    for item in ledger["sources"]:
        if item.get("status") not in VALID_STATUSES:
            errors.append(f"invalid ledger status for {item['project']}: {item.get('status')}")
        for evidence in item.get("evidence", []):
            if not (ROOT / evidence).exists():
                errors.append(f"missing evidence for {item['project']}: {evidence}")

    reference_root = Path(inventory["reference_root"])
    expected_names = {item["name"] for item in inventory["items"]}
    actual_names = {item.name for item in reference_root.iterdir()} if reference_root.is_dir() else set()
    for missing in sorted(expected_names - actual_names):
        errors.append(f"inventory item no longer present: {missing}")
    for untracked in sorted(actual_names - expected_names):
        errors.append(f"untracked reference-folder item: {untracked}")

    for item in inventory["items"]:
        mapped = item.get("ledger_project")
        if mapped and mapped not in ledger_projects:
            errors.append(f"inventory mapping has no ledger entry: {item['name']} -> {mapped}")

    print(f"ledger projects: {len(projects)}")
    print(f"reference-folder items: {len(expected_names)}")
    print("ledger statuses: " + ", ".join(f"{key}={value}" for key, value in sorted(Counter(item['status'] for item in ledger['sources']).items())))
    print("inventory statuses: " + ", ".join(f"{key}={value}" for key, value in sorted(Counter(item['status'] for item in inventory['items']).items())))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("credit audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

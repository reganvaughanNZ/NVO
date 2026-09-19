"""Verify the proposed 4J1 deployment against retained and current files; no install."""
import json
from datetime import datetime, timezone
from pathlib import Path

from prepare_combat_4g import ROOT, sha, record, write

GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
STEP = ROOT / 'source/combat/step4j1'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4J1-Flame-Lifecycle'


def child(root, relative):
    path = (root / relative).resolve()
    if root.resolve() not in path.parents:
        raise RuntimeError(f'Path escaped root: {relative}')
    return path


def main():
    if (STEP / 'INSTALL-result.json').exists():
        raise RuntimeError('Installation already recorded')
    previous = json.loads((ROOT / 'source/combat/step4j/INSTALL-result.json').read_text(encoding='utf-8-sig'))
    if previous['status'] != 'installed' or previous['native_version'] != 330:
        raise RuntimeError('Expected installed native330 receipt')
    old = {row['path']: row['sha256'] for row in previous['installed']}
    manifest = json.loads((RELEASE / 'MANIFEST.json').read_text())
    if manifest['packet'] != '4J1':
        raise RuntimeError('Wrong release manifest')
    for row in manifest['files']:
        path = child(RELEASE, row['path'])
        if sha(path) != row['sha256'] or path.stat().st_size != row['bytes']:
            raise RuntimeError(f'Package mismatch: {path}')
    verify = json.loads((STEP / 'Evidence/VERIFICATION.json').read_text())
    if verify['native_version'] != 331 or verify['installed'] or verify['damage_replacement']:
        raise RuntimeError('Expected prepared diagnostic native331')
    for row in verify['source_inputs']:
        if sha(child(ROOT, row['path'])) != row['sha256']:
            raise RuntimeError(f'Source changed since preparation: {row["path"]}')
    proposed = json.loads((RELEASE / 'PROPOSED-FILES.json').read_text())['files']
    expected = {'Data/NVSE/Plugins/NVOCombatCore.dll', 'Data/NVSE/Plugins/NVOCombatCore.pdb'}
    if len(proposed) != 2 or {r['path'] for r in proposed} != expected:
        raise RuntimeError('Expected only the DLL/PDB pair')
    files = []
    for row in proposed:
        path = row['path']
        if sha(child(GAME, path)) != old[path]:
            raise RuntimeError(f'Installed baseline changed: {path}')
        files.append(dict(path=path, source=str(child(RELEASE, path)),
                          sha256=row['sha256'], previous_sha256=old[path]))
    prior_plan = json.loads((ROOT / 'source/combat/step4j/Evidence/INSTALL-plan.json').read_text())
    protected = dict(prior_plan['protected'])
    protected['NVOComponentKit4J.txt'] = old['NVOComponentKit4J.txt']
    for path, digest in protected.items():
        if sha(child(GAME, path)) != digest:
            raise RuntimeError(f'Protected baseline changed: {path}')
    if (GAME / 'Data/RD.esm').exists():
        raise RuntimeError('RD.esm unexpectedly present')
    plan = dict(packet='4J1', native_version=331, prepared_only=True, game_root=str(GAME),
                protected=protected, files=files, generated_utc=datetime.now(timezone.utc).isoformat(),
                prior_installation_receipt='source/combat/step4j/INSTALL-result.json',
                release_manifest=record(RELEASE / 'MANIFEST.json', ROOT),
                authorization='User explicitly replied "Yes you may install" after being asked to '
                'install Packet 4J1/native0.3.31, replace only NVOCombatCore.dll and its matching PDB '
                'with a verified backup, and close New Vegas if necessary. This resolves the prior '
                'automatic approval rejection. No new feature or damage authority authorized here.')
    write(STEP / 'Evidence/INSTALL-plan.json', plan)
    print(json.dumps(dict(status='PLAN_VERIFIED_NOT_INSTALLED', files=len(files),
                          protected=len(protected), manifest_files=len(manifest['files']),
                          source_inputs=len(verify['source_inputs']), game_files_modified=False)))


if __name__ == '__main__':
    main()

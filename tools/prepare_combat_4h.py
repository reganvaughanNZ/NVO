"""Fresh offline Packet 4H checks/package. No game paths, DLL build or deployment."""
import hashlib
import json
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from prepare_combat_4g import ROOT, MODEL, sha, record, write, copy

STEP = ROOT / 'source/combat/step4h'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4H-Impact-Evidence'
CHANGED = {'MaterialPreview.hpp', 'MaterialPreview.cpp',
           'material_preview_tests.cpp', 'run_material_checks.cmd'}
NEW = ['ImpactBinding.hpp', 'ImpactBinding.cpp', 'impact_binding_tests.cpp', 'run_binding_checks.cmd']
DOCS = ['README.md', 'INPUT-AUDIT.md', 'BINDING-CONTRACT.md', 'REVIEW.md', 'START-HERE.html']


def main():
    prior = json.loads((ROOT / 'source/combat/step4g/Evidence/VERIFICATION.json').read_text())
    pinned = json.loads((ROOT / 'source/combat/step4g/Evidence/UNCHANGED-NATIVE.json').read_text())
    unchanged, changed = {}, []
    for row in pinned['files'] + prior['source_inputs']:
        path = ROOT / row['path']
        if path.parent == MODEL and path.name in CHANGED:
            changed.append(dict(before_sha256=row['sha256'], after=record(path, ROOT)))
            continue
        if sha(path) != row['sha256']:
            raise RuntimeError(f'Unexpected baseline change: {row["path"]}')
        unchanged[row['path']] = record(path, ROOT)
    if len(changed) != len(CHANGED):
        raise RuntimeError('Intentional change list differs from expected four 4G inputs')
    for name in ('CMakeLists.txt', 'BUILD.cmd'):
        content = (ROOT / 'native/NVOCombatCore' / name).read_text()
        if any(module in content for module in ('ImpactBinding', 'MaterialPreview',
                                                'ArmourModel.cpp', 'ShadowAdapter', 'ResponseDefinitions')):
            raise RuntimeError('Offline module unexpectedly included in DLL build')
    sources = [ROOT / row['path'] for row in prior['source_inputs']] + [MODEL / name for name in NEW]
    before = [record(path, ROOT) for path in sources]
    docs_before = [record(STEP / name, ROOT) for name in DOCS]
    for runner in ('run_binding_checks.cmd', 'run_material_checks.cmd'):
        run = subprocess.run(['cmd.exe', '/d', '/c', runner], cwd=MODEL, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(run.stdout + run.stderr + '\nInspect out-binding / out-material logs.')
    if before != [record(path, ROOT) for path in sources]:
        raise RuntimeError('Source changed during checks')
    suites, evidence, executables = {}, [], []
    for suite in ('binding', 'material', 'model', 'shadow', 'response'):
        out = MODEL / ('out-binding' if suite == 'binding' else 'out-material')
        result = (out / f'{suite}-results.txt').read_text()
        pattern = r'^PASS material preview checks: (\d+)' if suite == 'material' else (
            r'^PASS (\d+) checks;' if suite == 'response' else r'^RESULT checks=(\d+) failures=0')
        match = re.search(pattern, result, re.M)
        if not match or re.search(r'\bFAIL\b', result):
            raise RuntimeError(f'Unrecognised or failed result: {suite}')
        build = out / f'{suite}-build.log'
        if re.search(r'\b(?:warning|error) [A-Z]+\d+', build.read_text(), re.I):
            raise RuntimeError(f'Compiler diagnostic: {suite}')
        suites[suite] = dict(checks=int(match[1]), result=result.strip())
        executables.append(record(out / f'{suite}_checks.exe', ROOT))
        for label, src in (('CHECKS', out / f'{suite}-results.txt'), ('BUILD', build)):
            dst = STEP / 'Evidence' / f'{suite.upper()}-{label}.txt'
            copy(src, dst)
            evidence.append(dst)
    for name in ('binding', 'material'):
        dst = STEP / 'Evidence' / f'{name.upper()}-TOOLCHAIN.txt'
        copy(MODEL / f'out-{name}/toolchain.log', dst)
        evidence.append(dst)

    # Bundle the audited source as reference evidence so citations work without the checkout.
    audit = (STEP / 'INPUT-AUDIT.md').read_text(encoding='utf-8')
    references = sorted(set(re.findall(r'\.\./\.\./\.\./\.\./(native/[^)#]+)', audit)))
    references.append('source/combat/step3v/AUDIT.md')
    reference_hashes = [record(ROOT / path, ROOT) for path in references]
    verification = dict(
        packet='4H', status='PREPARED_OFFLINE', verified_utc=datetime.now(timezone.utc).isoformat(),
        native_source_version=327, material_contract_version=2, binding_contract_version=1,
        runtime_integrated=False, gameplay_writes=False, dll_built=False,
        installed=False, game_accessed=False, new_runtime_dependencies=[],
        compiler='MSVC x86 /std:c++17 /W4 /WX /permissive-',
        checks_total=sum(row['checks'] for row in suites.values()), suites=suites,
        source_inputs=before, document_inputs=docs_before, audit_references=reference_hashes,
        existing_native_and_offline_files_unchanged=len(unchanged), changed_4g_inputs=changed,
        executable_hashes=executables,
        limitations=[
            'Synthetic exact/at-impact producer assertions only; no current native producer qualifies.',
            'Matching stamps cannot validate three identically stale or falsely relabelled payloads.',
            'Exact contact speed, calibrated units and coherent component-bound impact state remain open.',
            'No production profiles, engine-hook integration, gameplay writes or performance measurement.',
            'Installed game state was not inspected; this is offline preparation, not live acceptance.'
        ])
    write(STEP / 'Evidence/VERIFICATION.json', verification)
    write(STEP / 'Evidence/UNCHANGED-NATIVE.json', dict(files=list(unchanged.values())))
    evidence += [STEP / 'Evidence/VERIFICATION.json', STEP / 'Evidence/UNCHANGED-NATIVE.json']
    files = []
    for name in DOCS:
        dst = RELEASE / name
        copy(STEP / name, dst)
        if name == 'INPUT-AUDIT.md':
            dst.write_text(audit.replace('../../../../native/', 'Reference/native/').replace(
                '../step3v/AUDIT.md', 'Reference/source/combat/step3v/AUDIT.md'), encoding='utf-8')
        files.append(dst)
    for path in sources:
        dst = RELEASE / 'Source' / path.name
        copy(path, dst)
        files.append(dst)
    for row in reference_hashes:
        dst = RELEASE / 'Reference' / row['path']
        copy(ROOT / row['path'], dst)
        if sha(dst) != row['sha256']:
            raise RuntimeError('Audit source changed during packaging')
        files.append(dst)
    for path in evidence:
        dst = RELEASE / 'Evidence' / path.name
        copy(path, dst)
        files.append(dst)
    for name in ('CREDITS.md', 'LICENSE'):
        dst = RELEASE / name
        copy(ROOT / name, dst)
        files.append(dst)
    for name in ('THIRD-PARTY-NOTICES.md', 'LICENSE-GPL-3.0.txt', 'LICENSE-ITR-MIT.txt'):
        dst = RELEASE / 'Notices' / name
        copy(ROOT / 'native/NVOCombatCore' / name, dst)
        files.append(dst)
    for row in before:
        if sha(RELEASE / 'Source' / Path(row['path']).name) != row['sha256']:
            raise RuntimeError('Packaged source differs from checked source')
    for href in re.findall(r'href="([^"]+)"', (RELEASE / 'START-HERE.html').read_text()):
        if not (RELEASE / href).is_file():
            raise RuntimeError(f'Missing review link: {href}')
    for href in re.findall(r'\]\(([^)]+)\)', (RELEASE / 'INPUT-AUDIT.md').read_text()):
        if not (RELEASE / href.split('#')[0]).is_file():
            raise RuntimeError(f'Missing audit reference: {href}')
    if docs_before != [record(STEP / name, ROOT) for name in DOCS]:
        raise RuntimeError('Documents changed during packaging')
    manifest = RELEASE / 'MANIFEST.json'
    write(manifest, dict(packet='4H', status='PREPARED_OFFLINE', files=[record(p, RELEASE) for p in sorted(files)]))
    bundle = RELEASE.with_suffix('.zip')
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files + [manifest]):
            archive.write(path, str(Path(RELEASE.name) / path.relative_to(RELEASE)))
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('ZIP integrity failure')
        for row in json.loads(manifest.read_text())['files']:
            if hashlib.sha256(archive.read(RELEASE.name + '/' + row['path'])).hexdigest() != row['sha256']:
                raise RuntimeError('ZIP hash mismatch')
    write(STEP / 'PACKAGE.json', dict(path=str(bundle), sha256=sha(bundle), bytes=bundle.stat().st_size,
                                     status='PREPARED_OFFLINE'))
    print(json.dumps(dict(packet=str(RELEASE), checks={key: row['checks'] for key, row in suites.items()},
                          total=verification['checks_total'], unchanged_files=len(unchanged), game_accessed=False)))


if __name__ == '__main__':
    main()

"""Compile/check/package Packet 4G offline. No game paths or installation."""
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'native/NVOCombatModel'
STEP = ROOT / 'source/combat/step4g'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4G-Kinetic-Material-Preview'
SOURCES = ['ArmourModel.hpp', 'ArmourModel.cpp', 'ShadowAdapter.hpp', 'ShadowAdapter.cpp',
           'ResponseDefinitions.hpp', 'ResponseDefinitions.cpp', 'MaterialPreview.hpp', 'MaterialPreview.cpp',
           'tests.cpp', 'shadow_adapter_tests.cpp', 'response_definition_tests.cpp',
           'material_preview_tests.cpp', 'run_material_checks.cmd']
REFACTORED = {'NVOCombatModel/' + name for name in
              ('ArmourModel.hpp', 'ArmourModel.cpp', 'ShadowAdapter.hpp', 'ShadowAdapter.cpp')}
DOCS = ['README.md', 'MODEL-RULES.md', 'REVIEW.md', 'START-HERE.html']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path, root):
    return dict(path=path.relative_to(root).as_posix(), bytes=path.stat().st_size, sha256=sha(path))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main():
    baseline = json.loads((ROOT / 'source/combat/step4d/Evidence/SOURCE-SNAPSHOT.json').read_text())
    unchanged, refactored = [], []
    for row in baseline['files']:
        relative = Path(row['path'])
        name = relative.as_posix()
        path = ROOT / 'native' / relative
        if name == 'NVOCombatModel/README.md':
            continue
        if name in REFACTORED:
            refactored.append(dict(before_sha256=row['sha256'], after=record(path, ROOT)))
        else:
            if sha(path) != row['sha256']:
                raise RuntimeError(f'Unexpected existing native change: {name}')
            unchanged.append(record(path, ROOT))
    previous = json.loads((ROOT / 'source/combat/step4f/Evidence/VERIFICATION.json').read_text())
    for row in previous['source_inputs']:
        path = ROOT / row['path']
        if sha(path) != row['sha256']:
            raise RuntimeError(f'4F input unexpectedly changed: {path}')
        unchanged.append(record(path, ROOT))
    for name in ('CMakeLists.txt', 'BUILD.cmd'):
        path = ROOT / 'native/NVOCombatCore' / name
        if any(module in path.read_text() for module in ('MaterialPreview', 'ArmourModel.cpp', 'ShadowAdapter', 'ResponseDefinitions')):
            raise RuntimeError('Offline module unexpectedly included in DLL build')
    source_before = [record(MODEL / name, ROOT) for name in SOURCES]
    check = subprocess.run(['cmd.exe', '/d', '/c', 'run_material_checks.cmd'], cwd=MODEL,
                           capture_output=True, text=True)
    if check.returncode:
        raise RuntimeError(check.stdout + check.stderr + '\nInspect native/NVOCombatModel/out-material logs.')
    if source_before != [record(MODEL / name, ROOT) for name in SOURCES]:
        raise RuntimeError('Sources changed during checking')
    results = {}
    evidence = []
    for suite in ('material', 'model', 'shadow', 'response'):
        output = (MODEL / f'out-material/{suite}-results.txt').read_text()
        pattern = r'^PASS material preview checks: (\d+)' if suite == 'material' else (
            r'^PASS (\d+) checks;' if suite == 'response' else r'^RESULT checks=(\d+) failures=0')
        match = re.search(pattern, output, re.M)
        if not match or re.search(r'\bFAIL\b', output):
            raise RuntimeError(f'Unrecognised/failed result: {suite}')
        build = MODEL / f'out-material/{suite}-build.log'
        if re.search(r'\b(?:warning|error) [A-Z]+\d+', build.read_text(), re.I):
            raise RuntimeError(f'Compiler diagnostic: {suite}')
        results[suite] = dict(checks=int(match[1]), result=output.strip())
        for label, src in (('CHECKS', MODEL / f'out-material/{suite}-results.txt'), ('BUILD', build)):
            dst = STEP / 'Evidence' / f'{suite.upper()}-{label}.txt'
            copy(src, dst); evidence.append(dst)
    copy(MODEL / 'out-material/toolchain.log', STEP / 'Evidence/TOOLCHAIN.txt')
    evidence.append(STEP / 'Evidence/TOOLCHAIN.txt')
    verification = dict(
        packet='4G', status='PREPARED_OFFLINE', verified_utc=datetime.now(timezone.utc).isoformat(),
        native_source_version=327, gameplay_writes=False, runtime_integrated=False,
        dll_built=False, installed=False, game_accessed=False, new_runtime_dependencies=[],
        compiler='MSVC x86 /std:c++17 /W4 /WX /permissive-',
        checks_total=sum(row['checks'] for row in results.values()), suites=results,
        source_inputs=source_before, existing_native_files_unchanged=len(unchanged),
        refactored_offline_sources=refactored,
        executable_hashes=[record(MODEL / f'out-material/{name}_checks.exe', ROOT)
                           for name in ('material', 'model', 'shadow', 'response')],
        limitations=[
            'Synthetic numeric profiles/evidence only; no production armour or creature mappings.',
            'Scalar stopping and direct-to-target transmission surrogate, not calibrated material physics.',
            'Other ten families explicitly unsupported by the new numerical bridge.',
            'No live impact-speed/snapshot authority, engine writes, or stress performance measured.',
            'Installed game files were not inspected or changed; source evidence is not live acceptance.'
        ])
    write(STEP / 'Evidence/VERIFICATION.json', verification)
    write(STEP / 'Evidence/UNCHANGED-NATIVE.json', dict(files=unchanged))
    evidence += [STEP / 'Evidence/VERIFICATION.json', STEP / 'Evidence/UNCHANGED-NATIVE.json']
    files = []
    for name in DOCS:
        dst = RELEASE / name; copy(STEP / name, dst); files.append(dst)
    for name in SOURCES:
        dst = RELEASE / 'Source' / name; copy(MODEL / name, dst); files.append(dst)
    for path in evidence:
        dst = RELEASE / 'Evidence' / path.name; copy(path, dst); files.append(dst)
    for name in ('CREDITS.md', 'LICENSE'):
        dst = RELEASE / name; copy(ROOT / name, dst); files.append(dst)
    for name in ('THIRD-PARTY-NOTICES.md', 'LICENSE-GPL-3.0.txt', 'LICENSE-ITR-MIT.txt'):
        dst = RELEASE / 'Notices' / name; copy(ROOT / 'native/NVOCombatCore' / name, dst); files.append(dst)
    for href in re.findall(r'href="([^"]+)"', (RELEASE / 'START-HERE.html').read_text()):
        if not (RELEASE / href).is_file():
            raise RuntimeError(f'Missing review page link: {href}')
    for row in source_before:
        if sha(RELEASE / 'Source' / Path(row['path']).name) != row['sha256']:
            raise RuntimeError('Packaged source differs from checked source')
    manifest = RELEASE / 'MANIFEST.json'
    write(manifest, dict(packet='4G', status='PREPARED_OFFLINE', files=[record(p, RELEASE) for p in sorted(files)]))
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
    print(json.dumps(dict(packet=str(RELEASE), checks={k: v['checks'] for k, v in results.items()},
                          total=verification['checks_total'], unchanged_native=len(unchanged), game_accessed=False)))


if __name__ == '__main__':
    main()

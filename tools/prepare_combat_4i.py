"""Package a checked 4I native build without game access or deployment."""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from prepare_combat_4g import ROOT, MODEL, sha, record, write, copy
from package_combat_3b2 import inspect_pair

CORE = ROOT / 'native/NVOCombatCore'
STEP = ROOT / 'source/combat/step4i'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4I-Native-Copy-Capture'
ALLOWED = {'README.md', 'CMakeLists.txt', 'include/HitTransaction.hpp', 'include/NativeObserver.hpp',
           'include/ArmourSnapshot.hpp', 'include/FlightPhysics.hpp', 'src/CurrentHit.cpp',
           'src/HitTransaction.cpp', 'src/NativeObserver.cpp', 'src/ArmourSnapshot.cpp',
           'src/FlightImpactJoin.inl', 'src/Plugin.cpp'}
CHECKS = [('copy-capture', 'RUN-COPY-CAPTURE-CHECKS.cmd', 'CopyCaptureTests.exe'),
          ('hit-scope', 'RUN-HIT-SCOPE-CHECKS.cmd', 'HitTransactionScopeTests.exe'),
          ('armour', 'RUN-ARMOUR-SNAPSHOT-CHECKS.cmd', 'ArmourSnapshotReaderTests.exe')]


def naked_functions(text):
    result = []
    for match in re.finditer(r'__declspec\(naked\) void \w+\(\)\s*\{', text):
        pos = match.end(); depth = 1
        while depth and pos < len(text):
            depth += (text[pos] == '{') - (text[pos] == '}'); pos += 1
        if depth:
            raise RuntimeError('Unterminated wrapper during static comparison')
        result.append(text[match.start():pos])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', required=True, help='Existing checked directory name under native/NVOCombatCore/out')
    parser.add_argument('--run-checks', action='store_true', help='Rerun standalone fixtures before packaging')
    args = parser.parse_args()
    build = (CORE / 'out' / args.build).resolve()
    if build.parent != (CORE / 'out').resolve():
        raise RuntimeError('Build must be directly inside the workspace native output directory')
    baseline = json.loads((ROOT / 'source/combat/step4h/Evidence/UNCHANGED-NATIVE.json').read_text())['files']
    baseline += json.loads((ROOT / 'source/combat/step4h/Evidence/VERIFICATION.json').read_text())['source_inputs']
    baseline = {row['path']: row for row in baseline}
    unchanged, changed = [], []
    for relative, row in baseline.items():
        path = ROOT / relative
        now = record(path, ROOT)
        if sha(path) == row['sha256']:
            unchanged.append(now)
        elif relative.startswith('native/NVOCombatCore/') and path.relative_to(CORE).as_posix() in ALLOWED:
            changed.append(dict(before_sha256=row['sha256'], after=now))
        else:
            raise RuntimeError(f'Unexpected native/model change: {relative}')
    if len(changed) != len(ALLOWED):
        raise RuntimeError('Unexpected changed-file set')
    for name in ('CMakeLists.txt', 'BUILD.cmd'):
        data = (CORE / name).read_text()
        if any(module in data for module in ('MaterialPreview', 'ArmourModel.cpp', 'ImpactBinding', 'ShadowAdapter', 'ResponseDefinitions')):
            raise RuntimeError('Offline damage model unexpectedly linked')
    old = ROOT / 'release/NVO-Combat-Packet-4D-Armour-Identity/Source/NVOCombatCore'
    wrappers = []
    for name in ('src/CurrentHit.cpp', 'src/HitTransaction.cpp'):
        if naked_functions((old / name).read_text()) != naked_functions((CORE / name).read_text()):
            raise RuntimeError(f'Hook wrapper changed: {name}')
        wrappers.append(name)
    # Existing native readers/movement/hook guards are pinned by the baseline above.
    sources = [CORE / name for name in ('BUILD.cmd', 'CMakeLists.txt', 'README.md',
        'THIRD-PARTY-NOTICES.md', 'LICENSE-GPL-3.0.txt', 'LICENSE-ITR-MIT.txt', 'CREDITS-BALLISTX.md')]
    for folder in ('include', 'src', 'tests', 'config'):
        sources += sorted(p for p in (CORE / folder).glob('*') if p.is_file()
                          and p.suffix.lower() in ('.hpp', '.h', '.cpp', '.inl', '.cmd', '.def', '.ini', '.tsv'))
    sources += [MODEL / 'CoverageProfiles.hpp', MODEL / 'CoverageProfiles.cpp']
    inputs = [record(path, ROOT) for path in sources]
    runtime_inputs = [p for p in sources if (p.parent.name in ('include', 'src')
                      and p.suffix != '.def') or p.parent == MODEL or p.name in ('BUILD.cmd', 'CMakeLists.txt')]
    if any(p.stat().st_mtime_ns > (build / 'NVOCombatCore.dll').stat().st_mtime_ns for p in runtime_inputs):
        raise RuntimeError('Runtime source newer than DLL; rebuild before packaging')
    if args.run_checks:
        for _, runner, _ in CHECKS:
            run = subprocess.run(['cmd.exe', '/d', '/c', runner], cwd=CORE / 'tests', capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(run.stdout + run.stderr)
    results, evidence = {}, []
    for name, runner, exe in CHECKS:
        path = CORE / f'tests/out/{name}-results.txt'
        text = path.read_text()
        pattern = r'^PASS (\d+) checks;' if name == 'armour' else r'^RESULT checks=(\d+) failures=0'
        match = re.search(pattern, text, re.M)
        if not match or re.search(r'\bFAIL\b', text):
            raise RuntimeError(f'Missing or failed suite: {name}')
        buildlog = CORE / f'tests/out/{name}-build.log'
        if re.search(r'\b(?:warning|error) [A-Z]+\d+', buildlog.read_text(), re.I):
            raise RuntimeError(f'Compiler diagnostic: {name}')
        results[name] = dict(checks=int(match[1]), result=text.strip(),
            results_utc=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            executable=record(CORE / 'tests/out' / exe, ROOT), runner=runner)
        for suffix in ('results.txt', 'build.log', 'toolchain.log'):
            dst = STEP / 'Evidence' / f'{name}-{suffix}'
            copy(CORE / 'tests/out' / f'{name}-{suffix}', dst); evidence.append(dst)
    binary = inspect_pair(build, b'NVOCombatCore 0.3.28 | phase=4I')
    imports = re.findall(r'^\s{4}([^\s]+\.dll)\s*$', (build / 'dll-details.txt').read_text(), re.I | re.M)
    if [value.lower() for value in imports] != ['kernel32.dll']:
        raise RuntimeError(f'Unexpected imports: {imports}')
    binary['imports'] = imports
    for name in ('build.log', 'dll-details.txt', 'toolchain.log'):
        dst = STEP / 'Evidence' / name
        copy(build / name, dst); evidence.append(dst)
    verification = dict(packet='4I', status='COMPILED_NOT_INSTALLED',
        verified_utc=datetime.now(timezone.utc).isoformat(), native_version=328,
        last_accepted_live_version=327, binary=binary, checks_total=sum(x['checks'] for x in results.values()),
        suites=results, source_inputs=inputs, unchanged_files=len(unchanged), changed_baseline_files=changed,
        unchanged_wrapper_assembly=wrappers, model_inputs_unchanged=True, model_tests_rerun=False,
        new_engine_hooks=0, new_runtime_dependencies=[], model_linked=False,
        damage_replacement=False, stagger_writes=False, at_impact_authority=False,
        component_verified=False, application_verified=False, installed=False,
        game_accessed=False, game_launched=False, live_acceptance=False,
        limitations=['Copy association only; not exact contact, atomic impact state or committed application.',
                     'Fixture memory/stubs exercise production scope and armour paths, not running engine hooks.',
                     'Existing diagnostic budgets unchanged; omissions do not supply gameplay evidence.',
                     'Installed files were not inspected; prepare a fresh backup/installation receipt before deployment.'])
    write(STEP / 'Evidence/VERIFICATION.json', verification)
    write(STEP / 'Evidence/UNCHANGED-NATIVE.json', dict(files=unchanged))
    evidence += [STEP / 'Evidence/VERIFICATION.json', STEP / 'Evidence/UNCHANGED-NATIVE.json']
    files = []
    for name in ('README.md', 'REVIEW.md', 'START-HERE.html'):
        dst = RELEASE / name; copy(STEP / name, dst); files.append(dst)
    for path in sources:
        dst = RELEASE / 'Source' / path.relative_to(ROOT / 'native')
        copy(path, dst); files.append(dst)
    for path in evidence:
        dst = RELEASE / 'Evidence' / path.name; copy(path, dst); files.append(dst)
    proposed = []
    for name in ('NVOCombatCore.dll', 'NVOCombatCore.pdb'):
        dst = RELEASE / 'Data/NVSE/Plugins' / name
        copy(build / name, dst); files.append(dst)
        proposed.append(record(dst, RELEASE))
    for name in ('CREDITS.md', 'LICENSE'):
        dst = RELEASE / name; copy(ROOT / name, dst); files.append(dst)
    install = RELEASE / 'PROPOSED-FILES.json'
    write(install, dict(prepared_only=True, installed=False, files=proposed,
        note='Only this DLL/PDB pair is proposed. Fresh installed-state validation and backup required; no installer included.'))
    files.append(install)
    for href in re.findall(r'href="([^"]+)"', (RELEASE / 'START-HERE.html').read_text()):
        if not (RELEASE / href).is_file(): raise RuntimeError(f'Missing review link: {href}')
    if inputs != [record(path, ROOT) for path in sources]:
        raise RuntimeError('Sources changed during packaging')
    for row in inputs:
        if sha(RELEASE / 'Source' / Path(row['path']).relative_to('native')) != row['sha256']:
            raise RuntimeError('Packaged source mismatch')
    manifest = RELEASE / 'MANIFEST.json'
    write(manifest, dict(packet='4I', status='COMPILED_NOT_INSTALLED', files=[record(p, RELEASE) for p in sorted(files)]))
    bundle = RELEASE.with_suffix('.zip')
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files + [manifest]): archive.write(path, str(Path(RELEASE.name) / path.relative_to(RELEASE)))
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None: raise RuntimeError('ZIP integrity failure')
        for row in json.loads(manifest.read_text())['files']:
            if hashlib.sha256(archive.read(RELEASE.name + '/' + row['path'])).hexdigest() != row['sha256']:
                raise RuntimeError('ZIP hash mismatch')
    write(STEP / 'PACKAGE.json', dict(path=str(bundle), sha256=sha(bundle), bytes=bundle.stat().st_size,
                                     status='COMPILED_NOT_INSTALLED'))
    print(json.dumps(dict(packet=str(RELEASE), checks={k: v['checks'] for k, v in results.items()},
                          total=verification['checks_total'], unchanged_files=len(unchanged), installed=False)))


if __name__ == '__main__': main()

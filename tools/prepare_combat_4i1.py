"""Package checked 4I1 callbacks, without game access, deployment or DLL loading."""
import argparse
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from prepare_combat_4g import ROOT, MODEL, sha, record, write, copy
from prepare_combat_4i import naked_functions
from package_combat_3b2 import inspect_pair

CORE = ROOT / 'native/NVOCombatCore'
STEP = ROOT / 'source/combat/step4i1'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4I1-Callback-Survival'
ALLOWED = {'README.md', 'CMakeLists.txt', 'include/NativeObserver.hpp', 'include/DamageEvents.hpp',
           'src/DamageEvents.cpp', 'src/HitTransaction.cpp', 'src/Plugin.cpp', 'tests/HitTransactionScopeTests.cpp'}
CHECKS = [('damage-event', 'RUN-DAMAGE-EVENT-CHECKS.cmd', 'DamageEventLifecycleTests.exe'),
          ('hit-scope', 'RUN-HIT-SCOPE-CHECKS.cmd', 'HitTransactionScopeTests.exe'),
          ('copy-capture', 'RUN-COPY-CAPTURE-CHECKS.cmd', 'CopyCaptureTests.exe')]


def trace_sources():
    rows = json.loads((CORE / 'sdk-reference.json').read_text())['sources']
    wanted = {'PluginAPI.h', 'EventManager.h', 'EventManager.cpp', 'Serialization.cpp',
              'OnPreDamageHandler.cpp', 'EventDispatch.cpp', 'ITR.cpp'}
    result = []
    for row in rows:
        path = Path(row['path'])
        if path.name not in wanted:
            continue
        if sha(path) != row['sha256']:
            raise RuntimeError(f'Changed pinned source: {path}')
        result.append(dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size, prior_pin=True))
    if len(result) != 7:
        raise RuntimeError('Expected seven pinned source trace inputs')
    parent = Path(next(r['path'] for r in result if Path(r['path']).name == 'PluginAPI.h')).parent
    for name in ('Core_Serialization.cpp', 'Hooks_SaveLoad.cpp', 'Hooks_Gameplay.cpp', 'PluginManager.cpp'):
        path = parent / name
        result.append(dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size, prior_pin=False))
    write(STEP / 'Evidence/SOURCE-TRACE.json', dict(files=result, copied_donor_implementation=False,
          api='xNVSE event interface8: IsEventHandlerFirst index11 offset44, prefix48 bytes',
          original_live_cause_established=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', required=True)
    args = parser.parse_args()
    build = (CORE / 'out' / args.build).resolve()
    if build.parent != (CORE / 'out').resolve():
        raise RuntimeError('Build must be directly under native output')
    baseline = json.loads((ROOT / 'source/combat/step4i/Evidence/VERIFICATION.json').read_text())['source_inputs']
    baseline += json.loads((ROOT / 'source/combat/step4h/Evidence/VERIFICATION.json').read_text())['source_inputs']
    # Current4I overrides earlier4H input rows for the same path.
    baseline = {r['path']: r for r in reversed(baseline)}
    changed, unchanged = [], []
    for relative, row in baseline.items():
        path = ROOT / relative
        now = record(path, ROOT)
        if now['sha256'] == row['sha256']:
            unchanged.append(now)
        elif relative.startswith('native/NVOCombatCore/') and path.relative_to(CORE).as_posix() in ALLOWED:
            changed.append(dict(before_sha256=row['sha256'], after=now))
        else:
            raise RuntimeError(f'Unexpected baseline change: {relative}')
    if len(changed) != len(ALLOWED):
        raise RuntimeError('Unexpected changed-file set')
    for name in ('CMakeLists.txt', 'BUILD.cmd'):
        if any(s in (CORE / name).read_text() for s in ('MaterialPreview', 'ArmourModel.cpp', 'ImpactBinding', 'ShadowAdapter', 'ResponseDefinitions')):
            raise RuntimeError('Offline model unexpectedly linked')
    old = ROOT / 'release/NVO-Combat-Packet-4I-Native-Copy-Capture/Source/NVOCombatCore'
    for name in ('src/CurrentHit.cpp', 'src/HitTransaction.cpp'):
        if naked_functions((old / name).read_text()) != naked_functions((CORE / name).read_text()):
            raise RuntimeError(f'Hook assembly changed: {name}')
    trace_sources()
    sources = [CORE / n for n in ('BUILD.cmd', 'CMakeLists.txt', 'README.md', 'sdk-reference.json',
        'THIRD-PARTY-NOTICES.md', 'LICENSE-GPL-3.0.txt', 'LICENSE-ITR-MIT.txt', 'CREDITS-BALLISTX.md')]
    for folder in ('include', 'src', 'tests', 'config'):
        sources += sorted(p for p in (CORE / folder).glob('*') if p.is_file()
                          and p.suffix.lower() in ('.hpp', '.h', '.cpp', '.inl', '.cmd', '.def', '.ini', '.tsv'))
    sources += [MODEL / 'CoverageProfiles.hpp', MODEL / 'CoverageProfiles.cpp']
    inputs = [record(p, ROOT) for p in sources]
    runtime = [p for p in sources if p.parent.name in ('include', 'src') or p.parent == MODEL
               or p.name in ('BUILD.cmd', 'CMakeLists.txt')]
    if any(p.stat().st_mtime_ns > (build / 'NVOCombatCore.dll').stat().st_mtime_ns for p in runtime):
        raise RuntimeError('Runtime source newer than build')
    results, evidence = {}, [STEP / 'Evidence/SOURCE-TRACE.json']
    for name, runner, exe in CHECKS:
        path = CORE / f'tests/out/{name}-results.txt'
        output = path.read_text()
        match = re.search(r'^RESULT checks=(\d+) failures=0', output, re.M)
        if not match or re.search(r'\bFAIL\b', output):
            raise RuntimeError(f'Missing/failed checks: {name}')
        log = CORE / f'tests/out/{name}-build.log'
        if re.search(r'\b(?:warning|error) [A-Z]+\d+', log.read_text(), re.I):
            raise RuntimeError(f'Compiler diagnostic: {name}')
        # The changed production files must precede this suite's execution.
        relevant = ['src/DamageEvents.cpp', 'include/DamageEvents.hpp', 'include/NativeObserver.hpp'] if name == 'damage-event' else []
        if name == 'hit-scope': relevant = ['src/HitTransaction.cpp', 'tests/HitTransactionScopeTests.cpp']
        if any((CORE / p).stat().st_mtime_ns > path.stat().st_mtime_ns for p in relevant):
            raise RuntimeError(f'Stale suite: {name}')
        results[name] = dict(checks=int(match[1]), result=output.strip(), runner=runner,
            results_utc=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            executable=record(CORE / 'tests/out' / exe, ROOT))
        for suffix in ('results.txt', 'build.log', 'toolchain.log'):
            dst = STEP / 'Evidence' / f'{name}-{suffix}'
            copy(CORE / 'tests/out' / f'{name}-{suffix}', dst); evidence.append(dst)
    binary = inspect_pair(build, b'NVOCombatCore 0.3.29 | phase=4I1')
    imports = re.findall(r'^\s{4}([^\s]+\.dll)\s*$', (build / 'dll-details.txt').read_text(), re.I | re.M)
    if [v.lower() for v in imports] != ['kernel32.dll']:
        raise RuntimeError(f'Unexpected imports: {imports}')
    binary['imports'] = imports
    for name in ('build.log', 'dll-details.txt', 'toolchain.log'):
        dst = STEP / 'Evidence' / name; copy(build / name, dst); evidence.append(dst)
    verification = dict(packet='4I1', status='COMPILED_NOT_INSTALLED',
        verified_utc=datetime.now(timezone.utc).isoformat(), native_version=329, last_installed_version=328,
        original_callback_gap_cause_established=False, live_recovery_verified=False,
        binary=binary, checks_total=sum(r['checks'] for r in results.values()), suites=results,
        source_inputs=inputs, unchanged_files=len(unchanged), changed_baseline_files=changed,
        unchanged_wrapper_assembly=True, model_inputs_unchanged=True, model_tests_rerun=False,
        armour_reader_tests_rerun=False, new_engine_hooks=0, new_runtime_dependencies=[],
        model_linked=False, damage_replacement=False, stagger_writes=False, installed=False,
        game_accessed=False, game_launched=False, live_acceptance=False,
        limitations=['Synthetic API/PE/form fixtures do not run xNVSE, ITR or game hooks.',
                     'Registry positives are instant observations; false remains ambiguous.',
                     'Registration is not emission or actual committed damage.',
                     'Provider suppression may remain even with confirmed registrations.'])
    for name, value in [('VERIFICATION.json', verification), ('UNCHANGED-NATIVE.json', dict(files=unchanged))]:
        dst = STEP / 'Evidence' / name; write(dst, value); evidence.append(dst)
    files = []
    for name in ('README.md', 'REVIEW.md', 'SOURCE-TRACE.md', 'START-HERE.html'):
        dst = RELEASE / name; copy(STEP / name, dst); files.append(dst)
    for path in sources:
        dst = RELEASE / 'Source' / path.relative_to(ROOT / 'native'); copy(path, dst); files.append(dst)
    for path in evidence:
        dst = RELEASE / 'Evidence' / path.name; copy(path, dst); files.append(dst)
    proposed = []
    for name in ('NVOCombatCore.dll', 'NVOCombatCore.pdb'):
        dst = RELEASE / 'Data/NVSE/Plugins' / name; copy(build / name, dst); files.append(dst)
        proposed.append(record(dst, RELEASE))
    for name in ('CREDITS.md', 'LICENSE'):
        dst = RELEASE / name; copy(ROOT / name, dst); files.append(dst)
    install = RELEASE / 'PROPOSED-FILES.json'
    write(install, dict(prepared_only=True, installed=False, files=proposed,
        note='DLL/PDB only; separate approval, fresh installed-state checks and backup required. No installer included.'))
    files.append(install)
    for href in re.findall(r'href="([^"]+)"', (RELEASE / 'START-HERE.html').read_text()):
        if not (RELEASE / href).is_file(): raise RuntimeError(f'Missing link: {href}')
    if inputs != [record(p, ROOT) for p in sources]: raise RuntimeError('Sources changed during packaging')
    for row in inputs:
        if sha(RELEASE / 'Source' / Path(row['path']).relative_to('native')) != row['sha256']:
            raise RuntimeError('Source package mismatch')
    manifest = RELEASE / 'MANIFEST.json'
    write(manifest, dict(packet='4I1', status='COMPILED_NOT_INSTALLED', files=[record(p, RELEASE) for p in sorted(files)]))
    bundle = RELEASE.with_suffix('.zip')
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(files + [manifest]): archive.write(p, str(Path(RELEASE.name) / p.relative_to(RELEASE)))
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None: raise RuntimeError('ZIP integrity failure')
        for row in json.loads(manifest.read_text())['files']:
            if hashlib.sha256(archive.read(RELEASE.name + '/' + row['path'])).hexdigest() != row['sha256']:
                raise RuntimeError('ZIP hash mismatch')
    write(STEP / 'PACKAGE.json', dict(path=str(bundle), sha256=sha(bundle), bytes=bundle.stat().st_size,
                                     status='COMPILED_NOT_INSTALLED'))
    print(json.dumps(dict(packet=str(RELEASE), checks={k:v['checks'] for k,v in results.items()},
                          total=verification['checks_total'], unchanged_files=len(unchanged), installed=False)))


if __name__ == '__main__': main()

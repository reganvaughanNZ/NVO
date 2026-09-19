"""Package checked diagnostic routes. No installation, process actions or DLL loading."""
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
STEP = ROOT / 'source/combat/step4j'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4J-Damage-Routes'
ALLOWED = {'README.md', 'CMakeLists.txt', 'include/HitTransaction.hpp', 'include/ActorValueObserver.hpp',
           'src/ActorValueObserver.cpp', 'src/HitTransaction.cpp', 'src/DamageEvents.cpp', 'src/Plugin.cpp',
           'tests/HitTransactionScopeTests.cpp', 'tests/DamageEventLifecycleTests.cpp'}
CHECKS = [
    ('av-attribution', 'RUN-AV-ATTRIBUTION-CHECKS.cmd', 'ActorValueAttributionTests.exe',
     ['src/ActorValueObserver.cpp', 'include/ActorValueObserver.hpp', 'include/DamageAttribution.hpp',
      'include/HitTransaction.hpp', 'tests/ActorValueAttributionTests.cpp']),
    ('hit-scope', 'RUN-HIT-SCOPE-CHECKS.cmd', 'HitTransactionScopeTests.exe',
     ['src/HitTransaction.cpp', 'include/HitTransaction.hpp', 'tests/HitTransactionScopeTests.cpp']),
    ('damage-event', 'RUN-DAMAGE-EVENT-CHECKS.cmd', 'DamageEventLifecycleTests.exe',
     ['src/DamageEvents.cpp', 'include/ActorValueObserver.hpp', 'tests/DamageEventLifecycleTests.cpp'])]


def trace_sources():
    result = []
    for row in json.loads((CORE / 'sdk-reference.json').read_text())['sources']:
        path = Path(row['path'])
        if path.name not in {'GameProcess.h', 'GameForms.h', 'GameObjects.h', 'OnPreDamageHandler.cpp'}:
            continue
        if sha(path) != row['sha256']:
            raise RuntimeError(f'Changed pinned source: {path}')
        result.append(dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size, prior_pin=True))
    if len(result) != 4:
        raise RuntimeError('Expected four pinned donor sources')
    captures = []
    inputs = [
        ('source/combat/step3k/runtime-20260916-100050/hitme-0089A760.bin', 0x89A760,
         'fe7630d6076ac3fe6e19827eb79c00d9e4a128081fd5db48222221f5cd78d515',
         [(0x89BDD8, 0x89BDAF, 41, 0x0F240085048900B4), (0x89BB8E, 0x89BB65, 41, 0x907658F5F564234C)]),
    ]
    health_hash = '3e1f757cf838f959bc358f87383b076679fd7f198fbcafc9eb99cd7bd492c2b1'
    health = [p for p in (ROOT / 'source/combat/step3l').glob('runtime-*/hitme_tail_and_health_apply-0089BF60.bin')
              if sha(p) == health_hash]
    if not health:
        raise RuntimeError('Missing retained health caller capture')
    inputs.append((health[0].relative_to(ROOT).as_posix(), 0x89BF60, health_hash,
                   [(0x89D82D, 0x89D80E, 31, 0xBA8F8D907EB3EA79)]))
    header = (CORE / 'include/DamageAttribution.hpp').read_text()
    for relative, base, digest, windows in inputs:
        path = ROOT / relative
        if sha(path) != digest:
            raise RuntimeError(f'Changed retained capture: {relative}')
        raw = path.read_bytes()
        rows = []
        for caller, start, size, expected in windows:
            window = raw[start-base:start-base+size]
            if len(window) != size:
                raise RuntimeError('Truncated route window')
            fnv = 14695981039346656037
            for byte in window:
                fnv = ((fnv ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
            if fnv != expected or f'0x{expected:016X}ull' not in header or f'0x{caller:08X}' not in header:
                raise RuntimeError('Route fingerprint disagrees with retained capture/header')
            rows.append(dict(caller=f'{caller:08X}', start=f'{start:08X}', bytes=size,
                             fnv1a64=f'{fnv:016X}', sha256=hashlib.sha256(window).hexdigest()))
        captures.append(dict(**record(path, ROOT), base=f'{base:08X}', windows=rows))
    write(STEP / 'Evidence/SOURCE-TRACE.json', dict(files=result, retained_captures=captures,
        new_engine_hooks=0, damage_components_verified=False, copied_donor_implementation=False,
        note='Guarded caller routes and original hit metadata; neither proves primary/secondary ownership.'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', required=True)
    args = parser.parse_args()
    build = (CORE / 'out' / args.build).resolve()
    if build.parent != (CORE / 'out').resolve():
        raise RuntimeError('Build must be directly under native output')
    baseline = json.loads((ROOT / 'source/combat/step4i1/Evidence/VERIFICATION.json').read_text())['source_inputs']
    baseline += json.loads((ROOT / 'source/combat/step4h/Evidence/VERIFICATION.json').read_text())['source_inputs']
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
        raise RuntimeError(f'Unexpected changed-file set: {len(changed)}')
    for name in ('CMakeLists.txt', 'BUILD.cmd'):
        if any(s in (CORE / name).read_text() for s in ('MaterialPreview', 'ArmourModel.cpp', 'ImpactBinding', 'ShadowAdapter', 'ResponseDefinitions')):
            raise RuntimeError('Offline model unexpectedly linked')
    old = ROOT / 'release/NVO-Combat-Packet-4I1-Callback-Survival/Source/NVOCombatCore'
    for name in ('src/CurrentHit.cpp', 'src/HitTransaction.cpp', 'src/ActorValueObserver.cpp'):
        if naked_functions((old / name).read_text()) != naked_functions((CORE / name).read_text()):
            raise RuntimeError(f'Hook assembly changed: {name}')
    old_av = (old / 'src/ActorValueObserver.cpp').read_text()
    new_av = (CORE / 'src/ActorValueObserver.cpp').read_text()
    # Existing hook guards/install/chaining stay byte-identical at source level.
    if old_av[old_av.index('bool Image('):old_av.index('} // namespace')] != new_av[new_av.index('bool Image('):new_av.index('} // namespace')]:
        raise RuntimeError('AV hook guards or installer changed')
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
    results, evidence = {}, [STEP / 'Evidence/SOURCE-TRACE.json', STEP / 'Evidence/TEST-KIT-FORMS.json']
    for name, runner, exe, relevant in CHECKS:
        path = CORE / f'tests/out/{name}-results.txt'
        output = path.read_text()
        match = re.search(r'^RESULT checks=(\d+) failures=0', output, re.M)
        if name == 'av-attribution':
            match = re.search(r'^AV attribution checks: (\d+) passed, 0 failed$', output, re.M)
        if not match or re.search(r'\bFAIL\b', output):
            raise RuntimeError(f'Missing/failed checks: {name}')
        log = CORE / f'tests/out/{name}-build.log'
        if re.search(r'\b(?:warning|error) [A-Z]+\d+', log.read_text(), re.I):
            raise RuntimeError(f'Compiler diagnostic: {name}')
        if any((CORE / p).stat().st_mtime_ns > path.stat().st_mtime_ns for p in relevant + ['tests/' + runner]):
            raise RuntimeError(f'Stale suite: {name}')
        results[name] = dict(checks=int(match[1]), runner=runner,
            results_utc=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            executable=record(CORE / 'tests/out' / exe, ROOT))
        for suffix in ('results.txt', 'build.log', 'toolchain.log'):
            dst = STEP / 'Evidence' / f'{name}-{suffix}'
            copy(CORE / 'tests/out' / f'{name}-{suffix}', dst); evidence.append(dst)
    binary = inspect_pair(build, b'NVOCombatCore 0.3.30 | phase=4J')
    imports = re.findall(r'^\s{4}([^\s]+\.dll)\s*$', (build / 'dll-details.txt').read_text(), re.I | re.M)
    if [v.lower() for v in imports] != ['kernel32.dll']:
        raise RuntimeError(f'Unexpected imports: {imports}')
    binary['imports'] = imports
    for name in ('build.log', 'dll-details.txt', 'toolchain.log'):
        dst = STEP / 'Evidence' / name; copy(build / name, dst); evidence.append(dst)
    kit = STEP / 'NVOComponentKit4J.txt'
    expected_kit = ['player.additem 000E3778 1', 'player.additem 0008ED03 50', 'player.additem 00004330 3',
                    'player.additem 0000432D 1', 'player.additem 00029371 100']
    if kit.read_text().splitlines() != expected_kit:
        raise RuntimeError('Unexpected test-kit command')
    verification = dict(packet='4J', status='COMPILED_NOT_INSTALLED',
        verified_utc=datetime.now(timezone.utc).isoformat(), native_version=330, last_installed_version=329,
        binary=binary, checks_total=sum(r['checks'] for r in results.values()), suites=results,
        source_inputs=inputs, unchanged_files=len(unchanged), changed_baseline_files=changed,
        unchanged_wrapper_assembly=True, unchanged_av_hook_guards_and_installer=True,
        model_inputs_unchanged=True, model_tests_rerun=False, armour_reader_tests_rerun=False,
        new_engine_hooks=0, new_runtime_dependencies=[], model_linked=False,
        damage_replacement=False, stagger_writes=False, installed=False, game_launched=False,
        game_closed=False, game_files_modified=False, game_read_only_form_lookup=True,
        live_acceptance=False, component_verified=False, application_verified=False,
        limitations=['Synthetic fixtures do not run the game or actual ITR/xNVSE providers.',
            'Caller, hit context and callback matches are separate diagnostic witnesses.',
            'In-scope is not primary; out-of-scope is not automatically secondary.',
            'Provider-call nets are not single committed writes and cannot be added across nested windows.',
            'Exact contact input, coherent impact snapshot and component/application ownership remain unfinished.'])
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
    dst = RELEASE / kit.name; copy(kit, dst); files.append(dst); proposed.append(record(dst, RELEASE))
    for name in ('CREDITS.md', 'LICENSE'):
        dst = RELEASE / name; copy(ROOT / name, dst); files.append(dst)
    install = RELEASE / 'PROPOSED-FILES.json'
    write(install, dict(prepared_only=True, installed=False, files=proposed,
        note='DLL/PDB and inventory batch only; separate approval, fresh installed-state checks and backup. No installer included.'))
    files.append(install)
    for href in re.findall(r'href="([^"]+)"', (RELEASE / 'START-HERE.html').read_text()):
        if not (RELEASE / href).is_file(): raise RuntimeError(f'Missing link: {href}')
    if inputs != [record(p, ROOT) for p in sources]: raise RuntimeError('Sources changed during packaging')
    for row in inputs:
        if sha(RELEASE / 'Source' / Path(row['path']).relative_to('native')) != row['sha256']:
            raise RuntimeError('Source package mismatch')
    manifest = RELEASE / 'MANIFEST.json'
    write(manifest, dict(packet='4J', status='COMPILED_NOT_INSTALLED', files=[record(p, RELEASE) for p in sorted(files)]))
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

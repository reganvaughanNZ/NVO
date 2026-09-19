"""Package the checked flame-lifecycle fix. Never install, load the DLL or access a game."""
import argparse
import hashlib
import json
import re
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from prepare_combat_4g import ROOT, MODEL, sha, record, write, copy
from prepare_combat_4i import naked_functions
from package_combat_3b2 import inspect_pair

CORE = ROOT / 'native/NVOCombatCore'
STEP = ROOT / 'source/combat/step4j1'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4J1-Flame-Lifecycle'
ALLOWED = {'README.md', 'CMakeLists.txt', 'include/NativeObserver.hpp',
           'include/FlightPreview.hpp', 'include/FlightPhysics.hpp',
           'src/NativeObserver.cpp', 'src/FlightPreview.cpp', 'src/FlightPhysics.cpp', 'src/Plugin.cpp'}
NEW_TESTS = {'tests/ProjectileLifecycleTests.cpp', 'tests/RUN-PROJECTILE-LIFECYCLE-CHECKS.cmd'}
LIVE = ROOT / 'source/combat/step4j/Evidence/LIVE-4J-20260919-094727.log'
LIVE_SHA = '8e079a12b768f5b2ae25b56e0ddc378092f73ee51efec4e3239cd2903ebb3d30'
SHOWOFF_SHA = '5c7f69c550a341124fc408fa9a2010e75dadcb0a360e51974fd46c62ef489270'
CHECKS = [
    dict(name='projectile-lifecycle', runner='RUN-PROJECTILE-LIFECYCLE-CHECKS.cmd',
         exe='ProjectileLifecycleTests.exe', result='projectile-lifecycle-results.txt',
         logs=['projectile-lifecycle-build.log', 'projectile-lifecycle-toolchain.log'],
         pattern=r'^Projectile lifecycle checks: (\d+) passed, 0 failed$',
         relevant=['src/NativeObserver.cpp', 'include/NativeObserver.hpp',
                   'src/FlightPreview.cpp', 'include/FlightPreview.hpp',
                   'src/FlightPhysics.cpp', 'include/FlightPhysics.hpp',
                   'include/FlightAdmission.hpp', 'include/SpawnCall.hpp',
                   'tests/ProjectileLifecycleTests.cpp'],
         scope='Production NativeObserver with bounded synthetic forms and stubbed dependencies; '
               'actual physics/preview branches receive compilation and source review, not execution here.'),
    dict(name='admission', runner='RUN-ADMISSION-CHECKS.cmd', exe='FlightAdmissionTests.exe',
         result='admission-checks.txt', logs=['admission-build.log'],
         pattern=r'^PASS (\d+) checks; bounded production pool/receipt fixtures; no game or DLL execution\.$',
         relevant=['include/FlightAdmission.hpp', 'include/SpawnCall.hpp', 'tests/FlightAdmissionTests.cpp'],
         scope='Synthetic production admission-pool and spawn-receipt fixtures; no game or DLL execution.')]


def trace_sources():
    wanted = {'ShowOffEvents.h', 'GameForms.h', 'GameObjects.h'}
    files = []
    for row in json.loads((CORE / 'sdk-reference.json').read_text())['sources']:
        path = Path(row['path'])
        if path.name not in wanted:
            continue
        digest = sha(path)
        if digest != row['sha256'] or (path.name == 'ShowOffEvents.h' and digest != SHOWOFF_SHA):
            raise RuntimeError(f'Changed pinned donor source: {path}')
        files.append(dict(path=str(path), sha256=digest, bytes=path.stat().st_size, prior_pin=True))
    if len(files) != len(wanted) or {Path(r['path']).name for r in files} != wanted:
        raise RuntimeError('Expected the three exact donor-source pins')
    if sha(LIVE) != LIVE_SHA:
        raise RuntimeError('Retained 4J live capture changed')
    user_document = STEP / 'Evidence/USER-DOCUMENT.json'
    json.loads(user_document.read_text())  # Include only the receipt, never the attachment or extraction.
    destination = STEP / 'Evidence/SOURCE-TRACE.json'
    write(destination, dict(files=files, retained_live_capture=record(LIVE, ROOT),
        user_document_receipt=record(user_document, ROOT), copied_donor_implementation=False,
        new_engine_hooks=0, game_files_read=False,
        note='Retained evidence and local donor source only. Repeated CREATE notifications do not '
             'establish unique physical projectiles, components or damage applications.'))
    return destination


def binary_imports(path):
    """Read the PE32 import table itself, independently of the dumpbin report."""
    data = path.read_bytes()
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    if data[pe:pe + 4] != b'PE\0\0':
        raise RuntimeError('Invalid PE signature')
    machine, count = struct.unpack_from('<HH', data, pe + 4)
    optional_size = struct.unpack_from('<H', data, pe + 20)[0]
    optional = pe + 24
    if machine != 0x14c or struct.unpack_from('<H', data, optional)[0] != 0x10b:
        raise RuntimeError('Imports require PE32 x86')
    sections = []
    for i in range(count):
        section = optional + optional_size + 40 * i
        virtual_size, rva, raw_size, raw = struct.unpack_from('<IIII', data, section + 8)
        sections.append((rva, virtual_size, raw_size, raw))

    def offset(rva, size):
        for start, virtual_size, raw_size, raw in sections:
            delta = rva - start
            if 0 <= delta and delta + size <= raw_size and raw + delta + size <= len(data):
                return raw + delta
        raise RuntimeError('Import RVA outside file-backed sections')

    import_rva, import_size = struct.unpack_from('<II', data, optional + 96 + 8)
    if not import_rva or import_size < 20:
        raise RuntimeError('Missing import table')
    imports = []
    for cursor in range(0, import_size - 19, 20):
        descriptor = struct.unpack_from('<IIIII', data, offset(import_rva + cursor, 20))
        if not any(descriptor):
            return imports
        name = bytearray()
        for i in range(256):
            char = data[offset(descriptor[3] + i, 1)]
            if char == 0:
                break
            name.append(char)
        else:
            raise RuntimeError('Unterminated import name')
        imports.append(name.decode('ascii'))
    raise RuntimeError('Unterminated import table')


def check_suites():
    results, evidence = {}, []
    for suite in CHECKS:
        output_dir = CORE / 'tests/out'
        result_path = output_dir / suite['result']
        output = result_path.read_text()
        matches = re.findall(suite['pattern'], output, re.M)
        if len(matches) != 1 or int(matches[0]) <= 0 or re.search(r'\bFAIL\b', output):
            raise RuntimeError(f'Missing/failed checks: {suite["name"]}')
        relevant = [CORE / p for p in suite['relevant'] + ['tests/' + suite['runner']]]
        executable = output_dir / suite['exe']
        for path in relevant:
            if path.stat().st_mtime_ns > result_path.stat().st_mtime_ns:
                raise RuntimeError(f'Stale suite {suite["name"]}: {path}')
        if executable.stat().st_mtime_ns > result_path.stat().st_mtime_ns:
            raise RuntimeError(f'Suite executable newer than result: {suite["name"]}')
        for name in suite['logs']:
            log = output_dir / name
            if re.search(r'\b(?:warning|error) [A-Z]+\d+', log.read_text(), re.I):
                raise RuntimeError(f'Compiler/toolchain diagnostic: {name}')
            if log.stat().st_mtime_ns > result_path.stat().st_mtime_ns:
                raise RuntimeError(f'Suite log newer than result: {name}')
        results[suite['name']] = dict(checks=int(matches[0]), runner=suite['runner'],
            results_utc=datetime.fromtimestamp(result_path.stat().st_mtime, timezone.utc).isoformat(),
            executable=record(executable, ROOT), result=record(result_path, ROOT),
            relevant_inputs=[record(p, ROOT) for p in relevant], scope=suite['scope'])
        for name in [suite['result']] + suite['logs']:
            dst = STEP / 'Evidence' / name
            copy(output_dir / name, dst)
            evidence.append(dst)
    return results, evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', required=True)
    args = parser.parse_args()
    build = (CORE / 'out' / args.build).resolve()
    if build.parent != (CORE / 'out').resolve():
        raise RuntimeError('Build must be directly under native output')
    baseline_paths = [ROOT / f'source/combat/{packet}/Evidence/VERIFICATION.json'
                      for packet in ('step4j', 'step4h')]
    baseline = {}
    for path in baseline_paths:
        for row in json.loads(path.read_text())['source_inputs']:
            baseline.setdefault(row['path'], row)
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
    changed_names = {Path(row['after']['path']).relative_to('native/NVOCombatCore').as_posix()
                     for row in changed}
    if changed_names != ALLOWED:
        raise RuntimeError(f'Unexpected changed-file set: {sorted(changed_names)}')
    for name in NEW_TESTS:
        if not (CORE / name).is_file() or 'native/NVOCombatCore/' + name in baseline:
            raise RuntimeError(f'Missing or non-new lifecycle fixture: {name}')
    for name in ('CMakeLists.txt', 'BUILD.cmd'):
        if any(s in (CORE / name).read_text() for s in
               ('MaterialPreview', 'ArmourModel.cpp', 'ImpactBinding', 'ShadowAdapter', 'ResponseDefinitions')):
            raise RuntimeError('Offline model unexpectedly linked')
    old = ROOT / 'release/NVO-Combat-Packet-4J-Damage-Routes/Source/NVOCombatCore'
    for name in ('src/CurrentHit.cpp', 'src/HitTransaction.cpp', 'src/ActorValueObserver.cpp',
                 'src/FlightPhysics.cpp', 'src/FlightTiming.cpp', 'src/SpawnBoundary.cpp'):
        if sha(old / name) != baseline['native/NVOCombatCore/' + name]['sha256']:
            raise RuntimeError(f'Prior packaged wrapper source changed: {name}')
        if naked_functions((old / name).read_text()) != naked_functions((CORE / name).read_text()):
            raise RuntimeError(f'Hook assembly changed: {name}')
    old_av = (old / 'src/ActorValueObserver.cpp').read_text()
    new_av = (CORE / 'src/ActorValueObserver.cpp').read_text()
    if old_av[old_av.index('bool Image('):old_av.index('} // namespace')] != \
            new_av[new_av.index('bool Image('):new_av.index('} // namespace')]:
        raise RuntimeError('AV hook guards or installer changed')
    sources = [CORE / n for n in ('BUILD.cmd', 'CMakeLists.txt', 'README.md', 'sdk-reference.json',
        'THIRD-PARTY-NOTICES.md', 'LICENSE-GPL-3.0.txt', 'LICENSE-ITR-MIT.txt', 'CREDITS-BALLISTX.md')]
    for folder in ('include', 'src', 'tests', 'config'):
        sources += sorted(p for p in (CORE / folder).glob('*') if p.is_file()
                          and p.suffix.lower() in ('.hpp', '.h', '.cpp', '.inl', '.cmd', '.def', '.ini', '.tsv'))
    sources += sorted({MODEL / 'CoverageProfiles.hpp', MODEL / 'CoverageProfiles.cpp'} |
                      {ROOT / p for p in baseline if p.startswith('native/NVOCombatModel/')})
    inputs = [record(p, ROOT) for p in sources]
    runtime = [p for p in sources if p.parent.name in ('include', 'src') or
               p in (MODEL / 'CoverageProfiles.hpp', MODEL / 'CoverageProfiles.cpp') or
               p.name in ('BUILD.cmd', 'CMakeLists.txt')]
    if any(p.stat().st_mtime_ns > (build / 'NVOCombatCore.dll').stat().st_mtime_ns for p in runtime):
        raise RuntimeError('Runtime source newer than build')
    results, evidence = check_suites()
    evidence += [trace_sources(), STEP / 'Evidence/USER-DOCUMENT.json']
    binary = inspect_pair(build, b'NVOCombatCore 0.3.31 | phase=4J1')
    imports = binary_imports(build / 'NVOCombatCore.dll')
    report_imports = re.findall(r'^\s{4}([^\s]+\.dll)\s*$',
                               (build / 'dll-details.txt').read_text(), re.I | re.M)
    if [v.lower() for v in imports] != ['kernel32.dll'] or \
            [v.lower() for v in report_imports] != ['kernel32.dll']:
        raise RuntimeError(f'Unexpected imports or stale report: {imports}, {report_imports}')
    binary['imports'] = imports
    for name in ('build.log', 'dll-details.txt', 'toolchain.log'):
        dst = STEP / 'Evidence' / name
        copy(build / name, dst)
        evidence.append(dst)
    verification = dict(packet='4J1', status='COMPILED_NOT_INSTALLED',
        verified_utc=datetime.now(timezone.utc).isoformat(), native_version=331, last_installed_version=330,
        last_installed_flame_lifecycle='unresolved in the retained 4J capture; no fresh game inspection',
        binary=binary, checks_total=sum(r['checks'] for r in results.values()), suites=results,
        baseline_evidence=[record(p, ROOT) for p in baseline_paths],
        source_inputs=inputs, unchanged_files=len(unchanged), changed_baseline_files=changed,
        new_fixture_files=[record(CORE / p, ROOT) for p in sorted(NEW_TESTS)],
        unchanged_wrapper_assembly=True, unchanged_av_hook_guards_and_installer=True,
        model_inputs_unchanged=True,
        unchanged_model_inputs=[r for r in unchanged if r['path'].startswith('native/NVOCombatModel/')],
        model_tests_rerun=False, armour_reader_tests_rerun=False,
        new_engine_hooks=0, new_runtime_dependencies=[], model_linked=False,
        damage_replacement=False, stagger_writes=False, installed=False, game_launched=False,
        game_closed=False, game_files_read=False, game_files_modified=False,
        live_acceptance=False, component_verified=False, application_verified=False,
        limitations=['Synthetic fixtures do not execute the game, real providers or the DLL.',
            'Lifecycle fixtures exercise production NativeObserver with stubbed physics/preview; '
            'actual physics/preview changes receive compilation and source review only.',
            'Observer associations and repeated CREATE notices are not unique projectile/application identities.',
            'The retained 4J route pass does not establish flame-lifecycle recovery in native331.',
            'Secondary-effect coverage, exact contact input and coherent impact snapshots remain unfinished.'])
    for name, value in [('VERIFICATION.json', verification), ('UNCHANGED-NATIVE.json', dict(files=unchanged))]:
        dst = STEP / 'Evidence' / name
        write(dst, value)
        evidence.append(dst)
    files = []
    for name in ('README.md', 'REVIEW.md', 'SOURCE-TRACE.md', 'DOCUMENT-REVIEW.md', 'START-HERE.html'):
        dst = RELEASE / name
        copy(STEP / name, dst)
        files.append(dst)
    for path in sources:
        dst = RELEASE / 'Source' / path.relative_to(ROOT / 'native')
        copy(path, dst)
        files.append(dst)
    for path in evidence:
        dst = RELEASE / 'Evidence' / path.name
        copy(path, dst)
        files.append(dst)
    proposed = []
    for name in ('NVOCombatCore.dll', 'NVOCombatCore.pdb'):
        dst = RELEASE / 'Data/NVSE/Plugins' / name
        copy(build / name, dst)
        files.append(dst)
        proposed.append(record(dst, RELEASE))
    for name in ('CREDITS.md', 'LICENSE'):
        dst = RELEASE / name
        copy(ROOT / name, dst)
        files.append(dst)
    install = RELEASE / 'PROPOSED-FILES.json'
    write(install, dict(prepared_only=True, installed=False, files=proposed,
        existing_inventory_kit='NVOComponentKit4J.txt; reuse only, not included or redeployed',
        note='DLL/PDB only; separate approval, fresh installed-state checks and backup. No installer included.'))
    files.append(install)
    for href in re.findall(r'href="([^"]+)"', (RELEASE / 'START-HERE.html').read_text()):
        if not (RELEASE / href).is_file():
            raise RuntimeError(f'Missing link: {href}')
    if inputs != [record(p, ROOT) for p in sources]:
        raise RuntimeError('Sources changed during packaging')
    for row in inputs:
        if sha(RELEASE / 'Source' / Path(row['path']).relative_to('native')) != row['sha256']:
            raise RuntimeError('Source package mismatch')
    manifest = RELEASE / 'MANIFEST.json'
    expected_files = set(files + [manifest])
    extras = {p for p in RELEASE.rglob('*') if p.is_file()} - expected_files
    if extras:
        raise RuntimeError(f'Unexpected release files: {sorted(str(p) for p in extras)}')
    write(manifest, dict(packet='4J1', status='COMPILED_NOT_INSTALLED',
                         files=[record(p, RELEASE) for p in sorted(files)]))
    bundle = RELEASE.with_suffix('.zip')
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(expected_files):
            archive.write(p, (Path(RELEASE.name) / p.relative_to(RELEASE)).as_posix())
    with zipfile.ZipFile(bundle) as archive:
        expected_names = {(Path(RELEASE.name) / p.relative_to(RELEASE)).as_posix() for p in expected_files}
        if len(archive.namelist()) != len(expected_names) or set(archive.namelist()) != expected_names:
            raise RuntimeError('ZIP entry set mismatch')
        if archive.testzip() is not None:
            raise RuntimeError('ZIP integrity failure')
        for row in json.loads(manifest.read_text())['files']:
            if sha(RELEASE / row['path']) != row['sha256'] or \
                    hashlib.sha256(archive.read(RELEASE.name + '/' + row['path'])).hexdigest() != row['sha256']:
                raise RuntimeError('Manifest or ZIP hash mismatch')
        if archive.read(RELEASE.name + '/MANIFEST.json') != manifest.read_bytes():
            raise RuntimeError('Archived manifest mismatch')
    write(STEP / 'PACKAGE.json', dict(path=str(bundle), sha256=sha(bundle), bytes=bundle.stat().st_size,
                                     status='COMPILED_NOT_INSTALLED'))
    print(json.dumps(dict(packet=str(RELEASE), checks={k: v['checks'] for k, v in results.items()},
                         total=verification['checks_total'], unchanged_files=len(unchanged), installed=False)))


if __name__ == '__main__':
    main()

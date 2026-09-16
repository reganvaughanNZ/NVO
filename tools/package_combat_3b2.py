"""Inspect and package packet 3B2 without loading its DLL or running the game."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'native/NVOCombatCore'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_pair(build):
    dll = (build / 'NVOCombatCore.dll').read_bytes()
    pe = struct.unpack_from('<I', dll, 0x3c)[0]
    assert dll[pe:pe + 4] == b'PE\0\0'
    machine, count = struct.unpack_from('<HH', dll, pe + 4)
    opt_size = struct.unpack_from('<H', dll, pe + 20)[0]
    opt = pe + 24
    assert machine == 0x14c and struct.unpack_from('<H', dll, opt)[0] == 0x10b
    sections = []
    for i in range(count):
        row = opt + opt_size + 40 * i
        virtual_size, rva, raw_size, raw = struct.unpack_from('<IIII', dll, row + 8)
        sections.append((rva, max(virtual_size, raw_size), raw))

    def offset(rva):
        for start, size, raw in sections:
            if start <= rva < start + size:
                return raw + rva - start
        raise AssertionError('RVA outside section')

    debug_rva, debug_size = struct.unpack_from('<II', dll, opt + 96 + 6 * 8)
    codeview = None
    for i in range(debug_size // 28):
        row = offset(debug_rva) + i * 28
        kind, size, address, raw = struct.unpack_from('<IIII', dll, row + 12)
        if kind == 2 and dll[raw:raw + 4] == b'RSDS':
            codeview = (dll[raw + 4:raw + 20], struct.unpack_from('<I', dll, raw + 20)[0])
    assert codeview
    pdb = (build / 'NVOCombatCore.pdb').read_bytes()
    assert pdb.startswith(b'Microsoft C/C++ MSF 7.00')
    block_size, unused, total_blocks, directory_size, unused2, block_map = struct.unpack_from('<IIIIII', pdb, 32)
    assert len(pdb) == total_blocks * block_size
    page_count = (directory_size + block_size - 1) // block_size
    pages = struct.unpack_from('<' + 'I' * page_count, pdb, block_map * block_size)
    directory = b''.join(pdb[i * block_size:(i + 1) * block_size] for i in pages)[:directory_size]
    stream_count = struct.unpack_from('<I', directory)[0]
    sizes = struct.unpack_from('<' + 'I' * stream_count, directory, 4)
    cursor = 4 + 4 * stream_count
    info = None
    for i, size in enumerate(sizes):
        n = 0 if size == 0xffffffff else (size + block_size - 1) // block_size
        stream_pages = struct.unpack_from('<' + 'I' * n, directory, cursor)
        cursor += n * 4
        if i == 1:
            info = b''.join(pdb[j * block_size:(j + 1) * block_size] for j in stream_pages)[:size]
    assert info and info[12:28] == codeview[0] and struct.unpack_from('<I', info, 8)[0] == codeview[1]
    export_rva = struct.unpack_from('<I', dll, opt + 96)[0]
    export = offset(export_rva)
    names_count = struct.unpack_from('<I', dll, export + 24)[0]
    names = offset(struct.unpack_from('<I', dll, export + 32)[0])
    exports = []
    for i in range(names_count):
        address = offset(struct.unpack_from('<I', dll, names + i * 4)[0])
        exports.append(dll[address:dll.index(b'\0', address)].decode('ascii'))
    assert sorted(exports) == ['NVSEPlugin_Load', 'NVSEPlugin_Query']
    log = (build / 'build.log').read_text(errors='replace')
    assert not re.search(r'\b(?:warning|error) [A-Z]+\d+', log, re.I)
    assert b'NVOCombatCore 0.3.2 | phase=3B2' in dll
    return {'machine': 'PE32 x86', 'exports': exports, 'warnings': 0,
            'dll_sha256': digest(build / 'NVOCombatCore.dll'), 'pdb_sha256': digest(build / 'NVOCombatCore.pdb'),
            'codeview_pdb_guid': str(uuid.UUID(bytes_le=codeview[0])), 'pdb_age': codeview[1], 'pdb_pair_verified': True,
            'dll_bytes': len(dll), 'pdb_bytes': len(pdb),
            'validation_scope': 'Compilation and static identity/source/assembly inspection only. No DLL execution or gameplay tests.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', required=True)
    args = parser.parse_args()
    build = (PROJECT / 'out' / args.build).resolve()
    assert build.parent == (PROJECT / 'out').resolve()
    evidence = inspect_pair(build)
    evidence['manual_review'] = ['Existing CopyObserver assembly retains register/FP saves and one original tail jump.',
                               'FlightPreview imports bounded batch-file output, file metadata access, guarded reads and NVO logging.',
                               'No new event registration, engine setter, process-memory write or persistent game pointer in FlightPreview; kit file writes occur at capture initialization only.',
                               'Fixed console notice dispatched outside the parent observer lock.',
                               'Config parser and caches bounded; no files or game pointers polled every frame.']
    (build / 'static-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    (PROJECT / 'BUILD-RESULT.md').write_text(f'''# Packet 3B2 build result

NVOCombatCore 0.3.2 / 302 built for Win32 with MSVC 19.51.36257.0, /W4 /permissive- /O2 /MT /Zi, full matching PDB. Build output: out/{build.name}. Zero compiler warnings/errors. Only the two expected NVSE exports; DLL/PDB GUID and age agree. Assembly and new module external-symbol references were inspected. No DLL/game/GECK execution or gameplay test.

DLL SHA256: {evidence['dll_sha256']}

PDB SHA256: {evidence['pdb_sha256']}

PDB GUID: {evidence['codeview_pdb_guid']}, age {evidence['pdb_age']}.

Isolated private PROJ records provide engine-driven constant-speed flight. Native observation and kit batch output are prepared; runtime flight awaits the user capture. Native flight and damage writes remain disabled. Full build log, DLL details and object disassemblies accompany the compiled delivery.
''', encoding='utf-8')
    source = [PROJECT / n for n in ('BUILD.cmd', 'CMakeLists.txt', 'README.md', 'START-HERE.html', 'BUILD-RESULT.md',
              'SDK-BOUNDARY.md', 'sdk-reference.json', 'THIRD-PARTY-NOTICES.md', 'LICENSE-GPL-3.0.txt',
              'LICENSE-ITR-MIT.txt', 'CREDITS-BALLISTX.md', 'src/Exports.def')]
    for folder, pattern in [('include', '*.hpp'), ('src', '*.cpp'), ('config', '*'), ('reference', '*')]:
        source += sorted(p for p in (PROJECT / folder).glob(pattern) if p.is_file())
    installed = [{'path': 'Data/NVSE/Plugins/' + name, 'sha256': digest(build / name)} for name in ('NVOCombatCore.dll', 'NVOCombatCore.pdb')]
    ini = PROJECT / 'config/NVOFlightPreview.ini'
    assert ini.read_bytes() == (ROOT / 'source/combat/step3b2/NVOFlightPreview.ini').read_bytes()
    installed.append({'path': 'Data/NVSE/Plugins/NVOFlightPreview.ini', 'sha256': digest(ini)})
    pilot = ROOT / 'source/combat/step3b2/NVOFlightPilot.esp'
    batch = ROOT / 'source/combat/step3b2/NVOFlightPilot.txt'
    batch.write_bytes(b'')
    installed.extend([{'path': 'Data/NVOFlightPilot.esp', 'sha256': digest(pilot)},
                      {'path': 'NVOFlightPilot.txt', 'sha256': digest(batch), 'runtime_generated': True}])
    manifest = {'packet': '3B2', 'version': '0.3.2', 'plugin_version': 302, 'prepared': '2026-09-15',
                'status': 'Compiled and statically inspected; runtime capture pending', 'installed_by_assistant': False,
                'installation_state_note': 'Packaging-time state; consult separate installation receipt.',
                'assistant_built': True, 'assistant_game_tested': False, 'new_dependencies': ['NVOFlightPilot.esp (six local calibration records, FalloutNV.esm master)'],
                'engine_damage_calculation_hooks': False, 'flight_writes': False, 'damage_replacement_enabled': False,
                'new_native_event_handlers': 0, 'pilot_profiles': 2, 'baseline_profiles': 2, 'isolated_record_flight': True, 'maximum_profiles': 8, 'maximum_sampled_matches_per_capture': 32,
                'maximum_skip_rows_per_capture': 8, 'maximum_config_bytes': 8192, 'process_log_row_limit': 8192,
                'runtime_config_format': 'INI schema 1; JSON is source provenance only',
                'installed_files': installed, 'build_output': str(build.relative_to(PROJECT)),
                'generated_log': 'Game root/NVOCombatCore.log', 'code_license': 'GPL-3.0-only; donor data notices retained separately',
                'source_files': [{'path': p.relative_to(PROJECT).as_posix(), 'sha256': digest(p)} for p in source],
                'limits': 'Private PROJ record flight with native measurement. No native integrator or committed-damage measurement.'}
    (PROJECT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    source.append(PROJECT / 'manifest.json')
    release = ROOT / 'release/NVO-Combat-Packet-3B2-Compiled'
    (release / 'Data/NVSE/Plugins').mkdir(parents=True, exist_ok=True)
    for name in ('NVOCombatCore.dll', 'NVOCombatCore.pdb'):
        shutil.copyfile(build / name, release / 'Data/NVSE/Plugins' / name)
    shutil.copyfile(ini, release / 'Data/NVSE/Plugins/NVOFlightPreview.ini')
    shutil.copyfile(pilot, release / 'Data/NVOFlightPilot.esp')
    shutil.copyfile(batch, release / 'NVOFlightPilot.txt')
    (release / 'RecordPreparation').mkdir(exist_ok=True)
    for name in ('prepare_combat_3b2.py', 'inspect_plugin.py'):
        shutil.copyfile(ROOT / 'tools' / name, release / 'RecordPreparation' / name)
    shutil.copyfile(ROOT / 'source/combat/step3b2/RECORD-AUDIT.json', release / 'RecordPreparation/RECORD-AUDIT.json')
    for p in source:
        target = release / 'Source/NVOCombatCore' / p.relative_to(PROJECT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
        if p.parent == PROJECT and p.name not in ('BUILD.cmd', 'CMakeLists.txt'):
            shutil.copyfile(p, release / p.name)
    (release / 'build-evidence').mkdir(exist_ok=True)
    for name in ('build.log', 'toolchain.log', 'dll-details.txt', 'wrapper-disassembly.txt',
                 'damage-events-disassembly.txt', 'flight-preview-disassembly.txt', 'static-evidence.json'):
        shutil.copyfile(build / name, release / 'build-evidence' / name)
    with zipfile.ZipFile(ROOT / 'release/NVO-Combat-Packet-3B2-Source.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in source:
            z.write(p, 'native/NVOCombatCore/' + p.relative_to(PROJECT).as_posix())
        for name in ('prepare_combat_3b2.py', 'inspect_plugin.py'):
            z.write(ROOT / 'tools' / name, 'tools/' + name)
        z.write(pilot, 'source/combat/step3b2/NVOFlightPilot.esp')
        z.write(ROOT / 'source/combat/step3b2/RECORD-AUDIT.json', 'source/combat/step3b2/RECORD-AUDIT.json')
        for name in ('NVO-Flight-Pilot.json', 'PROVENANCE.json'):
            z.write(ROOT / 'source/combat/step3a' / name, 'source/combat/step3a/' + name)
        z.write(ROOT / 'source/combat/step3b1/NVOFlightPreview.ini', 'source/combat/step3b1/NVOFlightPreview.ini')
    target = ROOT / 'release/NVO-Combat-Packet-3B2-Compiled.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(release.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(release).as_posix())
    print(json.dumps({'compiled_zip': str(target), 'bytes': target.stat().st_size, 'sha256': digest(target),
                      'source_files': len(source), **evidence}, indent=2))


if __name__ == '__main__':
    main()

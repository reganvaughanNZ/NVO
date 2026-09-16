"""Inspect and package packet 3B3A without loading its DLL or running the game."""
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
    assert b'NVOCombatCore 0.3.4 | phase=3B3A' in dll
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
    evidence['manual_review'] = [
        'Both timing bridges save/restore EFLAGS, GP registers and aligned x87/SSE/MXCSR state.',
        'Entry uses saved ECX +24, float argument +40 and return address +36 after pushfd/pushad.',
        'Only sampled calls substitute ReturnObserver; one original tail jump is retained.',
        'Return reserves a continuation slot, preserves callee output state, and uses ret without another argument cleanup.',
        'Original runtime missile function ends in ret 4; timestep bits and original stack layout are retained.',
        'No timing lock crosses the original engine call; parent lock is never acquired by timing.',
        'CurrentHit, NativeObserver, DamageEvents, NativeLog and FlightPreview source bytes unchanged from packet 303.',
        'Only code-pointer instrumentation is written in-process; no game object, projectile state or damage setter.',
        'Shared event counts and identity retirement replace TLS impact markers; same-lifetime overlaps disable that sample.',
        'Timing assembly bridge matches 303; Before/After sampling on other threads awaits runtime acceptance.',
    ]
    previous = ROOT / 'release/NVO-Combat-Packet-3B3-Compiled/Source/NVOCombatCore'
    for n in ('CurrentHit.cpp', 'NativeObserver.cpp', 'DamageEvents.cpp', 'NativeLog.cpp', 'FlightPreview.cpp'):
        assert (previous / 'src' / n).read_bytes() == (PROJECT / 'src' / n).read_bytes(), n
    (build / 'static-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    (PROJECT / 'BUILD-RESULT.md').write_text(f'''# Packet 3B3A build result

NVOCombatCore 0.3.4 / 304, Win32 MSVC 19.51.36257.0, /W4 /permissive- /O2 /MT /Zi. Build: out/{build.name}. Zero compiler warnings/errors. Expected two NVSE exports; matching DLL/PDB GUID and age. New timing entry/return assembly and unchanged copy wrapper inspected. No DLL execution, gameplay or GECK test.

DLL SHA256: {evidence['dll_sha256']}

PDB SHA256: {evidence['pdb_sha256']}

PDB GUID: {evidence['codeview_pdb_guid']}; age {evidence['pdb_age']}.

This packet changes only DLL/PDB. The existing 3B2 test ESP, INI and activation are retained. Native flight/damage state writes remain disabled; one guarded missile dispatch slot supplies observation. Runtime acceptance awaits the user's four-shot/reload capture. Complete compile and object-disassembly evidence accompanies the release.
''', encoding='utf-8')
    source = [PROJECT / n for n in ('BUILD.cmd', 'CMakeLists.txt', 'README.md', 'START-HERE.html', 'BUILD-RESULT.md',
        'SDK-BOUNDARY.md', 'sdk-reference.json', 'THIRD-PARTY-NOTICES.md', 'LICENSE-GPL-3.0.txt',
        'LICENSE-ITR-MIT.txt', 'CREDITS-BALLISTX.md', 'src/Exports.def')]
    for folder, pattern in [('include', '*.hpp'), ('src', '*.cpp'), ('config', '*'), ('reference', '*')]:
        source += sorted(p for p in (PROJECT / folder).glob(pattern) if p.is_file())
    installed = [{'path': 'Data/NVSE/Plugins/' + n, 'sha256': digest(build / n)} for n in ('NVOCombatCore.dll', 'NVOCombatCore.pdb')]
    manifest = {
        'packet': '3B3A', 'version': '0.3.4', 'plugin_version': 304, 'prepared': '2026-09-15',
        'status': 'Compiled and statically inspected; runtime capture pending', 'assistant_built': True,
        'assistant_game_tested': False, 'installed_by_assistant': False,
        'installation_state_note': 'Packaging state. Separate INSTALL-3B3A receipt records the transaction.',
        'new_dependencies': [], 'requires_existing_packet': '3B2 test ESP/INI and activation',
        'new_observer_vtable_slots': [], 'retained_observer_vtable_slots': ['0108FD54'], 'new_native_event_handlers': 0,
        'update_threads': 'caller_thread_with_shared_lifetime_guards', 'cross_thread_event_counters': True, 'maximum_timing_lifetimes_per_capture': 8, 'maximum_steps_per_lifetime': 64, 'maximum_nested_continuations_per_thread': 8,
        'flight_writes': False, 'damage_replacement_enabled': False, 'isolated_record_flight': True,
        'installed_files': installed, 'build_output': str(build.relative_to(PROJECT)),
        'generated_log': 'Game root/NVOCombatCore.log', 'code_license': 'GPL-3.0-only; donor notices retained',
        'source_files': [{'path': p.relative_to(PROJECT).as_posix(), 'sha256': digest(p)} for p in source],
    }
    (PROJECT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    source.append(PROJECT / 'manifest.json')
    release = ROOT / 'release/NVO-Combat-Packet-3B3A-Compiled'
    (release / 'Data/NVSE/Plugins').mkdir(parents=True, exist_ok=True)
    for n in ('NVOCombatCore.dll', 'NVOCombatCore.pdb'):
        shutil.copyfile(build / n, release / 'Data/NVSE/Plugins' / n)
    for p in source:
        target = release / 'Source/NVOCombatCore' / p.relative_to(PROJECT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
        if p.parent == PROJECT and p.name not in ('BUILD.cmd', 'CMakeLists.txt'):
            shutil.copyfile(p, release / p.name)
    (release / 'build-evidence').mkdir(exist_ok=True)
    for n in ('build.log', 'toolchain.log', 'dll-details.txt', 'wrapper-disassembly.txt',
              'flight-timing-disassembly.txt', 'flight-timing-symbols.txt', 'static-evidence.json'):
        shutil.copyfile(build / n, release / 'build-evidence' / n)
    (release / 'Installation').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'tools/install_combat_3b3a.ps1', release / 'Installation/install_combat_3b3a.ps1')
    with zipfile.ZipFile(ROOT / 'release/NVO-Combat-Packet-3B3A-Source.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in source: z.write(p, 'native/NVOCombatCore/' + p.relative_to(PROJECT).as_posix())
        for n in ('package_combat_3b3a.py', 'install_combat_3b3a.ps1'):
            z.write(ROOT / 'tools' / n, 'tools/' + n)
        z.write(ROOT / 'source/combat/step3b3a/HOOK-EVIDENCE.json', 'source/combat/step3b3a/HOOK-EVIDENCE.json')
    target = ROOT / 'release/NVO-Combat-Packet-3B3A-Compiled.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(release.rglob('*')):
            if p.is_file(): z.write(p, p.relative_to(release).as_posix())
    print(json.dumps({'compiled_zip': str(target), 'bytes': target.stat().st_size, 'sha256': digest(target), **evidence}, indent=2))


if __name__ == '__main__':
    main()


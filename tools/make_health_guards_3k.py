"""Derive bounded callable-entry fingerprints from the inspected runtime capture."""
from pathlib import Path
import hashlib, json, struct
ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3k'
CAPTURE = PACKET / 'runtime-20260916-100050'
manifest = json.loads((CAPTURE / 'manifest.json').read_text(encoding='utf-8-sig'))
buffers = {}
for row in manifest['files']:
    data = (CAPTURE / row['filename']).read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    buffers[row['name']] = (int(row['address'], 16), data)
def data_at(name, address, size):
    start, data = buffers[name]
    assert start <= address and address+size <= start+len(data)
    return data[address-start:address-start+size]
def fnv(data):
    result = 14695981039346656037
    for byte in data: result = ((result ^ byte)*1099511628211) & ((1 << 64)-1)
    return result
classes = [
    ('character_tables', 0x1086a6c, 0x10869a4, 0x8805f0, 0x8b0d70, 0x881130, 0x7c754),
    ('creature_tables', 0x10870ac, 0x1086fe4, 0x8d4870, 0x8b0d70, 0x8d49f0, 0x7c748),
    ('player_tables', 0x108aa3c, 0x108a974, 0x93acb0, 0x94c490, 0x93b7a0, 0x7c738)]
targets = []
header = '// Generated from inspected runtime method entries; does not fingerprint all downstream engine code.\n'
header += 'struct ClassSpec { U32 table, owner, get, damage, original, originalRva; };\nconstexpr ClassSpec kClasses[] = {\n'
for name, table, owner, getter, modifier, original, original_rva in classes:
    targets.append(struct.unpack('<I', data_at(name, table+0x3ac, 4))[0])
    assert struct.unpack('<I', data_at(name, owner+0xc, 4))[0] == getter
    assert struct.unpack('<I', data_at(name, owner+0x14, 4))[0] == modifier
    header += '    {'+','.join(f'0x{x:X}' for x in (table, owner, getter, modifier, original, original_rva))+'},\n'
assert len(set(targets)) == 1
header += '};\nstruct CodeSpec { U32 address, size; U64 hash; };\nconstexpr CodeSpec kCode[] = {\n'
rows = []
for name, address, size in [
    ('character_getav', 0x8805f0, 0x70), ('creature_getav', 0x8d4870, 0x28),
    ('player_getav', 0x93acb0, 0x74), ('npc_damage_modifier', 0x8b0d70, 0x3f),
    ('player_damage_modifier', 0x94c490, 0x21), ('creature_damage', 0x8d4a80, 0x2f),
    ('character_damage', 0x881130, 32), ('creature_damage', 0x8d49f0, 32),
    ('player_damage', 0x93b7a0, 32)]:
    data = data_at(name, address, size)
    value = fnv(data)
    header += f'    {{0x{address:X},{size},0x{value:016X}ull}},\n'
    rows.append(dict(address=f'{address:08X}', bytes=size, fnv64=f'{value:016X}'))
header += '};\n'
provider = json.loads((PACKET / 'PROVIDER-FINDINGS.json').read_text())
header += f'constexpr U64 kProviderHash = 0x{provider["thunk_fnv64_preferred_base"]}ull;\n'
header += 'constexpr unsigned kProviderRelocations[] = {'+','.join(map(str, provider['highlow_relocation_offsets']))+'};\n'
(ROOT / 'native/NVOCombatCore/src/ActorValueGuards.inl').write_text(header)
(PACKET / 'ENGINE-GUARDS.json').write_text(json.dumps(dict(capture=str(CAPTURE),
    manifest_sha256=hashlib.sha256((CAPTURE / 'manifest.json').read_bytes()).hexdigest(),
    captured_shared_dispatch=f'{targets[0]:08X}', guards=rows,
    scope='Complete directly called getters/remapper; original damage entry prefixes only. Existing downstream hooks are preserved, not exhaustively fingerprinted.',
    terminal_damage_rule_verified=False), indent=2)+'\n')
print('Generated 9 bounded method guards and provider fingerprint from captured evidence.')

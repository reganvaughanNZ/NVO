"""Export the two NVO filename fixes for the user to compile in GECK."""
import hashlib
import json
from pathlib import Path
import winreg

from inspect_plugin import records, fields

root = Path(__file__).resolve().parents[1]
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    r'SOFTWARE\WOW6432Node\Bethesda Softworks\FalloutNV') as key:
    game = Path(winreg.QueryValueEx(key, 'Installed Path')[0])
plugin = game / 'Data' / 'NVO.esm'
data = plugin.read_bytes()
output = root / 'source' / 'step1'
output.mkdir(parents=True, exist_ok=True)
targets = {'ALTStartQscript', 'ALTQscript'}
manifest = {'plugin': str(plugin), 'plugin_sha256': hashlib.sha256(data).hexdigest(),
            'status': 'Source prepared; user must compile and save in GECK.',
            'scripts': []}

for kind, form, flags, payload in records(data):
    if kind != 'SCPT':
        continue
    parts = dict(fields(payload))
    name = parts.get('EDID', b'').rstrip(b'\x00').decode('cp1252')
    if name not in targets:
        continue
    source = parts['SCTX'].rstrip(b'\x00').decode('cp1252')
    count = source.count('AltStart.esm')
    corrected = source.replace('AltStart.esm', 'NVO.esm')
    corrected = corrected.replace('\r\n', '\n').replace('\r', '\n')
    path = output / f'{name}.txt'
    path.write_bytes(corrected.replace('\n', '\r\n').encode('cp1252'))
    # Update the earlier prepared source copy to match this fresh extraction.
    (root / 'source' / path.name).write_bytes(path.read_bytes())
    manifest['scripts'].append({'editor_id': name, 'form_id_in_file': f'{form:08X}',
                                'filename_occurrences_changed': count,
                                'source_file': str(path)})

if {s['editor_id'] for s in manifest['scripts']} != targets:
    raise RuntimeError('NVO.esm does not contain both expected scripts.')
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))

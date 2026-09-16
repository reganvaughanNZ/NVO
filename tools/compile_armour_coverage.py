"""Compile explicit armour JSON to the bounded runtime text format; no game launch."""
import argparse
from pathlib import Path
from generate_combat_4c_fixtures import REGIONS, load_document, validate

def encode_profiles(document):
    """Return the exact bounded runtime format after validating the whole input."""
    profiles=validate(document)
    lines=['NVO_ARMOUR_COVERAGE_V1','# plugin|local_hex6|revision|equip_mask_hex8|head|torso|left_arm|right_arm|left_leg|right_leg']
    for p in profiles:
        lines.append('|'.join([p['plugin'],f'{int(p["local_id"],16):06X}',str(p['revision']),p['expected_equip_mask'].upper()]+[p['coverage'][r] for r in REGIONS]))
    data=('\n'.join(lines)+'\n').encode('ascii')
    if len(data)>131072: raise ValueError('Runtime profile file exceeds128KiB')
    return data

def compile_profiles(source, output):
    document=load_document(Path(source).read_text(encoding='utf-8-sig'))
    data=encode_profiles(document)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(data)
    print(f'Compiled {len(document["profiles"])} profiles to {output}. No gameplay settings enabled.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('output');args=parser.parse_args()
    compile_profiles(args.source,args.output)

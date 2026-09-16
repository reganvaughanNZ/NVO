"""Read-only saved GECK script review. Writes evidence only inside the project."""
from pathlib import Path
import hashlib, json, struct, argparse
from verify_combat_3i import parse, text, source_key, variables

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'source/combat/step3j'
RELEASE=ROOT/'release/NVO-Combat-Packet-3J-RD-Free'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')

def main():
    cli=argparse.ArgumentParser();cli.add_argument('--plugin',type=Path,default=GAME/'Data/NVO.esm');args=cli.parse_args()
    path=args.plugin;stamp=path.stat();raw=path.read_bytes()
    assert raw==path.read_bytes() and stamp.st_mtime_ns==path.stat().st_mtime_ns
    digest=hashlib.sha256(raw).hexdigest();out=PACK/'captures'/('saved-'+digest[:12]);out.mkdir(parents=True,exist_ok=True)
    (out/'NVO.esm').write_bytes(raw)
    old=parse((RELEASE/'Data/NVO.esm').read_bytes());now=parse(raw)
    masters=[text(v) for t,v in now[0]['parts'] if t=='MAST']
    oldmasters=[text(v) for t,v in old[0]['parts'] if t=='MAST']
    own=len(masters);checks=[]
    for name,local in (('NVOCombatBootstrapScript',0x1941A),('ALTQscript',0x2900),('ALTStartQscript',0x22E1)):
        baseline=next(r for r in old if r['edid']==name)
        expected_path=(PACK/'recompile'/f'{name}.txt') if name!='NVOCombatBootstrapScript' else (RELEASE/'Scripts'/f'{name}.txt')
        expected=source_key(expected_path.read_text())
        candidates=[]
        for r in now:
            if r['kind']!='SCPT' or not (r['edid']==name or r['edid'].startswith(name+'DUPLICATE')):continue
            oldvars=variables(baseline['parts']);newvars=variables(r['parts'])
            candidates.append(dict(editor_id=r['edid'],form=f"{r['fid']:08X}",is_original=r['fid']==(own<<24|local),
                source_matches=source_key(text(r['fs'].get('SCTX',b'')))==expected,
                compiled_bytes=len(r['fs'].get('SCDA',b'')),compiled_changed=r['fs'].get('SCDA')!=baseline['fs'].get('SCDA'),
                variables_preserved=all(newvars.get(n)==v for n,v in oldvars.items()),
                variable_changes={n:dict(before=v,after=newvars.get(n)) for n,v in oldvars.items() if newvars.get(n)!=v}))
        checks.append(dict(script=name,candidates=candidates))
    q=next(r for r in now if r['edid']=='NVOCombatBootstrapScriptQ')
    gmst=lambda rows:{r['edid']:r['parts'] for r in rows if r['kind']=='GMST'}
    original_ok=all(any(c['is_original'] and c['source_matches'] and c['compiled_changed'] and c['variables_preserved'] for c in s['candidates']) for s in checks)
    result=dict(status='original_scripts_updated' if original_ok else 'script_repair_required',sha256=digest,bytes=len(raw),
        masters=masters,masters_unchanged=masters==oldmasters,rd_absent=not (GAME/'Data/RD.esm').exists(),
        rd_not_a_master='rd.esm' not in [m.lower() for m in masters],health_gmsts_preserved=gmst(now)==gmst(old) and len(gmst(old))==5,
        player_override_absent=not any(r['kind']=='NPC_' and r['fid']==7 for r in now),
        bootstrap_link_valid=q['fid']==own<<24|0x1941B and q['fs']['SCRI']==struct.pack('<I',own<<24|0x1941A) and bool(q['fs']['DATA'][0]&1),
        scripts=checks,gameplay_tested_by_assistant=False,
        limitation='Source and compiled-byte checks do not independently prove execution. Additional GECK record changes are recorded separately in changes.json.')
    (out/'script-review.json').write_text(json.dumps(result,indent=2)+'\n')
    (PACK/'SAVED-RECORD-REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

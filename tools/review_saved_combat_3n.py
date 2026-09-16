"""Read-only review of the user's saved 3N GECK records. No game writes."""
from pathlib import Path
import argparse, hashlib, json, re, struct
from verify_combat_3i import parse, text, variables, source_key
from review_3n_save_layout import equivalent

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'source/combat/step3n'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
def sha(b):return hashlib.sha256(b).hexdigest()

def review(path):
    stamp=path.stat(); raw=path.read_bytes()
    assert raw==path.read_bytes() and stamp.st_mtime_ns==path.stat().st_mtime_ns
    old=parse((PACK/'baseline/NVO.esm').read_bytes()); now=parse(raw)
    audit=json.loads((PACK/'SOURCE-AUDIT.json').read_text())
    findings=[]; checks=[]; allowed=set()
    for spec in audit['scripts']:
        name=spec['editor_id']; original=next(r for r in old if r['edid']==name and r['kind']=='SCPT')
        allowed.add(('SCPT',original['fid']))
        candidates=[r for r in now if r['kind']=='SCPT' and (r['edid']==name or r['edid'].startswith(name+'DUPLICATE'))]
        exact=[r for r in candidates if r['edid']==name and r['fid']==original['fid']]
        c={'editor_id':name,'original_form':f'{original["fid"]:08X}',
           'candidates':[{'editor_id':r['edid'],'form':f'{r["fid"]:08X}'} for r in candidates]}
        if len(exact)!=1:
            findings.append(name+': original record missing or duplicated')
        else:
            r=exact[0]; oldvars=variables(original['parts']); newvars=variables(r['parts'])
            c.update(source_matches=source_key(text(r['fs'].get('SCTX',b'')))==source_key((PACK/'Scripts'/f'{name}.txt').read_text()),
                compiled_bytes=len(r['fs'].get('SCDA',b'')),
                compiled_changed=bool(r['fs'].get('SCDA')) and r['fs']['SCDA']!=original['fs'].get('SCDA'),
                compiled_sha256=sha(r['fs'].get('SCDA',b'')),
                script_type_preserved=struct.unpack_from('<H',r['fs']['SCHR'],16)[0]==struct.unpack_from('<H',original['fs']['SCHR'],16)[0],
                prior_variable_slots_types_preserved=all(newvars.get(n)==v for n,v in oldvars.items()),
                variable_differences={n:{'before':v,'after':newvars.get(n)} for n,v in oldvars.items() if newvars.get(n)!=v},
                deleted=bool(r['flags']&0x20))
            for key in ('source_matches','compiled_changed','prior_variable_slots_types_preserved','script_type_preserved'):
                if not c[key]:findings.append(name+': '+key+' failed')
            if c['deleted']:findings.append(name+': record deleted')
        if len(candidates)!=1:findings.append(name+': duplicate script records need review')
        checks.append(c)
    oldmsg=next(r for r in old if r['kind']=='MESG' and r['edid']=='ALTRichKid')
    allowed.add(('MESG',oldmsg['fid']))
    msgs=[r for r in now if r['kind']=='MESG' and r['edid']=='ALTRichKid' and r['fid']==oldmsg['fid']]
    msg_ok=len(msgs)==1 and source_key(text(msgs[0]['fs'].get('DESC',b'')))==source_key((PACK/'ALTRichKid-description.txt').read_text())
    msg_identity=len(msgs)==1 and not msgs[0]['flags']&0x20 and [(t,v) for t,v in msgs[0]['parts'] if t!='DESC']==[(t,v) for t,v in oldmsg['parts'] if t!='DESC']
    if not msg_ok or not msg_identity:findings.append('ALTRichKid: expected description and unchanged other fields not verified')
    masters=lambda rows:[text(v) for t,v in rows[0]['parts'] if t=='MAST']
    gmst=lambda rows:{r['edid']:r['parts'] for r in rows if r['kind']=='GMST'}
    masters_ok=masters(now)==masters(old) and 'rd.esm' not in [m.lower() for m in masters(now)]
    gmst_ok=gmst(now)==gmst(old)
    if not masters_ok:findings.append('Master list changed or RD returned')
    if not gmst_ok:findings.append('User Game Settings changed')
    registrations=[]
    for r in now:
        s=text(r['fs'].get('SCTX',b''))
        if re.search(r'SetEventHandler(?:Alt)?\s+"OnHit"\s+ALTRichKidHit',s,re.I):
            registrations.append({'editor_id':r['edid'],'form':f'{r["fid"]:08X}'})
    if registrations:findings.append('Retired callback still has source registration sites')
    by_old={(r['kind'],r['fid']):r for r in old}; by_now={(r['kind'],r['fid']):r for r in now}
    extra=[]; layout_only=[]
    for key in set(by_old)|set(by_now):
        if key in allowed or key[0]=='TES4':continue
        a=by_old.get(key);b=by_now.get(key)
        if a is None or b is None or a['parts']!=b['parts'] or a['flags']!=b['flags']:
            target=layout_only if equivalent(a,b) else extra
            target.append({'type':key[0],'form':f'{key[1]:08X}','editor_id':(b or a)['edid'],
                'change':'added' if a is None else 'removed' if b is None else 'changed'})
    if extra:findings.append('Additional record changes require review; generated lambdas may be expected')
    result={'packet':'3N','sha256':sha(raw),'scripts':checks,'message_text_correct':msg_ok,
        'message_other_fields_preserved':msg_identity,'masters_preserved_RD_free':masters_ok,
        'game_settings_preserved':gmst_ok,'remaining_registrations':registrations,
        'additional_changes':sorted(extra,key=lambda r:(r['type'],r['form'])),
        'layout_only_changes':sorted(layout_only,key=lambda r:(r['type'],r['form'])),
        'findings':findings,'status':'record_checks_passed_runtime_pending' if not findings else 'review_required',
        'runtime_retirement_verified':False,'damage_replacement':False,
        'limit':'Source and changed compiled bytes are not independent bytecode decompilation or proof of runtime execution.'}
    out=PACK/'captures'/('saved-'+sha(raw)[:12]);out.mkdir(parents=True,exist_ok=True)
    (out/'NVO.esm').write_bytes(raw)
    (out/'REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
    (PACK/'SAVED-RECORD-REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--plugin',type=Path,default=GAME/'Data/NVO.esm');args=cli.parse_args()
    result=review(args.plugin)
    print(json.dumps({'status':result['status'],'sha256':result['sha256'],'findings':result['findings'],
                      'additional_changes':result['additional_changes']},indent=2))

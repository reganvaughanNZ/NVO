"""Read-only review of the user's eventual GECK save. Never modifies game files."""
from pathlib import Path
import hashlib,json,re,struct,argparse
from inspect_plugin import records,fields

ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'source/combat/step3i'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')

def sha(b):return hashlib.sha256(b).hexdigest()
def text(b):return b.rstrip(b'\0').decode('cp1252')
def source_key(s):return '\n'.join(line.strip() for line in re.sub(r'\r+\n?','\n',s).splitlines() if line.strip())
def parse(raw):
    result=[]
    for kind,fid,flags,payload in records(raw):
        parts=list(fields(payload)); fs=dict(parts)
        result.append(dict(kind=kind,fid=fid,flags=flags,parts=parts,fs=fs,edid=text(fs.get('EDID',b''))))
    return result
def variables(parts):
    out={}; pending=None
    for tag,value in parts:
        if tag=='SLSD':pending=(struct.unpack_from('<I',value)[0],value[16])
        if tag=='SCVR' and pending is not None:out[text(value).lower()]=pending
    return out

def verify(path):
    raw=path.read_bytes();stamp=path.stat();assert raw==path.read_bytes() and stamp.st_mtime_ns==path.stat().st_mtime_ns
    now=parse(raw); old=parse((PACKET/'baseline/NVO.esm').read_bytes()); rd=parse((PACKET/'baseline/RD.esm').read_bytes())
    masters=[text(v) for t,v in now[0]['parts'] if t=='MAST']
    oldmasters=[text(v) for t,v in old[0]['parts'] if t=='MAST']
    pending=[]; scripts=[]
    if masters!=oldmasters:pending.append('Master list changed; review remapping before accepting.')
    for name,origin,local in (('NVOCombatBootstrapScript','RD.esm',0xDBE),('ALTQscript','NVO.esm',0x2900),('ALTStartQscript','NVO.esm',0x22E1)):
        matches=[r for r in now if r['kind']=='SCPT' and r['edid']==name]
        baseline=next(r for r in (rd if origin=='RD.esm' else old) if r['kind']=='SCPT' and r['edid']==name)
        expected=(masters.index(origin) if origin in masters else len(masters))<<24|local
        check=dict(script=name,record_count=len(matches),expected_form=f'{expected:08X}')
        if len(matches)!=1:pending.append(name+': missing or duplicated script override')
        else:
            r=matches[0];fs=r['fs'];s=fs.get('SCTX',b'');compiled=fs.get('SCDA',b'');baseline_vars=variables(baseline['parts']);new_vars=variables(r['parts'])
            check.update(form=f"{r['fid']:08X}",identity_correct=r['fid']==expected,
                source_matches=source_key(text(s))==source_key((PACKET/'Scripts'/f'{name}.txt').read_text()),
                compiled_bytes=len(compiled),compiled_changed=bool(compiled) and compiled!=baseline['fs'].get('SCDA',b''),
                compiled_sha256=sha(compiled),prior_variable_indices_types_preserved=all(new_vars.get(n)==v for n,v in baseline_vars.items()))
            for key in ('identity_correct','source_matches','compiled_changed','prior_variable_indices_types_preserved'):
                if not check[key]:pending.append(name+': '+key+' not established')
        scripts.append(check)
    player=[r for r in now if r['kind']=='NPC_' and r['fid']==7]
    staged=parse((PACKET/'Staged/Data/NVO.esm').read_bytes());expect=next(r for r in staged if r['kind']=='NPC_' and r['fid']==7)
    player_check=dict(count=len(player),expected_source='FalloutNV.esm Player00000007')
    if len(player)==1:
        f=player[0]['fs'];player_check.update(full_payload_matches_vanilla=player[0]['parts']==expect['parts'],
            data_matches=f.get('DATA')==expect['fs'].get('DATA'),config_matches=f.get('ACBS')==expect['fs'].get('ACBS'),
            skills_match=f.get('DNAM')==expect['fs'].get('DNAM'),inventory_matches=[v for t,v in player[0]['parts'] if t=='CNTO']==[v for t,v in expect['parts'] if t=='CNTO'])
        if not all(player_check.get(k) for k in ('full_payload_matches_vanilla','data_matches','config_matches','skills_match','inventory_matches')):pending.append('Player override differs from prepared vanilla record; inspect field changes.')
    else:pending.append('Player override missing/duplicated')
    gmst_old={r['edid']:r['parts'] for r in old if r['kind']=='GMST'}
    gmst_now={r['edid']:r['parts'] for r in now if r['kind']=='GMST'}
    gmst_ok=gmst_now==gmst_old and len(gmst_old)==5
    if not gmst_ok:pending.append('User health GMST records changed.')
    live_rd=(GAME/'Data/RD.esm').read_bytes(); rd_ok=sha(live_rd)==sha((PACKET/'baseline/RD.esm').read_bytes())
    if not rd_ok:pending.append('RD.esm changed.')
    # Verify quest reference via actual winning record, whether inherited or overridden.
    rd_index=masters.index('RD.esm') if 'RD.esm' in masters else None
    q=[r for r in now if r['kind']=='QUST' and r['fid']==((rd_index or 0)<<24|0xDBF)]
    if q:
        quest_ok=len(q)==1 and q[0]['fs'].get('SCRI')==struct.pack('<I',rd_index<<24|0xDBE) and bool(q[0]['fs'].get('DATA',b'\0')[0]&1)
    else:
        q=[r for r in parse(live_rd) if r['kind']=='QUST' and r['fid']==0x01000DBF]
        quest_ok=len(q)==1 and q[0]['fs'].get('SCRI')==struct.pack('<I',0x01000DBE) and bool(q[0]['fs'].get('DATA',b'\0')[0]&1)
    if not quest_ok:pending.append('Existing start-enabled bootstrap quest linkage changed.')
    # Report extra semantic record changes for review, rather than silently treating
    # GECK reserialization or newly emitted lambdas as unrelated gameplay edits.
    by_old={(r['kind'],r['fid']):r for r in old};by_now={(r['kind'],r['fid']):r for r in now}
    allowed={('SCPT',len(masters)<<24|0x2900),('SCPT',len(masters)<<24|0x22E1),('NPC_',7),('SCPT',(rd_index or 0)<<24|0xDBE),('TES4',0)}
    extra=[]
    for key in sorted(set(by_old)|set(by_now)):
        a=by_old.get(key);b=by_now.get(key)
        if key in allowed:continue
        if a is None or b is None or a['parts']!=b['parts'] or a['flags']!=b['flags']:
            extra.append(dict(kind=key[0],form=f'{key[1]:08X}',edid=(b or a)['edid'],change='added' if a is None else 'removed' if b is None else 'changed'))
    if extra:pending.append('Additional record changes require inspection (generated lambda scripts may be expected).')
    return dict(source=str(path),sha256=sha(raw),bytes=len(raw),masters=masters,scripts=scripts,player=player_check,
        health_gmsts_preserved=gmst_ok,rd_unchanged=rd_ok,bootstrap_quest_link_valid=quest_ok,additional_changes=extra,
        findings=pending,status='record_checks_passed_runtime_pending' if not pending else 'review_required',
        scope='SCDA presence/change and source/identity checks do not independently decompile or prove runtime execution.',damage_replacement=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plugin',type=Path,default=GAME/'Data/NVO.esm');p.add_argument('--output',type=Path,default=PACKET/'SAVED-RECORD-REVIEW.json');a=p.parse_args()
    result=verify(a.plugin);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

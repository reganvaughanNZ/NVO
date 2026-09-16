"""Audit official xEdit's RD removal output without changing plugin records."""
from pathlib import Path
from collections import Counter
import hashlib, json, struct
from inspect_plugin import records, fields

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'source/combat/step3j'

def sha(b): return hashlib.sha256(b).hexdigest()
def read(path):
    raw=path.read_bytes(); rs=list(records(raw))
    owners=[v.rstrip(b'\0').decode() for t,v in fields(rs[0][3]) if t=='MAST']+['NVO.esm']
    def identity(k,f): return (k, 'HEADER' if k=='TES4' else owners[f>>24], f&0xffffff)
    return raw,owners,{identity(k,f):(fl,list(fields(p))) for k,f,fl,p in rs}

def main():
    before,old,aa=read(PACK/'PRE-CLEAN-NVO.esm')
    after,new,bb=read(PACK/'xedit-work/Data/NVO.esm')
    assert sha(after)=='2c005477f719ff6e2884d7ffeb6c7d547a0146196869999e14b8bff9e560ea98'
    assert new[:-1]==['FalloutNV.esm','DeadMoney.esm','HonestHearts.esm','LonesomeRoad.esm','OldWorldBlues.esm']
    assert aa.keys()==bb.keys() and len(aa)==822
    counts=Counter()
    def remap(v):
        assert len(v)==4
        f=struct.unpack('<I',v)[0]
        if not f: return v
        return struct.pack('<I',new.index(old[f>>24])<<24 | (f&0xffffff))
    def equivalent(a,b):
        assert len(a)==len(b)
        # Comparison only: xEdit, not this function, wrote the references.
        for i,(x,y) in enumerate(zip(a,b)):
            if x!=y:
                assert i>=3 and a[i-3:i]==b[i-3:i]
                assert remap(a[i-3:i+1])==b[i-3:i+1]
                counts['form_index_bytes_remapped']+=1
    def dial(parts,was_old):
        fixed=[]; groups=[]; group=None
        for t,v in parts:
            if t=='QSTI':
                group=[]; groups.append(group)
            elif t not in ('INFC','INFX'): group=None
            if t in ('QSTI','INFC') and was_old: v=remap(v)
            (group if group is not None else fixed).append((t,v))
        return fixed, sorted(groups)
    null_effects=[]
    script_fields=0
    for key,(flags,parts) in aa.items():
        nfl,nparts=bb[key];kind,owner,local=key
        if kind=='TES4': continue
        if flags!=nfl:
            assert key==('ACHR','FalloutNV.esm',0x160845) and flags==0 and nfl==0x400
            counts['xedit_persistent_actor_normalization']+=1
        for tag in ('SCDA','SCTX','SCHR','SLSD','SCVR'):
            assert [v for t,v in parts if t==tag]==[v for t,v in nparts if t==tag],(key,tag)
            if tag=='SCDA':script_fields+=sum(t==tag for t,v in parts)
        if kind=='DIAL':
            assert dial(parts,True)==dial(nparts,False),key
            counts['dialogue_quest_associations_preserved']+=1
            continue
        if kind=='LVLI' and local==0xFE72:
            def ll(ps,old_file):
                values=[]; fixed=[]
                for t,v in ps:
                    if t=='LVLO':
                        values.append(v[:4]+(remap(v[4:8]) if old_file else v[4:8])+v[8:])
                    else:fixed.append((t,v))
                return fixed,sorted(values)
            assert ll(parts,True)==ll(nparts,False)
            counts['leveled_list_sorted_without_entry_changes']+=1
            continue
        if kind=='ALCH' and len(nparts)==len(parts)+2:
            assert nparts[-2:]==[('EFID',bytes(4)),('EFIT',bytes(20))]
            assert not any(t in ('EFID','EFIT') for t,v in parts)
            null_effects.append(dict(parts)['EDID'].rstrip(b'\0').decode())
            nparts=nparts[:-2]
        if kind=='REFR' and local==0xFE6D:
            parts=sorted(parts);nparts=sorted(nparts)
        assert len(parts)==len(nparts),key
        for (t,v),(u,w) in zip(parts,nparts):
            assert t==u,(key,t,u)
            equivalent(v,w)
    assert len(null_effects)==6
    for gmst in (k for k in aa if k[0]=='GMST'): assert aa[gmst]==bb[gmst]
    assert len([k for k in aa if k[0]=='GMST'])==5
    assert ('NPC_','FalloutNV.esm',7) not in bb
    own=len(new)-1
    boot=dict(bb['SCPT','NVO.esm',0x1941A][1])
    quest=dict(bb['QUST','NVO.esm',0x1941B][1])
    assert boot['EDID']==b'NVOCombatBootstrapScript\0'
    assert quest['SCRI']==struct.pack('<I',own<<24|0x1941A) and quest['DATA'][0]&1
    log=(PACK/'xedit-work/xedit-errors.log').read_text(errors='replace')
    assert 'Processed Records: 822, Errors found: 6' in log and '--= All Done =--' in log
    assert not (PACK/'xedit-work/Data/RD.esm').exists()
    assert 'RD.esm' not in log and 'could not be resolved' not in log.lower()
    result=dict(status='RD-free file validation passed; GECK quiet-script compiles and gameplay pending',
        sha256=sha(after),bytes=len(after),masters=new[:-1],records=822,
        existing_records_retained=819,added_records=['NVO.esm:01941A SCPT','NVO.esm:01941B QUST'],
        compiled_script_blocks_preserved=script_fields,health_gmsts_preserved=5,
        player_override_in_NVO=False,bootstrap_start_enabled_and_link_valid=True,
        xedit_version='4.1.5f x64 7C57FA01',reference_check_with_RD_physically_absent=True,
        unresolved_nonnull_references=0,known_donor_empty_effect_records=null_effects,
        serialization_notes=['Six already empty donor effects serialized as NULL EFID/zero EFIT. No effect assigned.',
            'xEdit made the existing Crazed Chem Addict reference 00160845 persistent and moved it to the persistent cell group.',
            'Dialogue quest/INFO associations and leveled-list entry counts survived canonical sorting.'],
        counts=dict(counts),native_version=318,damage_replacement=False)
    (PACK/'RD-REMOVAL-AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()

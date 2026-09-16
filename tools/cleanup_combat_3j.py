"""Promote verified compiled bootstrap; remove exactly three unreferenced copies.

Only writes a workspace staging file. Never recompiles or rewrites SCDA.
"""
from pathlib import Path
import hashlib,json,struct
from inspect_plugin import records,fields
from verify_combat_3i import parse,variables,source_key,text
from prepare_combat_3i import flat_raw

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'source/combat/step3j'
OUT=PACK/'cleanup'
EXPECTED='e75f142b75e8b85ea63917905d287fbbb7407008b1e9de139475d1ae2a504845'
BASE=PACK/'captures/saved-e75f142b75e8/NVO.esm'
REMOVALS={0x05019A14:'NVOCombatBootstrapScriptDUPLICATE000',0x05019A15:'ALTQscriptDUPLICATE000',0x05019A16:'ALTStartQscriptDUPLICATE000'}
TARGET=0x0501941A
def sha(b):return hashlib.sha256(b).hexdigest()
def sub(t,v):
    assert len(v)<65536
    return t.encode()+struct.pack('<H',len(v))+v

def main():
    raw=BASE.read_bytes();assert sha(raw)==EXPECTED
    before=parse(raw);by={r['fid']:r for r in before};assert len(by)==len(before)
    initial=parse((ROOT/'release/NVO-Combat-Packet-3J-RD-Free/Data/NVO.esm').read_bytes())
    assert [v for t,v in before[0]['parts'] if t=='MAST']==[v for t,v in initial[0]['parts'] if t=='MAST']
    for fid,name in REMOVALS.items():
        assert by[fid]['kind']=='SCPT' and by[fid]['edid']==name and by[fid]['flags']==0
    for row in before:
        for tag,value in row['parts']:
            for fid,name in REMOVALS.items():
                assert struct.pack('<I',fid) not in value,('Incoming possible reference',row['edid'],tag,name)
            if row['fid'] not in REMOVALS and tag in ('SCTX','FULL','EDID'):
                assert not any(name.lower().encode() in value.lower() for name in REMOVALS.values())
    for name in ('ALTQscript','ALTStartQscript'):
        r=next(r for r in before if r['edid']==name);old=next(r for r in initial if r['edid']==name)
        assert source_key(text(r['fs']['SCTX']))==source_key((PACK/'recompile'/f'{name}.txt').read_text())
        assert r['fs']['SCDA']!=old['fs']['SCDA'] and all(variables(r['parts']).get(n)==v for n,v in variables(old['parts']).items())
    original=by[TARGET];compiled=by[0x05019A14]
    assert original['edid']=='NVOCombatBootstrapScript' and original['flags']==0
    assert source_key(text(compiled['fs']['SCTX']))==source_key((ROOT/'release/NVO-Combat-Packet-3J-RD-Free/Scripts/NVOCombatBootstrapScript.txt').read_text())
    assert all(variables(compiled['parts']).get(n)==v for n,v in variables(original['parts']).items())
    assert not any(t=='SCRO' for t,v in compiled['parts'])
    replacement=b''.join(sub(t,original['fs']['EDID'] if t=='EDID' else v) for t,v in compiled['parts'])
    changed=[];deleted=[];groups=0
    def rewrite(start,end):
        nonlocal groups
        output=bytearray();pos=start
        while pos<end:
            header=bytearray(raw[pos:pos+24]);size=struct.unpack_from('<I',header,4)[0]
            if header[:4]==b'GRUP':
                groups+=1;body=rewrite(pos+24,pos+size)
                struct.pack_into('<I',header,4,len(body)+24);output+=header+body;pos+=size
                continue
            fid=struct.unpack_from('<I',header,12)[0];body=raw[pos+24:pos+24+size]
            if fid in REMOVALS:
                deleted.append(fid);pos+=24+size;continue
            if fid==TARGET:
                body=replacement;struct.pack_into('<I',header,4,len(body));changed.append(fid)
            elif header[:4]==b'TES4':
                body=bytearray(body);assert body[:4]==b'HEDR'
                count=struct.unpack_from('<I',body,10)[0]
                struct.pack_into('<I',body,10,count-3)
            output+=header+body;pos+=24+size
        assert pos==end
        return bytes(output)
    cleaned=rewrite(0,len(raw));assert set(deleted)==set(REMOVALS) and changed==[TARGET]
    a={(k,f):r for k,f,r in flat_raw(raw)};b={(k,f):r for k,f,r in flat_raw(cleaned)}
    assert a.keys()-b.keys()=={('SCPT',fid) for fid in REMOVALS} and not b.keys()-a.keys()
    unchanged=0
    for key,value in b.items():
        if key not in (('TES4',0),('SCPT',TARGET)):assert a[key]==value;unchanged+=1
    oldheader=bytearray(a['TES4',0]);newheader=b['TES4',0]
    struct.pack_into('<I',oldheader,34,struct.unpack_from('<I',oldheader,34)[0]-3);assert bytes(oldheader)==newheader
    after=parse(cleaned);assert len(after)==822
    assert struct.unpack_from('<I',after[0]['fs']['HEDR'],4)[0]==len(after)-1+groups
    boot=next(r for r in after if r['fid']==TARGET)
    assert boot['fs']['SCDA']==compiled['fs']['SCDA']
    assert [(t,v) for t,v in boot['parts'] if t!='EDID']==[(t,v) for t,v in compiled['parts'] if t!='EDID']
    assert all(r['fid'] not in REMOVALS for r in after)
    (OUT/'Data').mkdir(parents=True,exist_ok=True);(OUT/'Data/NVO.esm').write_bytes(cleaned)
    audit=dict(before_sha256=sha(raw),after_sha256=sha(cleaned),before_bytes=len(raw),after_bytes=len(cleaned),
        original_records_byte_identical_except_bootstrap_and_header=unchanged,
        deleted=[dict(form=f'{f:08X}',editor_id=n) for f,n in REMOVALS.items()],
        bootstrap_original_identity_retained=f'{TARGET:08X}',compiled_bootstrap_bytecode_unchanged_from_user_copy=True,
        bootstrap_compiled_bytes=len(boot['fs']['SCDA']),records_before=len(before),records_after=len(after),
        incoming_duplicate_references_found=0,master_list_unchanged=True,header_change='HEDR record/group count -3 only; next FormID retained',
        native_changes=False,gameplay_tested=False)
    (OUT/'CLEANUP-AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))

if __name__=='__main__':main()

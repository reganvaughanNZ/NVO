"""Carry only RD's bootstrap into a workspace NVO copy; xEdit cleans the master."""
from pathlib import Path
import hashlib,json,struct
from inspect_plugin import records,fields

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'source/combat/step3j'
DATA=OUT/'xedit-work/Data'

def sub(t,v):return t.encode()+struct.pack('<H',len(v))+v
def record(k,f,p):return struct.pack('<4sIIIIHH',k.encode(),len(p),0,f,0,15,0)+p
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    nvo=(OUT/'baseline/NVO.esm').read_bytes();rd=(OUT/'baseline/RD.esm').read_bytes()
    assert sha(nvo)=='2bb53410287c1c409a0bbb9b51ef38bf14bba2a4e3376f23b5cfc9f73fc0028d'
    assert sha(rd)=='9498ee5bee4119ec289b8f88af83e3bbd0ff2e2ec57e45809f3e18dd8b139bc3'
    original=list(records(nvo));header=dict(fields(original[0][3]))
    masters=[v.rstrip(b'\0').decode() for t,v in fields(original[0][3]) if t=='MAST']
    assert masters.index('RD.esm')==9 and len(masters)==11
    own=len(masters);first=struct.unpack_from('<I',header['HEDR'],8)[0]
    assert first==0x1941A and all((f&0xFFFFFF)<first for k,f,fl,p in original if f>>24==own)
    scriptid=own<<24|first;questid=scriptid+1
    additions={};audit=[]
    for kind,fid,flags,payload in records(rd):
        fs=list(fields(payload));name=dict(fs).get('EDID',b'').rstrip(b'\0').decode('cp1252')
        if name not in ('NVOCombatBootstrapScript','NVOCombatBootstrapScriptQ'):continue
        assert flags==0
        if kind=='SCPT':
            assert not any(t=='SCRO' for t,v in fs)
            newfid=scriptid;newpayload=payload
        else:
            assert kind=='QUST';newfid=questid
            assert dict(fs)['SCRI']==struct.pack('<I',0x01000DBE)
            newpayload=b''.join(sub(t,struct.pack('<I',scriptid) if t=='SCRI' else v) for t,v in fs)
        additions[kind]=record(kind,newfid,newpayload)
        audit.append(dict(kind=kind,editor_id=name,origin=f'RD.esm:{fid&0xFFFFFF:06X}',destination=f'NVO.esm:{newfid&0xFFFFFF:06X}',compiled_script_unchanged=kind=='SCPT'))
    assert set(additions)=={'SCPT','QUST'}
    # xEdit may remove other unused declarations too. Keep every original
    # official DLC explicitly active when deploying, including the preorder packs
    # whose records use FalloutNV form identities. Do not invent fake references.
    output=bytearray();pos=0;done=[]
    while pos<len(nvo):
        h=bytearray(nvo[pos:pos+24]);size=struct.unpack_from('<I',h,4)[0]
        if h[:4]==b'GRUP':
            body=nvo[pos+24:pos+size];kind=h[8:12].decode()
            if struct.unpack_from('<I',h,12)[0]==0 and kind in additions:
                body+=additions[kind];done.append(kind);struct.pack_into('<I',h,4,len(body)+24)
            output+=h+body;pos+=size
        else:
            assert pos==0 and h[:4]==b'TES4'
            body=bytearray(nvo[pos+24:pos+24+size]);assert body[:4]==b'HEDR'
            struct.pack_into('<I',body,10,struct.unpack_from('<I',body,10)[0]+2)
            struct.pack_into('<I',body,14,first+2)
            output+=h+body;pos+=size+24
    assert set(done)==set(additions) and len(done)==2
    prepared=bytes(output);after=list(records(prepared));assert len(after)==len(original)+2
    by={(k,f):(fl,p) for k,f,fl,p in after}
    for k,f,fl,p in original:
        if k!='TES4':assert by[k,f]==(fl,p)
    for k,f,fl,p in after:
        list(fields(p))
        if k!='TES4':
            assert f>>24!=9
            for _,v in fields(p):
                for local in (0xADD,0xADE,0xADF,0xDBE,0xDBF):assert struct.pack('<I',0x09000000|local) not in v
    (OUT/'PRE-CLEAN-NVO.esm').write_bytes(prepared)
    (DATA/'NVO.esm').write_bytes(prepared)
    (OUT/'PREPARATION.json').write_text(json.dumps(dict(baseline_sha256=sha(nvo),pre_clean_sha256=sha(prepared),migrated=audit,official_dlc_to_keep_active=[m for m in masters if m!='RD.esm'],existing_records_preserved=True,master_cleanup='Pending official xEdit SortAndClean; no hand-edited MAST removal.',discarded_rd_records=['Player override','PlayerHelp','ReganGear','Regan perk','PowerArmorTraining override']),indent=2)+'\n')
    print(json.dumps(dict(prepared_sha256=sha(prepared),migrated=audit),indent=2))

if __name__=='__main__':main()

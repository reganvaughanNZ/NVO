"""Freeze native317 and derive compatibility fingerprints from the installed ITR PE."""
from pathlib import Path
import hashlib,json,re,shutil,struct
ROOT=Path(__file__).resolve().parents[1]
NATIVE=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3h'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=PACKET/'baseline-317'
if not (baseline/'manifest.json').exists():
    rows=[]
    paths=[p for folder in ('src','include','config') for p in (NATIVE/folder).glob('*') if p.is_file()]
    paths += [NATIVE/n for n in ('BUILD.cmd','CMakeLists.txt') if (NATIVE/n).is_file()]
    for p in paths:
        rel=p.relative_to(NATIVE);q=baseline/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
        rows.append(dict(path=rel.as_posix(),sha256=sha(p),bytes=p.stat().st_size))
    (baseline/'manifest.json').write_text(json.dumps(dict(version=317,files=rows),indent=2)+'\n')
p=GAME/'Data/NVSE/Plugins/itr-nvse.dll';b=p.read_bytes()
assert sha(p)=='31f5abad415750141906efbe810a32eb35ac714335e65e806215655c72c7fc0c'
pe=struct.unpack_from('<I',b,0x3c)[0];opt=pe+24
assert struct.unpack_from('<H',b,pe+4)[0]==0x14c
count=struct.unpack_from('<H',b,pe+6)[0];opsize=struct.unpack_from('<H',b,pe+20)[0]
imagebase=struct.unpack_from('<I',b,opt+28)[0];sections=[]
for i in range(count):
    off=opt+opsize+40*i;vs,rva,rs,raw=struct.unpack_from('<IIII',b,off+8);sections.append((rva,max(vs,rs),raw))
def offset(rva):
    for start,size,raw in sections:
        if start<=rva<start+size:return raw+rva-start
    raise ValueError(rva)
rr,sz=struct.unpack_from('<II',b,opt+96+5*8);pos=offset(rr);end=pos+sz;relocations=[]
while pos<end:
    page,size=struct.unpack_from('<II',b,pos);assert size>=8 and size%2==0
    for value in struct.unpack_from('<'+'H'*((size-8)//2),b,pos+8):
        if value>>12==3:relocations.append(page+(value&0xfff))
        else:assert value>>12==0
    pos+=size
dis=(PACKET/'inspection/itr-disassembly.txt').read_text(encoding='utf-8-sig')
sites=[0x87C4DA,0x89A738,0x8B91E1,0x9B0503,0x9C1E96,0x9CBDE8]
rows=[]
for n,site in enumerate(sites):
    match=re.search(r'^OnPreDamageHandler::Hook_HitMe<'+str(n)+r'>:\n(.*?)(?=^\S|\Z)',dis,re.M|re.S);assert match
    ins=re.findall(r'^  ([0-9A-F]{8}): ((?:[0-9A-F]{2} )*[0-9A-F]{2})\s',match[1],re.M)
    start=int(ins[0][0],16)-imagebase;stop=int(ins[-1][0],16)-imagebase+len(ins[-1][1].split())
    body=b[offset(start):offset(start)+stop-start];assert body[-3:]==b'\xc2\x08\x00' and len(body)==127
    assert body[5:7]==b'\x8b\x3d';original_rva=struct.unpack_from('<I',body,7)[0]-imagebase
    reloc=[x-start for x in relocations if start<=x<stop]
    h=14695981039346656037
    for v in body:h=((h^v)*1099511628211)&((1<<64)-1)
    rows.append(dict(index=n,site=f'{site:08X}',thunk_rva=start,size=len(body),original_rva=original_rva,relocations=reloc,fnv64=f'{h:016X}'))
    (PACKET/'inspection'/f'ITR-HitMe-{n}.txt').write_text(match.group(0))
source=Path(r'C:\Users\regan\Desktop\NVO Mod References (Open Source)\itr-nvse-master\itr-nvse\handlers\OnPreDamageHandler.cpp')
result=dict(provider_sha256=sha(p),provider_source=str(source),provider_source_sha256=sha(source),preferred_base=imagebase,timestamp=struct.unpack_from('<I',b,pe+8)[0],image_size=struct.unpack_from('<I',b,opt+56)[0],calls=rows,read_only_offline_inspection=True,full_game_damage_contract_verified=False)
(PACKET/'ENGINE-FINDINGS.json').write_text(json.dumps(result,indent=2)+'\n')
header='// Compatibility fingerprints of inspected ITR 2.2.2 functions; no executable bytes.\n'
header+='struct HookSpec { U32 site, rva, originalRva; U64 hash; };\nconstexpr HookSpec kSpecs[] = {\n'
for row in rows:header+=f"    {{0x{row['site']},0x{row['thunk_rva']:X},0x{row['original_rva']:X},0x{row['fnv64']}ull}},\n"
header+='};\n'
assert all(x['relocations']==rows[0]['relocations'] for x in rows)
header+='constexpr unsigned kRelocations[] = {'+','.join(str(x) for x in rows[0]['relocations'])+'};\n'
(NATIVE/'src/HitTransactionGuards.inl').write_text(header)
print(json.dumps(result,indent=2))

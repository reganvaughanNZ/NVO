"""Review archived 3H call scopes; never infer committed damage from callbacks."""
from pathlib import Path
import argparse,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
def audit(folder):
    folder=folder.resolve();assert folder.is_relative_to(ROOT/'source/combat')
    raw=(folder/'NVOCombatCore.log').read_bytes();meta=json.loads((folder/'capture.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==meta['sha256']
    parsed=[]
    for line_no,line in enumerate(raw.decode().splitlines(),1):
        if line.startswith('HIT_TX'):
            parsed.append(dict(line=line_no,kind=line.split()[0],fields=dict(re.findall(r'(\w+)=([^ ]+)',line))))
    get=lambda name:[r for r in parsed if r['kind']==name]
    begins=get('HIT_TX_BEGIN');stages=get('HIT_TX_STAGE');returns=get('HIT_TX_RETURN')
    byid={r['fields']['tx']:r for r in begins};assert len(byid)==len(begins)
    endid={r['fields']['tx']:r for r in returns};assert len(endid)==len(returns)
    checks=[]
    for tx,b in byid.items():
        f=b['fields'];ss=[r for r in stages if r['fields']['tx']==tx];end=endid.get(tx)
        assert all(r['fields']['session']==f['session'] and r['line']>b['line'] for r in ss)
        if end:assert end['fields']['session']==f['session'] and end['line']>max([b['line']]+[r['line'] for r in ss])
        exact=[r for r in ss if r['fields'].get('association')=='exact_input_pointer']
        for r in exact:
            for k in ('pointer_equal','identity_match','process_match'):assert r['fields'][k]=='1'
            assert r['fields']['tainted']=='0'
        checks.append(dict(tx=tx,session=f['session'],lifetime=f['lifetime'],valid=f['valid'],
            linked=f['linked'],site=f['site'],receiver=f['receiver'],weapon=f['weapon'],carrier=f['carrier'],
            ammo=f['ammo'],main_thread=f['main_thread'],stages=[r['fields']['stage'] for r in ss],
            returned=bool(end),exact_copy_count=len(exact),committed_loss='unverified'))
    errors=[r for r in parsed if r['kind'] in ('HIT_TX_DISABLED','HIT_TX_PROTECTION_RESTORE_FAILED')]
    out=dict(capture=meta,begin_count=len(begins),return_count=len(returns),stages=stages,checks=checks,
        summaries=get('HIT_TX_SUMMARY'),errors=errors,readiness=get('HIT_TX_READY'),
        installation=get('HIT_TX_HOOK_READY'),coverage_note='Detailed records are capped; summaries and unsupported stages need human review.',
        gameplay_acceptance='not_automatically_granted',damage_applications='unverified')
    (folder/'transactions-audit.json').write_text(json.dumps(out,indent=2)+'\n')
    return out
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);a=parser.parse_args();r=audit(a.folder)
    print(json.dumps({k:r[k] for k in ('begin_count','return_count','checks','summaries','errors')},indent=2))

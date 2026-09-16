"""Compact read-only summary of Packet 3K logs; no damage-acceptance verdict."""
from pathlib import Path
import argparse, hashlib, json, re

parser=argparse.ArgumentParser()
parser.add_argument('log',type=Path)
parser.add_argument('--limit',type=int,default=24)
args=parser.parse_args()
data=args.log.read_bytes();lines=data.decode('utf-8',errors='replace').splitlines()
begins={};hits={};rows=[];summaries=[];issues=[];ready=[];lifecycle=[]
for line in lines:
    fields=dict(re.findall(r'(\w+)=([^ ]+)',line))
    if line.startswith('LIFECYCLE '):lifecycle.append(line)
    elif line.startswith(('AV_APPLY_HOOK_READY ','AV_APPLY_READY ','AV_APPLY_DISABLED ')):ready.append(line)
    elif line.startswith('HIT_TX_DATA '):hits[(fields.get('session'),fields.get('tx'))]=fields
    elif line.startswith('AV_APPLY_BEGIN '):
        key=(fields.get('session'),fields.get('call'))
        if key in begins:issues.append(dict(problem='duplicate detailed begin',session=key[0],call=key[1]))
        begins[key]=fields
    elif line.startswith('AV_APPLY_END '):
        key=(fields.get('session'),fields.get('call'));before=begins.pop(key,None)
        if before is None:issues.append(dict(problem='detailed end without begin',session=key[0],call=key[1]))
        hit=hits.get((fields.get('session'),fields.get('tx')),{}) if fields.get('scope_match')=='1' else {}
        result={k:fields.get(k) for k in ('session','call','tx','scope_match','receiver','av','effective_av','valid','nested','tainted','net_current','net_damage')}
        result.update(requested=before.get('requested') if before else None,
                      hit_input_health=hit.get('health'),hit_region=hit.get('region'),
                      measurement='net over provider call; do not add parent and child intervals')
        rows.append(result)
    elif line.startswith('AV_APPLY_SUMMARY '):summaries.append(fields)
result=dict(path=str(args.log.resolve()),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),
    lifecycle=lifecycle,ready=ready,completed_detailed_calls=len(rows),
    invalid=sum(r['valid']!='1' for r in rows),nested=sum(r['nested'] not in ('0',None) for r in rows),
    pending_detailed_calls=[dict(session=s,call=c) for s,c in begins],issues=issues,summaries=summaries,
    calls=rows[:max(0,args.limit)],omitted_call_details=max(0,len(rows)-max(0,args.limit)),
    verdict='Observation summary only. No live calls means gameplay is untested; pending returns may reflect lifecycle boundaries.')
print(json.dumps(result,indent=2))

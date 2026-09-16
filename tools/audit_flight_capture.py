"""Reusable immutable-log audit. Reports evidence; never grants a gameplay pass."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import math
import re

ROOT=Path(__file__).resolve().parents[1]

def audit(folder):
    folder=folder.resolve();assert folder.is_relative_to(ROOT/'source/combat')
    meta=json.loads((folder/'capture.json').read_text())
    raw=(folder/'NVOCombatCore.log').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==meta['sha256']
    lines=raw.decode().splitlines()
    fields=lambda s:dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)',s))
    rows=[(s.split()[0],fields(s)) for s in lines if s]
    get=lambda n:[r for label,r in rows if label==n]
    events=[(s.split()[3],fields(s)) for s in lines if s.startswith('EVENT ')]
    creates=[r for n,r in events if n=='CREATE']
    impacts=[r for n,r in events if n=='IMPACT']
    destroys=[r for n,r in events if n=='DESTROY']
    selections=get('FLIGHT_SELECT');previews=[r for r in get('FLIGHT_PREVIEW') if r['phase']=='create']
    assert len(selections)==len(previews)==len(creates)>0
    for s,p,c in zip(selections,previews,creates):
        for key in ('session','source','weapon','ammo'):assert s[key]==p[key]==c[key],key
        assert s['replacement']==p['projectile_base'] and s['profile']==p['profile']
        assert p['lifetime']==c['lifetime'] and p['projectile']==c['projectile']
        assert c['tracked']==c['ammo_known']=='1'
    creation={(c['session'],c['lifetime']):c for c in creates}
    for r in get('IMPACT_STEP'):
        c=creation[(r['session'],r['lifetime'])]
        for key in ('projectile','source','weapon','ammo'):assert r[key]==c[key],key
        assert r['observer_writes']=='0'
    for r in get('FLIGHT_RANGE'):
        c=creation[(r['session'],r['lifetime'])]
        for key in ('projectile','source','weapon','ammo'):assert r[key]==c[key],key
        assert r['cause']=='unverified' and r['observer_writes']=='0'
    for h in get('HIT_CONTEXT'):
        if h.get('linked')!='1':continue
        c=creation[(h['session'],h['lifetime'])]
        assert h['carrier']==c['projectile'] and h['weapon']==c['weapon']
        assert h['ammo']==h['creation_ammo']==c['ammo']
    steps={(r['session'],r['lifetime'],r['step']):r for r in get('PHYSICS_STEP')}
    vec=lambda s:tuple(map(float,s.strip('()').split(',')))
    comparisons=[]
    for a in get('PHYSICS_ACTUAL'):
        k=(a['session'],a['lifetime'],a['step']);step=steps[k]
        error=math.dist(vec(step['world_delta']),vec(a['actual_delta']))
        matched=error<=float(a['tolerance']) and float(a['position_error'])<=float(a['tolerance'])
        if a['matched']=='1':assert matched,k
        comparisons.append(dict(session=k[0],lifetime=k[1],step=k[2],phase=a['phase'],
            logged_matched=a['matched']=='1',recomputed_matched=matched,
            vector_error=float(a['vector_error']),position_error=float(a['position_error']),
            tolerance=float(a['tolerance'])))
    summary=[(n,r) for n,r in rows if n=='SUMMARY' or n.endswith('_SUMMARY')]
    errors=[]
    boundary_open_counts=[]
    zero_keys=set('unmatched reused_live_address overflow read_failures open_lifetimes invalid_contexts open accounting_unpaired invalid retired_during_update overlap_lifetimes thread_changes nesting_limit identity_mismatches open_samples damage_replacement timing_writes damage_writes observer_writes move_untracked accounting_untracked report_write_failures reports_omitted_by_limit log_write_failures'.split())
    for n,r in summary:
        for key in zero_keys.intersection(r):
            if r[key]!='0':
                observation=dict(row=n,session=r.get('session'),field=key,value=r[key],reason=r.get('reason'))
                if key in ('open_lifetimes','open','open_samples') and r.get('reason')=='pre_load_game':
                    # Preserve the evidence, but distinguish a reload with a live
                    # projectile from an exit leak. The reviewer must check reset.
                    boundary_open_counts.append(observation)
                else:errors.append(observation)
    corrections={(r['session'],r['lifetime'],r['step']):r for r in get('PHYSICS_TERRAIN_REJECT_DEFAULT')}
    corrected_results={(r['session'],r['lifetime'],r['step']):r for r in get('PHYSICS_TERRAIN_REJECT_DEFAULT_VERIFIED')}
    correction_pairs=[]
    for k in corrections.keys() & corrected_results.keys():
        c=corrections[k];v=corrected_results[k]
        valid=(c['query_ok']=='0' and float(c['default_z'])==-2048 and float(c['prevented_raise'])>30
            and c['stack_height_write']==c['result_preserved']=='1' and c['position_write']=='0'
            and float(c['candidate_error'])<=float(c['tolerance'])
            and float(v['vector_error'])<=float(v['tolerance']) and float(v['position_error'])<=float(v['tolerance'])
            and abs(float(c['candidate_z'])-float(v['actual_z']))<=float(v['tolerance']))
        assert valid,k
        correction_pairs.append(dict(session=k[0],lifetime=k[1],step=k[2],correction=c,verification=v))
    correction_pairs.sort(key=lambda c:tuple(int(c[k]) for k in ('session','lifetime','step')))
    # Keep endpoint and contact comparisons separate: BeforeAccounting can see
    # the full step endpoint, while the later callback moves to the contact.
    # Recomputed values are observations, never an automatic speed acceptance.
    impact_geometry_checks=[]
    callbacks={(r['session'],r['lifetime']):r for r in get('IMPACT_CALLBACK')}
    for g in get('IMPACT_GEOMETRY'):
        start,expected,position,contact,delta=[vec(g[k]) for k in
            ('start','expected','position','contact','accounting_delta')]
        length2=sum(x*x for x in expected);tol=float(g['tolerance'])
        if not length2 or not all(math.isfinite(x) for v in
                (start,expected,position,contact,delta) for x in v):continue
        to_contact=tuple(c-s for c,s in zip(contact,start))
        fraction=sum(c*e for c,e in zip(to_contact,expected))/length2
        off_chord=math.dist(to_contact,tuple(fraction*x for x in expected))
        endpoint_error=math.dist(position,tuple(s+e for s,e in zip(start,expected)))
        accounting_error=math.dist(delta,expected)
        c=callbacks.get((g['session'],g['lifetime']))
        impact_geometry_checks.append(dict(session=g['session'],lifetime=g['lifetime'],
            step=g['step'],tolerance=tol,chord_fraction=fraction,off_chord_units=off_chord,
            contact_within_chord_tolerance=0<=fraction<=1 and off_chord<=tol,
            endpoint_error=endpoint_error,accounting_error=accounting_error,
            endpoint_matches=endpoint_error<=tol,accounting_matches=accounting_error<=tol,
            position_contact_gap=math.dist(position,contact),
            callback_contact_change=math.dist(vec(c['contact']),contact) if c and 'contact' in c else None,
            callback_position_contact_gap=math.dist(vec(c['position']),vec(c['contact']))
                if c and 'position' in c and 'contact' in c else None,
            model_candidate_evaluated=False))
    terrain=get('PHYSICS_TERRAIN_SUMMARY');routes=get('PHYSICS_ROUTE_SUMMARY')
    result=dict(capture=meta,header=lines[0],normal_exit=lines[-1]=='LIFECYCLE exit_game',
        loaded_sessions=sum(s.startswith('LIFECYCLE post_load_game success=1') for s in lines),
        selections=len(selections),created=len(creates),impacts=len(impacts),destroyed=len(destroys),
        identities_corroborated=len(creates),profiles=dict(Counter(s['profile'] for s in selections)),
        hits=get('HIT_CONTEXT'),impact_events=impacts,
        range_observations=get('FLIGHT_RANGE'),range_summaries=get('FLIGHT_RANGE_SUMMARY'),
        impact_steps=get('IMPACT_STEP'),impact_geometry=get('IMPACT_GEOMETRY'),
        impact_velocity=get('IMPACT_VELOCITY'),impact_models=get('IMPACT_MODEL'),
        impact_callbacks=get('IMPACT_CALLBACK'),impact_summaries=get('IMPACT_SUMMARY'),
        impact_boundaries=get('IMPACT_BOUNDARY'),impact_coverage_summaries=get('IMPACT_COVERAGE_SUMMARY'),
        impact_hits=get('IMPACT_HIT'),impact_hit_models=get('IMPACT_HIT_MODEL'),
        impact_hit_positions=get('IMPACT_HIT_POSITION'),impact_hit_summaries=get('IMPACT_HIT_SUMMARY'),
        impact_geometry_checks=impact_geometry_checks,
        destroy_travel=[r for r in get('FLIGHT_TRAVEL') if r['phase']=='destroy'],
        terrain_eligible=sum(int(r['eligible_queries']) for r in terrain),
        terrain_failed=sum(int(r['failed_queries']) for r in terrain),
        terrain_corrected=sum(int(r['corrected']) for r in terrain),
        terrain_verified=sum(int(r['verified']) for r in terrain),
        reported_baselines=sum(int(r['baselines_verified']) for r in routes),
        reported_edited_matches=sum(int(r['applied_verified']) for r in routes),
        reported_mismatches=sum(int(r['mismatches']) for r in routes),
        detailed_edited_matches=sum(c['phase']=='apply' and c['logged_matched'] for c in comparisons),
        detailed_baselines=sum(c['phase']=='baseline' and c['logged_matched'] for c in comparisons),
        rejection_rows=get('PHYSICS_REJECT'),disabled_rows=get('PHYSICS_DISABLED'),
        summary_errors=errors,boundary_open_counts=boundary_open_counts,
        correction_pairs=correction_pairs,
        unpaired_correction_details=sorted(corrections.keys()-corrected_results.keys()),
        unpaired_verification_details=sorted(corrected_results.keys()-corrections.keys()),
        comparisons=comparisons,summaries=summary,
        gameplay_acceptance='requires explicit review; this utility only audits logged evidence',game_modified=False)
    (folder/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('capture',type=Path);args=p.parse_args()
    r=audit(args.capture)
    print(json.dumps({k:r[k] for k in ('normal_exit','loaded_sessions','created','impacts','destroyed',
        'profiles','terrain_eligible','terrain_failed','terrain_corrected','reported_edited_matches',
        'reported_baselines','reported_mismatches','detailed_edited_matches','detailed_baselines',
        'summary_errors')},indent=2))

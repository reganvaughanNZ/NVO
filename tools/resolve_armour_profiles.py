"""Resolve NVO authoring tags to exact 4D profiles. No engine/JIP/KEYWORDS calls.

All validation finishes before output is opened. Ambiguity, typos and schema
errors reject the export; no numeric protection or gameplay authority is added.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from compile_armour_coverage import encode_profiles
from generate_combat_4c_fixtures import REGIONS, load_document, validate

MAX_SOURCE_BYTES=1048576
MAX_PROFILES=256
MAX_RULES=512
MAX_TAGS=32
TOP={'schema_version','policy','regions','profile_definitions','keyword_rules','bindings','record_overrides'}

def exact(value,fields,label):
    if not isinstance(value,dict) or set(value)!=fields:raise ValueError(label+': unexpected or missing fields')

def bounded(value,maximum,label,minimum=0):
    if not isinstance(value,list) or not minimum<=len(value)<=maximum:raise ValueError(label+': count/type')

def nonempty(value,label):
    if not isinstance(value,str) or not value.strip():raise ValueError(label+': empty/type')

def tag_key(value):
    if not isinstance(value,str) or not re.fullmatch(r'NVO_[A-Za-z0-9_]{1,59}',value,re.I):raise ValueError('keyword: expected NVO_ namespace and at most63 ASCII identifier characters')
    return value.lower()

def doc(policy,profiles):return dict(schema_version=1,policy=policy,regions=REGIONS.copy(),profiles=profiles)

def profile(definition,key,mask,identifier,rationale=None):
    return dict(id=identifier,plugin=key[0],local_id=key[1],revision=definition['revision'],expected_equip_mask=mask,coverage=dict(definition['coverage']),rationale=rationale or definition['rationale'])

def identity(row):
    # Reuse the installed-format authoring validator for exact plugin/ID/mask rules.
    p=dict(id='identity-check',plugin=row['plugin'],local_id=row['local_id'],revision=1,expected_equip_mask=row['expected_equip_mask'],coverage={r:'unknown' for r in REGIONS},rationale='Validation only')
    validate(doc('Validation only',[p]))
    return (row['plugin'].lower(),row['local_id'].upper())

def resolve_document(document):
    exact(document,TOP,'document')
    if type(document['schema_version']) is not int or document['schema_version']!=1:raise ValueError('schema_version')
    nonempty(document['policy'],'policy')
    if document['regions']!=REGIONS:raise ValueError('regions: require the six supported regions in order')
    definitions=document['profile_definitions'];rules=document['keyword_rules'];bindings=document['bindings'];overrides=document['record_overrides']
    bounded(definitions,MAX_PROFILES,'profile_definitions',1);bounded(rules,MAX_RULES,'keyword_rules')
    bounded(bindings,MAX_PROFILES,'bindings',1);bounded(overrides,MAX_PROFILES,'record_overrides')
    defs={}
    for d in definitions:
        exact(d,{'id','revision','coverage','rationale'},'profile_definition')
        if not isinstance(d['id'],str) or not re.fullmatch(r'[a-z0-9-]{1,64}',d['id']):raise ValueError('profile id')
        if d['id'] in defs:raise ValueError('duplicate profile id')
        # The temporary key is a validator fixture, never emitted into a mapping.
        validate(doc('Definition validation',[profile(d,('NVO.esm','00000001'),'00000004',d['id'])]))
        defs[d['id']]=d
    selectors={}
    for r in rules:
        exact(r,{'keyword','profile'},'keyword_rule');tag=tag_key(r['keyword'])
        if tag in selectors:raise ValueError('duplicate keyword rule (case-insensitive)')
        chosen=r['profile']
        if chosen is not None and (not isinstance(chosen,str) or chosen not in defs):raise ValueError('keyword rule references missing profile')
        selectors[tag]=chosen
    bind_map={}
    for b in bindings:
        exact(b,{'plugin','local_id','expected_equip_mask','keywords'},'binding');key=identity(b)
        if key in bind_map:raise ValueError('duplicate exact record binding')
        bounded(b['keywords'],MAX_TAGS,'binding keywords')
        tags=[tag_key(t) for t in b['keywords']]
        if len(tags)!=len(set(tags)):raise ValueError('duplicate keyword on record')
        if any(t not in selectors for t in tags):raise ValueError('undeclared keyword on record '+str(key))
        bind_map[key]=(b,tags)
    override_map={}
    for o in overrides:
        exact(o,{'plugin','local_id','profile','rationale'},'record_override')
        # Validate the key using the existing parser. The fixed mask is not emitted.
        key=identity(dict(plugin=o['plugin'],local_id=o['local_id'],expected_equip_mask='00000004'))
        nonempty(o['rationale'],'override rationale')
        if key in override_map:raise ValueError('duplicate exact record override')
        if key not in bind_map:raise ValueError('orphan record override')
        if not isinstance(o['profile'],str) or o['profile'] not in defs:raise ValueError('override references missing profile')
        override_map[key]=o
    output=[];decisions=[]
    for key,(b,tags) in sorted(bind_map.items()):
        choices={selectors[t] for t in tags if selectors[t] is not None}
        # A record exception must not hide contradictory classification input.
        if len(choices)>1:raise ValueError('conflicting profile keywords on '+str(key))
        chosen=next(iter(choices)) if choices else None
        reason='keyword_profile'
        if key in override_map:chosen=override_map[key]['profile'];reason='exact_record_override'
        if chosen is None:raise ValueError('no selecting keyword or exact override on '+str(key))
        d=defs[chosen]
        identifier='nvo-record-'+hashlib.sha256((key[0]+'|'+key[1]).encode('ascii')).hexdigest()[:24]
        rationale=d['rationale']
        if reason=='exact_record_override':rationale+=' Exact exception: '+override_map[key]['rationale']
        # Preserve the reviewed plugin spelling; key comparison itself ignores case.
        output.append(profile(d,(b['plugin'],key[1]),b['expected_equip_mask'].upper(),identifier,rationale))
        decisions.append(dict(plugin=b['plugin'],local_id=key[1],profile=chosen,revision=d['revision'],selection=reason,keywords=sorted(tags),expected_equip_mask=b['expected_equip_mask'].upper()))
    result=doc(document['policy'],output)
    validate(result)
    encode_profiles(result) # Also enforce the actual runtime byte limit before returning.
    report=dict(schema_version=1,mode='offline_NVO_authoring_tags',runtime_keyword_import=False,new_runtime_dependencies=[],native_version_required=327,records=len(output),definitions=len(defs),rules=len(selectors),decisions=decisions,coverage_authority=False,damage_replacement=False,stagger_writes=False)
    return result,report

def compile_source(source):
    raw=Path(source).read_bytes()
    if not raw or len(raw)>MAX_SOURCE_BYTES:raise ValueError('source size: expected1..1048576 bytes')
    resolved,report=resolve_document(load_document(raw.decode('utf-8-sig')))
    report['source_sha256']=hashlib.sha256(raw).hexdigest()
    runtime=encode_profiles(resolved)
    report['runtime_sha256']=hashlib.sha256(runtime).hexdigest()
    return runtime,resolved,report

def write_atomic(path,data):
    path=Path(path).resolve();path.parent.mkdir(parents=True,exist_ok=True)
    # A same-directory temporary file keeps the final single-file replacement atomic.
    handle=tempfile.NamedTemporaryFile(prefix='.nvo-profile-',suffix='.tmp',dir=path.parent,delete=False)
    temporary=Path(handle.name).resolve()
    assert temporary.parent==path.parent
    try:
        with handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
        os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source');p.add_argument('output',help='Workspace NVOArmourCoverage.tsv output')
    p.add_argument('--expanded',help='Optional expanded JSON authoring output')
    p.add_argument('--report',help='Optional resolution/provenance JSON output')
    args=p.parse_args()
    paths=[Path(x).resolve() for x in [args.source,args.output,args.expanded,args.report] if x]
    if len(paths)!=len(set(paths)):p.error('Input and output paths must be distinct')
    try:runtime,resolved,report=compile_source(args.source)
    except (ValueError,UnicodeError,OSError) as e:p.exit(2,'Profile export rejected; no output changed: '+str(e)+'\n')
    # Supporting outputs are written first. Only a fully validated export replaces the TSV.
    if args.expanded:write_atomic(args.expanded,(json.dumps(resolved,indent=2)+'\n').encode('utf-8'))
    if args.report:write_atomic(args.report,(json.dumps(report,indent=2)+'\n').encode('utf-8'))
    write_atomic(args.output,runtime)
    print(f'Prepared {len(resolved["profiles"])} exact profiles at {args.output}. New runtime dependencies:0. No game launch.')

if __name__=='__main__':main()

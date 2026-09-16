"""Focused malformed-authoring checks for the strict offline profile compiler."""
from copy import deepcopy
from generate_combat_4c_fixtures import PROFILE, load_document, validate

base = load_document(PROFILE.read_text())
checks = 0
def reject(document, name):
    global checks
    try: validate(document)
    except (ValueError, TypeError): checks += 1; print('PASS '+name); return
    raise AssertionError(name)
validate(base); checks += 1
for field, value in [('revision', True), ('revision', 0), ('revision', 2**32),
                     ('plugin', '../FalloutNV.esm'), ('plugin', 'FalloutNV.esm\n'),
                     ('plugin', 'Thing.esl'), ('local_id','0B020420'), ('local_id','00000000'),
                     ('expected_equip_mask','00100000'), ('expected_equip_mask','00000000')]:
    doc=deepcopy(base); doc['profiles'][0][field]=value; reject(doc, field+' malformed')
doc=deepcopy(base); doc['profiles'][0]['coverage'].pop('head'); reject(doc,'missing region')
doc=deepcopy(base); doc['profiles'][0]['coverage']['brain']='full'; reject(doc,'invented region')
doc=deepcopy(base); doc['profiles'][0]['coverage']['head']='50%'; reject(doc,'unapproved coverage fraction')
doc=deepcopy(base); doc['profiles'][0]['coverage']['head']=True; reject(doc,'boolean extent')
doc=deepcopy(base); doc['profiles'][0]['damage_multiplier']=4; reject(doc,'damage settings not accepted')
doc=deepcopy(base); doc['profiles'].append(deepcopy(doc['profiles'][0])); doc['profiles'][-1]['plugin']='FALLOUTNV.ESM'; doc['profiles'][-1]['id']='duplicate'; reject(doc,'duplicate origin key')
doc=deepcopy(base); doc['schema_version']=True; reject(doc,'boolean schema')
doc=deepcopy(base); doc['profiles']=[]; reject(doc,'empty catalog')
doc=deepcopy(base); doc['profiles']*=129; reject(doc,'catalog cap')
try: load_document('{"schema_version":1,"schema_version":2}')
except ValueError: checks += 1; print('PASS duplicate JSON fields')
else: raise AssertionError('duplicate JSON fields')
print(f'PASS {checks} profile-authoring checks')

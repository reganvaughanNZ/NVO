"""Review and preserve the user's four-hit 4D evidence. No game writes or launch."""
import hashlib,json,re,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STEP=ROOT/'source/combat/step4d'
RELEASE=ROOT/'release/NVO-Combat-Packet-4D-Armour-Identity'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
CAPTURE=STEP/'Evidence/LIVE-4D-20260917-010933.log'
EXPECTED='02f55dd6afa9999a85a595025c06c89f66a674f861a239f6a459335448fd5862'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
if not CAPTURE.exists():
    raw=(GAME/'NVOCombatCore.log').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==EXPECTED,'Log changed before capture; review new evidence separately.'
    CAPTURE.write_bytes(raw)
assert sha(CAPTURE)==EXPECTED
text=CAPTURE.read_text();assert text.startswith('NVOCombatCore 0.3.27 | phase=4D |')
rows=[]
for number,line in enumerate(text.splitlines(),1):
    if not line:continue
    fields={key:(quoted or plain) for key,quoted,plain in re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)=(?:"([^"]*)"|([^\s]+))',line)}
    rows.append(dict(kind=line.split()[0],line=number,**fields))
def of(kind):return [r for r in rows if r['kind']==kind]
def group(kind,s,q):return [r for r in of(kind) if r.get('session')==s and r.get('seq')==q]
expected=[('1','1',{'020420','020426'}),('1','2',{'020420'}),('1','3',set()),('2','1',{'020420','020426'})]
assert len(of('ARMOUR_SNAPSHOT'))==len(of('ARMOUR_COVERAGE'))==len(of('HIT_CONTEXT'))==4
assert len(of('ARMOUR_ITEM'))==len(of('ARMOUR_ORIGIN'))==len(of('ARMOUR_COVERAGE_ITEM'))==5
for s,q,forms in expected:
    snap=group('ARMOUR_SNAPSHOT',s,q)[0];result=group('ARMOUR_COVERAGE',s,q)[0]
    assert snap['target']==result['target']=='0015A796'
    assert snap['stable_double_read']==snap['enumeration_complete']=='1'
    assert snap['status']==('complete_with_armour' if forms else 'complete_no_armour_observed')
    assert int(snap['equipped_armour_count'])==int(result['item_count'])==len(forms)
    assert result['classified']=='1' and result['reason']=='classified_only'
    assert result['tx']==snap['tx']
    items=group('ARMOUR_ITEM',s,q);origins=group('ARMOUR_ORIGIN',s,q);coverage=group('ARMOUR_COVERAGE_ITEM',s,q)
    assert {r['form'][-6:] for r in items}=={r['local'] for r in origins}=={r['local'] for r in coverage}==forms
    for item in items:
        origin=next(r for r in origins if r['item']==item['item'])
        cov=next(r for r in coverage if r['item']==item['item'])
        assert origin['status']=='resolved_origin' and origin['form']==item['form']
        assert origin['tx']==result['tx'] and origin['local']==cov['local']==item['form'][-6:]
        assert origin['plugin']==cov['plugin']=='FalloutNV.esm'
        assert item['instance']==cov['instance'] and float(item['condition_ratio'])==float(cov['condition'])==1
        assert cov['revision']=='1' and cov['partial_hit_surface']=='unresolved' and cov['classification_only']=='1'
        regions=['head','torso','left_arm','right_arm','left_leg','right_leg']
        assert [cov[r] for r in regions]==(['partial']+['none']*5 if cov['local']=='020426' else ['none']+['partial']*5)
ready=of('ARMOUR_COVERAGE_READY');assert len(ready)==2
assert [r['session'] for r in ready]==['1','2']
assert all(r['ready']=='1' and r['reason']=='ready' and r['origin_mods']=='12' and r['profiles']=='2' for r in ready)
summary=of('ARMOUR_COVERAGE_SUMMARY');assert len(summary)==2
assert [(r['seen'],r['classified'],r['held']) for r in summary]==[('3','3','0'),('1','1','0')]
assert len(of('STARTUP_BANNER'))==1 and of('STARTUP_BANNER')[0]['submitted']=='1'
assert text.rstrip().endswith('LIFECYCLE exit_game')
authority=['snapshot_authority','armour_preview','gameplay_writes','damage_replacement','bare_region_verified','region_coverage_complete','layer_order_verified','impact_snapshot_verified','speed_authority','region_authority','coverage_authority','material_response','stagger_writes','winning_override_verified']
assert all(r[k]=='0' for r in rows for k in authority if k in r)
errors=['rejected','unstable','omitted_after_limit','scope_rejected','stale_epoch','unmatched','reused_live_address','overflow','read_failures','open_lifetimes','invalid','depth_overflow','unscoped_stages','log_failures','mismatches','accounting_unpaired','failed','process_fault','slots_held','open','unresolved_origins','log_write_failures','optional_read_failures','duplicate_collisions','duplicate_callbacks']
for r in rows:
    if r['kind']=='SUMMARY' or r['kind'].endswith('_SUMMARY'):assert all(r[k]=='0' for k in errors if k in r),r
assert sum(int(r['create']) for r in of('SUMMARY'))==4
assert all(r['weapon']=='00004333' and r['ammo']=='0006B53C' and r['target_type']=='3B' and r['source']=='00000014' and r['region']=='0' for r in of('HIT_CONTEXT'))
receipt=json.loads((STEP/'INSTALL-result.json').read_text(encoding='utf-8-sig'))
plan=json.loads((STEP/'Evidence/INSTALL-plan.json').read_text())
pinned=dict(plan['protected']);pinned.update({r['path']:r['sha256'] for r in receipt['installed']})
for name,digest in pinned.items():assert sha(GAME/name)==digest,name
assert not (GAME/'Data/RD.esm').exists()
report=dict(packet='4D',verdict='Live exact-origin and authored-coverage checkpoint PASSED',capture=str(CAPTURE.relative_to(ROOT)),sha256=EXPECTED,native_version=327,sessions=2,reloads=1,hits=4,weapon='Hunting rifle / standard .308',snapshot_item_counts=[2,1,0,2],armour_snapshots=of('ARMOUR_SNAPSHOT'),origin_rows=of('ARMOUR_ORIGIN'),classification_rows=of('ARMOUR_COVERAGE'),coverage_items=of('ARMOUR_COVERAGE_ITEM'),summaries=summary,startup_banners=1,normal_exit=True,installed_files_verified=len(pinned),authority_promoted=False,damage_replacement=False,game_files_changed=False,limitations=['No live custom armour, changed load order, unknown worn item, NPC-to-player or creature classification tested.','All observed item conditions were full. No new condition-change test.','Authored extents do not prove actual struck surface, material response, layer order, winning override or bare anatomy.','No new performance timing or stress acceptance. Contact speed remains non-authoritative.','Hunting rifle/.308 instead of requested9mm supplies the required equipment states; no repeat needed.'])
write(STEP/'LIVE-REVIEW.json',report)
review=f'''# Packet 4D live review

**Exact-origin and authored-coverage functional checkpoint passed.** No further repetition of this test is needed.

Pinned log: Evidence/{CAPTURE.name}; SHA256 {EXPECTED}. Native327, two load sessions, one reload and one submitted startup banner. Normal exit.

| Load / hit | Equipment observed | Classification result | Log line |
|---|---|---|---|
| 1 / 1 | Combat Armor and Combat Helmet | Two independent FalloutNV.esm profiles | 82 |
| 1 / 2 | Combat Armor only | Helmet row absent | 147 |
| 1 / 3 | No worn armour observed | Empty classification, bare authority remains0 | 209 |
| 2 / 1 | Both pieces restored | Fresh successful classification after reload | 328 |

Both activations resolved12 loaded mod names and loaded2 profiles. All4 snapshots were complete and stable. All5 item rows agree across raw identity, copied owning-plugin/local-ID, call-local instance token and profile mapping. Body coverage stays partial torso/limbs with no head; helmet coverage stays partial head only. All conditions were full. Item traversal order reverses after reload, with correct profile identity retained.

Zero classification holds, unresolved origins, reader rejects, unstable snapshots, scope failures or logging failures. Lifecycle, hit-transaction and projectile summaries report no open calls/lifetimes, read failures, movement mismatches or admission faults. Contact-speed rows remain non-authoritative observed engine segments; no exact-energy approval follows from them.

All4 landed hits used the hunting rifle00004333 and standard .3080006B53C, with hit-data region0 on the same humanoid. This differs from the requested9mm, but adequately exercises the requested inventory and reload states. No repeat is needed for this checkpoint.

All15 pinned installed files match the installation receipt and protected baseline. RD.esm is absent. This review copied the log and wrote workspace documentation only; it did not change game files, launch a process, install KEYWORDS or enable any damage/stagger authority.

Scope: successful live base-game identities and provisional authored coverage only. Custom gear, altered load order, unknown equipment, creatures, NPC-to-player cases, condition changes and stress timing were not exercised here. The existing offline cases remain separate evidence. Actual hit-surface coverage, ordered materials, winning overrides, anatomy, modifier ownership and contact-speed authority still gate damage.

Proposed next packet, subject to approval:4E keyword-to-profile authoring support for custom armour. Establish validated mappings and exact-record exceptions, refuse conflicting tags, and decide a bounded cached integration using the available JIP/KEYWORDS sources. Begin with offline resolution checks; do not presume a native keyword API or read private donor containers without a reviewed interface. No game installation or damage enablement is approved by this test-completion message.
'''
(STEP/'LIVE-REVIEW.md').write_text(review,encoding='utf-8')
for name in ['LIVE-REVIEW.md','LIVE-REVIEW.json']:shutil.copy2(STEP/name,RELEASE/name)
shutil.copy2(CAPTURE,RELEASE/'Evidence'/CAPTURE.name)
page=(STEP/'START-HERE.html').read_text(encoding='utf-8')
page=page.replace('Installed · NVO 0.3.27 / native327. Live test pending.','Installed · NVO 0.3.27 / native327. Live checkpoint passed.')
page=page.replace('<h2>Your test · four landed hits, one reload</h2>','<div class="notice"><strong>Test passed.</strong> All four equipment states and the reload matched. No repeat needed. <a href="LIVE-REVIEW.md">Read the result</a>. The instructions below are retained for reference.</div><h2>Completed test · four landed hits, one reload</h2>')
page=page.replace('The installation is ready for this checkpoint.','This checkpoint has been completed.')
for p in [STEP/'START-HERE.html',RELEASE/'START-HERE.html']:p.write_text(page,encoding='utf-8')
readme=(STEP/'README.md').read_text(encoding='utf-8').replace('the user live checkpoint is pending.','the live exact-origin and authored-coverage checkpoint passed; see LIVE-REVIEW.md.')
for p in [STEP/'README.md',RELEASE/'README.md']:p.write_text(readme,encoding='utf-8')
manifest=json.loads((RELEASE/'MANIFEST.json').read_text());manifest['status']=report['verdict'];manifest['files']=[]
for p in sorted(RELEASE.rglob('*')):
    if p.is_file() and p.name!='MANIFEST.json':manifest['files'].append(dict(path=p.relative_to(RELEASE).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
write(RELEASE/'MANIFEST.json',manifest)
archive=RELEASE.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file():z.write(p,str(Path(RELEASE.name)/p.relative_to(RELEASE)))
package=json.loads((STEP/'PACKAGE.json').read_text());package.update(sha256=sha(archive),bytes=archive.stat().st_size,status=report['verdict']);write(STEP/'PACKAGE.json',package)
status=ROOT/'STATUS.md';old=status.read_bytes()
heading=f'''## Current checkpoint: Packet 4D live origin/coverage checkpoint PASSED

Pinned capture SHA{EXPECTED}; source/combat/step4d/LIVE-REVIEW.md and JSON. Four stable humanoid snapshots classify2,1,0,2 worn items across one reload. Exact FalloutNV.esm Combat Armor020420/Helmet020426 origins and independent extents correct, including reversed traversal order after reload. Two ready activations,12 loaded mods,2 profiles, one banner and normal exit. Zero classification/reader/lifecycle errors. Four hunting-rifle/.308 torso contexts rather than requested9mm; accepted for this narrow state check with no repeat. All conditions full.15 installed hashes unchanged; RD absent; no game changes or authority promotion.

Pending damage gates remain: exact hit surface, anatomy, materials/layering, modifier ownership, winning-override review and authoritative contact energy. No custom gear/load-order change/unknown gear/creature/performance claim from this live test. NEXT ask before4E keyword-to-profile support for custom armour, beginning with offline validated resolution and exact-record exceptions. No new implementation/install authorized by test completion.

'''
if heading.splitlines()[0].encode() not in old:
    cut=old.index(b'\n')+1;status.write_bytes(old[:cut]+b'\n'+heading.encode('utf-8')+old[cut:])
print(json.dumps(dict(verdict=report['verdict'],hits=4,states=[2,1,0,2],reloads=1,installed_files_verified=len(pinned),game_changes=False,damage_replacement=False)))

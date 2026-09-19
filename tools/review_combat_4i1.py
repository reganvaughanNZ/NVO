"""Review the pinned three-hit 4I1 callback-survival capture; read-only against installed game files."""
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'source/combat/step4i1'
LOG = STEP / 'Evidence/LIVE-4I1-20260919.log'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lines = LOG.read_text().splitlines()
    rows = []
    for number, line in enumerate(lines, 1):
        row = dict(re.findall(r'\b([a-zA-Z_][a-zA-Z_0-9]*)=([^\s]+)', line))
        row.update(event=line.split()[0], line=number)
        rows.append(row)
    def select(event, **fields):
        return [r for r in rows if r['event'] == event and all(r.get(k) == str(v) for k, v in fields.items())]
    def one(event, **fields):
        found = select(event, **fields)
        if len(found) != 1: raise RuntimeError(f'Expected one {event} {fields}, got {len(found)}')
        return found[0]
    def require(test, why):
        if not test: raise RuntimeError(why)
    require(lines[0].startswith('NVOCombatCore 0.3.29 | phase=4I1'), 'Wrong native build')
    require(lines[-1] == 'LIFECYCLE exit_game', 'Capture has no normal exit marker')
    require(len(select('STARTUP_BANNER', submitted=1)) == 1, 'Expected one startup banner')
    captures = select('HIT_COPY_CAPTURE')
    require(Counter(r['session'] for r in captures) == {'1': 1, '2': 2}, 'Unexpected hit/reload sequence')
    hits = []
    for c in captures:
        session, context = c['session'], c['context']
        require(c['scope_session'] == session and c['copy_scope_valid'] == c['armour_joined'] == '1', 'Unbound copy')
        scope = {k: c[k] for k in ('session', 'generation', 'tx', 'copy')}
        tx = one('HIT_TX_STAGE', stage='copy_input', **scope)
        armour = one('ARMOUR_COPY_SCOPE', **scope)
        impact = one('IMPACT_COPY_CAPTURE', context=context, **scope)
        hit = one('HIT_CONTEXT', session=session, seq=context)
        contact = one('IMPACT_HIT', session=session, context=context)
        snapshot = one('ARMOUR_SNAPSHOT', session=session, seq=c['armour_seq'], tx=c['tx'])
        returned = one('HIT_TX_RETURN', session=session, tx=c['tx'])
        ready = one('HIT_TX_READY', session=session)
        require(ready['generation'] == c['generation'], 'Stale generation')
        require(tx['association'] == 'exact_input_pointer' and tx['tainted'] == returned['tainted'] == '0', 'Bad transaction scope')
        require(returned['copies'] == returned['pre_hit'] == returned['pre_health'] == '1', 'Missing or duplicate callback/copy')
        begin = one('HIT_TX_BEGIN', session=session, tx=c['tx'])
        pre_hit = one('HIT_TX_STAGE', session=session, tx=c['tx'], stage='itr_pre_hit')
        pre_health = one('HIT_TX_STAGE', session=session, tx=c['tx'], stage='itr_pre_health')
        damage_input = one('DAMAGE_INPUT', session=session, seq=context)
        health_input = one('HEALTH_INPUT', session=session, seq=context)
        require(begin['line'] < pre_hit['line'] < damage_input['line'] < tx['line'] < c['line']
                < pre_health['line'] < health_input['line'] < returned['line'], 'Unexpected callback ordering')
        for event in (pre_hit, pre_health):
            require(event['identity_match'] == event['read'] == event['value_valid'] == '1'
                    and event['tainted'] == '0', 'Invalid callback transaction association')
        require(damage_input['target'] == health_input['target'] == hit['target']
                and damage_input['source'] == health_input['source'] == hit['source']
                and damage_input['weapon'] == hit['weapon'] and damage_input['region'] == hit['region'], 'Callback identity mismatch')
        require(impact['scope_session'] == session and impact['copy_scope_valid'] == impact['armour_joined'] == impact['collision_paired'] == '1', 'Contact join failed')
        require(c['armour_status'] == impact['armour_status'] == 'stable_equipment_copy', 'Rejected receipt')
        require(c['reader_epoch'] == impact['reader_epoch'] == armour['reader_epoch'], 'Mismatched armour epoch')
        require(c['armour_seq'] == impact['armour_seq'] == armour['seq'], 'Mismatched snapshot sequence')
        require(snapshot['equipped_armour_count'] == c['items'] == '2'
                and snapshot['stable_double_read'] == snapshot['enumeration_complete'] == '1', 'Incomplete equipment')
        for field in ('source', 'target', 'carrier', 'weapon', 'ammo', 'lifetime'):
            require(hit[field] == armour[field], f'Armour identity mismatch: {field}')
        for field in ('source', 'target', 'weapon', 'ammo', 'lifetime'):
            require(hit[field] == contact[field], f'Contact identity mismatch: {field}')
        require(hit['carrier'] == contact['projectile'] and hit['lifetime'] == impact['lifetime'], 'Carrier/lifetime mismatch')
        require(hit['weapon'] == '000E3778' and hit['ammo'] == '0008ED03', 'Not standard 9mm pistol')
        require(hit['region'] == contact['hit_region'] == contact['contact_region'] == armour['hit_region'] == '0', 'Region mismatch')
        items = select('ARMOUR_ITEM', session=session, seq=c['armour_seq'])
        require(len(items) == 2 and {r['form'] for r in items} == {'00020420', '00020426'}, 'Unexpected equipment')
        require(all(r['condition_ratio'] == '1' for r in items), 'Unexpected item condition')
        speed = one('IMPACT_HIT_SPEED', session=session, context=context)
        require(speed['available'] == '1' and speed['status'] == 'observed_engine_segment', 'Unexpected speed producer')
        hits.append(dict(**scope, context=context, lifetime=hit['lifetime'], target=hit['target'],
            region=hit['region'], armour_sequence=c['armour_seq'], reader_epoch=c['reader_epoch'],
            forms=[r['form'] for r in items], instance_tokens=[r['instance'] for r in items],
            speed_kind=speed['status'], speed_authority=speed['speed_authority'],
            lines={r['event']: r['line'] for r in (tx, armour, c, hit, contact, impact, returned, damage_input, health_input)}))
    require(hits[0]['generation'] != hits[-1]['generation'] and hits[0]['reader_epoch'] != hits[-1]['reader_epoch'], 'Reload did not invalidate capture scopes')
    require(len({tuple(h[k] for k in ('session', 'generation', 'tx', 'copy')) for h in hits}) == 3, 'Duplicate copy key')
    require(len({h['lifetime'] for h in hits}) == 3, 'Reused lifetime')
    zero_summaries = {'HIT_TX_SUMMARY': ('open', 'invalid', 'depth_overflow', 'unscoped_stages', 'log_failures'),
        'ARMOUR_SNAPSHOT_SUMMARY': ('rejected', 'unstable', 'omitted_after_limit', 'scope_rejected', 'stale_epoch'),
        'IMPACT_HIT_SUMMARY': ('region_differences', 'optional_read_failures', 'omitted_queries', 'log_write_failures'),
        'SPAWN_BOUNDARY_SUMMARY': ('mismatched', 'depth_overflow', 'stale_returns'),
        'PHYSICS_DIAGNOSTIC_SUMMARY': ('mismatches', 'report_write_failures')}
    for event, fields in zero_summaries.items():
        for session in ('1', '2'):
            row = one(event, session=session)
            require(all(row[k] == '0' for k in fields), f'Nonzero failure summary: {event}')
    authority = ('damage_replacement', 'stagger_writes', 'snapshot_authority', 'armour_preview',
                 'speed_authority', 'region_authority', 'at_impact_verified', 'component_verified', 'application_verified')
    require(all(r[k] == '0' for r in rows for k in authority if k in r), 'Unexpected enabled authority')
    require(len(select('HIT_TX_BEGIN')) == len(select('HIT_TX_RETURN')) == len(select('DAMAGE_INPUT'))
            == len(select('HEALTH_INPUT')) == 3, 'Unexpected hit or callback count')
    callbacks = [one('DAMAGE_EVENT_SUMMARY', session=s) for s in ('1', '2')]
    registries = []
    for session, count in (('1', 1), ('2', 2)):
        summary = one('DAMAGE_EVENT_SUMMARY', session=session)
        require(summary['hit_callbacks'] == summary['health_callbacks'] == str(count)
                and summary['invalid'] == summary['gap_requests'] == '0'
                and summary['registry_checks'] == '4', 'Callback survival/budget failed')
        for stream in ('pre_hit', 'pre_health'):
            one('DAMAGE_EVENT_EMISSION', session=session, stream=stream, observed=1)
        registry = select('DAMAGE_EVENT_REGISTRY', session=session)
        require([r['loop'] for r in registry] == ['0', '2', '32', '64'], 'Unexpected survival schedule')
        require([r['check'] for r in registry] == ['1', '2', '3', '4'], 'Unbounded/duplicate checks')
        require(len({r['generation'] for r in registry}) == 1, 'Registry generation changed in session')
        for index, row in enumerate(registry):
            for stream in ('hit', 'health'):
                require(row[stream + '_after'] == 'present', 'Registry positive witness missing')
                require(row[stream + '_set'] == ('added_or_revived' if index == 0 else 'unchanged_or_refused'), 'Unexpected registration repair')
                if index: require(row[stream + '_before'] == 'present', 'Registration survival missing')
        registries.extend(registry)
    require(registries[0]['generation'] != registries[-1]['generation'], 'Registry epoch reused across reload')
    require(not any(r['event'].endswith(('_DISABLED', '_FAILED', '_INVALID')) for r in rows), 'Explicit diagnostic failure')
    gaps = [dict(session=r['session'], hit_callbacks=r['hit_callbacks'], health_callbacks=r['health_callbacks'],
                 line=r['line']) for r in callbacks if r['hit_callbacks'] == '0' or r['health_callbacks'] == '0']
    plan = json.loads((STEP / 'Evidence/INSTALL-plan.json').read_text(encoding='utf-8-sig'))
    game = Path(plan['game_root'])
    installed = []
    for row in plan['files']:
        path = game / row['path']; value = digest(path)
        require(value == row['sha256'], 'Installed build changed')
        installed.append(dict(path=row['path'], sha256=value))
    protected = []
    for relative, expected in plan['protected'].items():
        require(digest(game / relative) == expected, f'Protected record/config changed: {relative}')
        protected.append(dict(path=relative, sha256=expected))
    require(not (game / 'Data/RD.esm').exists(), 'RD master unexpectedly present')
    result = dict(packet='4I1', status='CALLBACK_SURVIVAL_PASSED' if not gaps else 'CALLBACK_SURVIVAL_FAILED',
        reviewed_utc=datetime.now(timezone.utc).isoformat(), capture=dict(path=LOG.relative_to(ROOT).as_posix(),
        sha256=digest(LOG), bytes=LOG.stat().st_size, lines=len(lines)), hits=hits, callback_summaries=callbacks,
        callback_gaps=gaps, registry_checks=registries, recovery_needed=False, original_gap_cause_established=False, installed=installed, protected_records_and_config=protected,
        normal_exit=True, startup_banners=1, gameplay_writes=False, game_modified=False,
        scope='Three standard9mm humanoid torso copies across one reload. No exact speed/atomic snapshot/component/application acceptance.',
        next='Ask before returning to native component/application diagnostics; keep damage authority disabled. No unchanged repeat of this callback check required.')
    (STEP / 'LIVE-REVIEW.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=result['status'], hits=len(hits), callbacks=callbacks,
                          installed_files_verified=len(installed), protected_files_verified=len(protected), sha256=digest(LOG))))


if __name__ == '__main__': main()

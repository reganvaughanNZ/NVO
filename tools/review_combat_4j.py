"""Reparse the pinned 4J playtest; read-only verification of installed files."""
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'source/combat/step4j'
LOG = STEP / 'Evidence/LIVE-4J-20260919-094727.log'
EXPECTED = '8e079a12b768f5b2ae25b56e0ddc378092f73ee51efec4e3239cd2903ebb3d30'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    def require(condition, message):
        if not condition:
            raise RuntimeError(message)
    require(digest(LOG) == EXPECTED, 'Pinned capture changed')
    lines = LOG.read_text().splitlines()
    rows = []
    for number, line in enumerate(lines, 1):
        if not line:
            continue
        row = dict(re.findall(r'\b([a-zA-Z_][a-zA-Z_0-9]*)=([^\s]+)', line))
        row.update(event=line.split()[0], line=number)
        rows.append(row)
    def select(event, **fields):
        return [r for r in rows if r['event'] == event and all(r.get(k) == str(v) for k, v in fields.items())]
    def one(event, **fields):
        found = select(event, **fields)
        require(len(found) == 1, f'Expected one {event} {fields}, found {len(found)}')
        return found[0]
    require(lines[0].startswith('NVOCombatCore 0.3.30 | phase=4J'), 'Wrong native version')
    require(lines[-1] == 'LIFECYCLE exit_game', 'No normal exit marker')
    one('STARTUP_BANNER', submitted=1)
    require(not any(r['event'].endswith(('_FAILED', '_DISABLED', '_INVALID')) for r in rows), 'Explicit diagnostic failure')
    authority = ('damage_replacement', 'stagger_writes', 'snapshot_authority', 'armour_preview',
                 'speed_authority', 'region_authority', 'at_impact_verified', 'component_verified',
                 'application_verified', 'observer_writes', 'observer_value_writes', 'gameplay_writes')
    require(all(r[k] == '0' for r in rows for k in authority if k in r), 'Unexpected gameplay authority')
    copies = select('HIT_COPY_CAPTURE')
    require(Counter(r['session'] for r in copies) == {'1': 12, '2': 1}, 'Unexpected hit sequence')
    require(len(select('HIT_TX_BEGIN')) == len(select('HIT_TX_RETURN')) == 13, 'Transaction count mismatch')
    transactions = []
    for c in copies:
        scope = {k: c[k] for k in ('session', 'generation', 'tx', 'copy')}
        session, tx = c['session'], c['tx']
        begin = one('HIT_TX_BEGIN', session=session, tx=tx)
        returned = one('HIT_TX_RETURN', session=session, tx=tx)
        data = one('HIT_TX_DATA', session=session, tx=tx)
        hit = one('HIT_CONTEXT', session=session, seq=c['context'])
        stage = one('HIT_TX_STAGE', stage='copy_input', **scope)
        armour = one('ARMOUR_COPY_SCOPE', **scope)
        snapshot = one('ARMOUR_SNAPSHOT', session=session, seq=c['armour_seq'], tx=tx)
        require(one('HIT_TX_READY', session=session)['generation'] == c['generation'], 'Stale transaction generation')
        require(c['copy_scope_valid'] == c['armour_joined'] == snapshot['stable_double_read'] == snapshot['enumeration_complete'] == '1', 'Rejected copy receipt')
        require(c['scope_session'] == session and c['armour_status'] == 'stable_equipment_copy', 'Copy scope mismatch')
        require(c['reader_epoch'] == armour['reader_epoch'] and c['armour_seq'] == armour['seq'], 'Armour receipt mismatch')
        require(stage['association'] == 'exact_input_pointer' and stage['tainted'] == returned['tainted'] == '0', 'Invalid copy association')
        require(begin['valid'] == begin['main_thread'] == begin['return_site_match'] == returned['pre_hit'] == returned['copies'] == '1', 'Invalid transaction')
        require(all(hit[k] == armour[k] for k in ('source', 'target', 'carrier', 'weapon', 'ammo', 'lifetime')), 'Copy metadata mismatch')
        require(begin['line'] < stage['line'] < c['line'] < returned['line'], 'Copy outside transaction')
        transactions.append(dict(**scope, context=c['context'], weapon=hit['weapon'], carrier=hit['carrier'],
            carrier_type=hit['carrier_type'], lifetime=hit['lifetime'], region=hit['region'],
            input_health=data['health'], flags=data['flags'], pre_health=returned['pre_health'],
            reader_epoch=c['reader_epoch'], begin_line=begin['line'], return_line=returned['line']))
    require(len({tuple(r[k] for k in ('session', 'generation', 'tx', 'copy')) for r in transactions}) == 13, 'Duplicate copy key')
    require(transactions[0]['generation'] != transactions[-1]['generation'] and transactions[0]['reader_epoch'] != transactions[-1]['reader_epoch'], 'Reload reused capture generation')
    require(Counter(r['weapon'] for r in transactions) == {'000E3778': 2, '00004330': 1, '0000432D': 10}, 'Unexpected weapon sample')
    av_calls = []
    for attr in select('AV_ATTRIBUTION_BEGIN'):
        key = {k: attr[k] for k in ('session', 'call')}
        begin = one('AV_APPLY_BEGIN', **key)
        end = one('AV_APPLY_END', **key)
        finish = one('AV_ATTRIBUTION_END', **key)
        txkey = dict(session=attr['session'], tx=attr['tx'])
        tx = one('HIT_TX_BEGIN', **txkey)
        data = one('HIT_TX_DATA', **txkey)
        returned = one('HIT_TX_RETURN', **txkey)
        copy = one('HIT_COPY_CAPTURE', **txkey)
        require(attr['generation'] == finish['generation'] == one('AV_APPLY_READY', session=attr['session'])['generation'], 'Stale AV generation')
        require(attr['tx_generation'] == finish['tx_generation'] == copy['generation'], 'Stale transaction join')
        require(attr['tx'] == begin['tx'] == end['tx'] == finish['tx'], 'AV transaction changed')
        require(attr['context'] == 'matching_hit_scope' and attr['hit_metadata_available'] == finish['scope_retained'] == begin['scope_match'] == end['scope_match'] == '1', 'Unmatched AV context')
        require(all(attr[k] == tx[k] for k in ('weapon', 'ammo', 'carrier', 'carrier_type', 'lifetime')) and attr['hit_flags'] == data['flags'], 'Original metadata changed')
        require(begin['receiver'] == tx['receiver'] and begin['source'] == tx['source'], 'AV actor identity mismatch')
        require(attr['route_witness'] == finish['route_witness'] == 'verified_window' and attr['route'] == finish['route'], 'Unverified route')
        require(begin['read_valid'] == end['valid'] == finish['valid'] == '1' and end['tainted'] == finish['callback_mismatches'] == '0', 'Invalid AV interval')
        require(begin['parent'] == end['nested'] == finish['nested'] == '0', 'Unexpected nesting in pinned capture')
        require(attr['primary_or_secondary'] == finish['primary_or_secondary'] == 'unresolved' and finish['additive_net'] == '0', 'Overclaimed ownership')
        require(tx['line'] < begin['line'] < attr['line'] < end['line'] < finish['line'] < returned['line'], 'AV interval outside transaction')
        expected_health = '1' if begin['av'] == '16' else '0'
        require(finish['health_callbacks'] == expected_health, 'Callback/AV mismatch')
        if begin['av'] == '16':
            callback = one('HIT_TX_STAGE', stage='itr_pre_health', **txkey)
            require(callback['delta'] == begin['requested'] and callback['identity_match'] == callback['read'] == callback['value_valid'] == '1', 'Pre-health input mismatch')
            require(attr['line'] < callback['line'] < end['line'], 'Pre-health outside AV interval')
            require(attr['route'] == 'health_helper_call' and begin['caller'] == '0089D82D', 'Unexpected health caller')
        else:
            require(attr['route'] == 'hitme_condition_call' and begin['caller'] in ('0089BDD8', '0089BB8E'), 'Unexpected condition caller')
        av_calls.append(dict(**key, generation=attr['generation'], tx=attr['tx'], av=begin['av'],
            requested=begin['requested'], net_current=end['net_current'], net_damage=end['net_damage'],
            route=attr['route'], caller=begin['caller'], carrier_kind=attr['carrier_kind'],
            explosion_flag=attr['explosion_flag'], critical_effect=attr['critical_effect'],
            health_callbacks=finish['health_callbacks'], begin_line=begin['line'], end_line=finish['line']))
    require(len(av_calls) == len(select('AV_APPLY_BEGIN')) == len(select('AV_APPLY_END')) == len(select('AV_ATTRIBUTION_END')) == 27, 'Incomplete AV rows')
    require(len({r['call'] for r in av_calls}) == 27, 'Reused diagnostic call ID')
    require(Counter(r['route'] for r in av_calls) == {'health_helper_call': 12, 'hitme_condition_call': 15}, 'Unexpected route count')
    no_health = [r for r in transactions if r['pre_health'] == '0']
    require(len(no_health) == 1 and no_health[0]['tx'] == '4' and no_health[0]['region'] == '14' and float(no_health[0]['input_health']) == 0, 'Unexplained health callback gap')
    require(not [r for r in av_calls if r['tx'] == '4'], 'Unexpected watched AV at zero-health weapon contact')
    registries = select('DAMAGE_EVENT_REGISTRY')
    for s, count in (('1', 5), ('2', 4)):
        rs = select('DAMAGE_EVENT_REGISTRY', session=s)
        require(len(rs) == count and [r['check'] for r in rs] == [str(i) for i in range(1, count+1)], 'Unbounded registry checks')
        require([r['loop'] for r in rs[:4]] == ['0', '2', '32', '64'], 'Survival schedule changed')
        require(all(r['hit_after'] == r['health_after'] == 'present' for r in rs), 'Missing positive registry witness')
        for stream in ('pre_hit', 'pre_health'):
            one('DAMAGE_EVENT_EMISSION', session=s, stream=stream, observed=1)
    gap = one('DAMAGE_EVENT_REGISTRY', reason='copied_transaction_callback_gap')
    require(gap['tx'] == '4' and gap['hit_before'] == gap['health_before'] == 'present' and gap['hit_set'] == gap['health_set'] == 'unchanged_or_refused', 'Unexpected registration repair')
    zero_summaries = {
        'AV_APPLY_SUMMARY': ('open', 'invalid', 'depth_overflow', 'log_failures'),
        'AV_ATTRIBUTION_SUMMARY': ('unscoped', 'route_unresolved', 'callback_mismatches', 'unscoped_health_callbacks'),
        'HIT_TX_SUMMARY': ('open', 'invalid', 'depth_overflow', 'unscoped_stages', 'omitted_stage_rows', 'log_failures'),
        'ARMOUR_SNAPSHOT_SUMMARY': ('rejected', 'unstable', 'omitted_after_limit', 'scope_rejected', 'stale_epoch'),
        'IMPACT_HIT_SUMMARY': ('region_differences', 'optional_read_failures', 'omitted_queries', 'log_write_failures'),
        'SPAWN_BOUNDARY_SUMMARY': ('mismatched', 'depth_overflow', 'stale_returns'),
        'PHYSICS_DIAGNOSTIC_SUMMARY': ('mismatches', 'report_write_failures'),
        'DAMAGE_EVENT_SUMMARY': ('invalid',)}
    summaries = []
    for event, fields in zero_summaries.items():
        for session in ('1', '2'):
            r = one(event, session=session)
            require(all(r[k] == '0' for k in fields), f'Nonzero diagnostic failure: {event}')
            summaries.append(r)
    for session, calls, hit_count, health_count in (('1', '25', '12', '11'), ('2', '2', '1', '1')):
        av = one('AV_APPLY_SUMMARY', session=session)
        att = one('AV_ATTRIBUTION_SUMMARY', session=session)
        cb = one('DAMAGE_EVENT_SUMMARY', session=session)
        require(av['entries'] == av['returns'] == att['scoped'] == att['route_verified'] == calls, 'AV summary disagrees')
        require(cb['hit_callbacks'] == hit_count and cb['health_callbacks'] == att['health_callbacks'] == health_count, 'Callback summary disagrees')
    flight_faults = []
    for session in ('1', '2'):
        for event in ('FLIGHT_ADMISSION_SUMMARY', 'PHYSICS_ADMISSION_SUMMARY'):
            r = one(event, session=session)
            require(r['process_fault'] == '6', 'Pinned flight fault changed')
            flight_faults.append(r)
    repeated = [r for r in select('EVENT', session=1, replaced=1) if ' CREATE ' in lines[r['line']-1]]
    require(len(repeated) == 12 and all(r['projectile'] == 'FF001736' and r['weapon'] == '0000432D' and r['tracked'] == '0' for r in repeated), 'Unexpected repeated flame creation evidence')
    summary = one('SUMMARY', session=1)
    require(summary['reused_live_address'] == summary['overflow'] == '12', 'Lifetime summary disagrees')
    last_spawn = one('SPAWN_BOUNDARY', session=2)
    require(last_spawn['supplied_base'] == last_spawn['forwarded_base'] == last_spawn['returned_base'] == '0008F20F'
            and last_spawn['base_argument_changed'] == last_spawn['reserved'] == '0', 'Unexpected final projectile selection')
    require(one('IMPACT_HIT_SPEED', session=2)['status'] == 'untracked_profile', 'Unexpected post-reload flight evidence')
    # Compare separated health observations, without attributing the intervening change.
    health_gaps, previous = [], {}
    for call in av_calls:
        if call['av'] != '16': continue
        key = dict(session=call['session'], call=call['call'])
        begin = one('AV_APPLY_BEGIN', **key)
        end = one('AV_APPLY_END', **key)
        identity = (call['session'], begin['receiver'])
        old = previous.get(identity)
        if old:
            gap_value = float(begin['current_before']) - float(old['current_after'])
            if abs(gap_value) > 0.001:
                health_gaps.append(dict(session=call['session'], receiver=begin['receiver'],
                    previous_call=old['call'], next_call=call['call'], net_difference=gap_value,
                    cause='unobserved', component_verified=False, application_verified=False))
        previous[identity] = end
    plan = json.loads((STEP / 'Evidence/INSTALL-plan.json').read_text(encoding='utf-8-sig'))
    game = Path(plan['game_root'])
    installed, protected = [], []
    for row in plan['files']:
        value = digest(game / row['path']); require(value == row['sha256'], 'Installed file changed')
        installed.append(dict(path=row['path'], sha256=value))
    for relative, expected in plan['protected'].items():
        require(digest(game / relative) == expected, f'Protected input changed: {relative}')
        protected.append(dict(path=relative, sha256=expected))
    require(not (game / 'Data/RD.esm').exists(), 'RD master unexpectedly present')
    trace_sources = []
    pins = {r['path']:r['sha256'] for r in json.loads((STEP / 'Evidence/VERIFICATION.json').read_text())['source_inputs']}
    for relative in ('native/NVOCombatCore/src/NativeObserver.cpp', 'native/NVOCombatCore/include/FlightAdmission.hpp',
                     'native/NVOCombatCore/src/FlightPreview.cpp', 'native/NVOCombatCore/src/ActorValueObserver.cpp'):
        value = digest(ROOT / relative)
        require(value == pins[relative], 'Reviewed runtime source changed since prepared build')
        trace_sources.append(dict(path=relative, sha256=value))
    result = dict(packet='4J', native_version=330, status='ROUTE_PASS_FLIGHT_LIFECYCLE_FIX_REQUIRED',
        reviewed_utc=datetime.now(timezone.utc).isoformat(),
        capture=dict(path=LOG.relative_to(ROOT).as_posix(), sha256=EXPECTED, bytes=LOG.stat().st_size, lines=len(lines)),
        transactions=transactions, av_calls=av_calls, registry_checks=registries, summaries=summaries,
        installed=installed, protected_records_and_config=protected, rd_absent=True,
        normal_exit=True, startup_banners=1, game_modified=False, game_process_actions=False,
        native_rebuilt=False, fixture_tests_rerun=False, gameplay_writes=False,
        secondary_effect_coverage_verified=False, component_verified=False, application_verified=False,
        flight_accepted=False, flight_faults=flight_faults, repeated_flame_creates=repeated,
        post_reload_spawn=last_spawn, health_changes_between_windows=health_gaps, reviewed_source_pins=trace_sources,
        other_thread_passthrough={s:one('AV_APPLY_SUMMARY', session=s)['other_thread_passthrough'] for s in ('1','2')},
        projectile_profile_skips=select('FLIGHT_PREVIEW_SKIP'),
        scope='Recorded main-thread caller routes, original HitMe association and matched pre-health inputs across one reload.',
        limitations=['No timed-effect coverage or committed application identity established.',
            '356 off-main-thread dispatches were passed through before AV/delta filtering; their causes are unknown.',
            'Repeated flame contacts share one projectile lifetime; distinct grenade calls can have identical arguments.',
            'Repeated unadmitted flame creation notifications trigger the existing process-wide lifetime fault.',
            'That fault intentionally survives reload; the final 9mm retained its stock projectile and NVO flight was blocked.',
            'Health changes between monitored flamer windows have no captured owning call; cause remains unknown.',
            'No exact speed, coherent impact protection or damage authority accepted.'],
        next='Ask before Packet4J1: qualify repeated non-admitted flame creation without weakening admitted ownership guards; add explicit fault/blocked-selection diagnostics, with damage disabled.')
    (STEP / 'LIVE-REVIEW.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status=result['status'], transactions=len(transactions), av_calls=len(av_calls),
        matched_health_callbacks=12, installed_files_verified=len(installed), protected_files_verified=len(protected),
        secondary_effect_coverage_verified=False, sha256=EXPECTED)))


if __name__ == '__main__':
    main()

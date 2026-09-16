"""Build a disabled reference packet; never writes game files or native sources."""
from pathlib import Path
import hashlib
import html
import json
import math
import shutil
from inspect_plugin import records, fields

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3m'
RELEASE = ROOT / 'release/NVO-Combat-Packet-3M-Armour-Contract'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(name, data):
    (PACKET / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

# Pin the current baseline without requiring another process launch or playtest.
previous = read(ROOT / 'source/combat/step3l/RESULT.json')
protected = [f for f in previous['verified_files'] if Path(f['path']).name.lower() in {
    'nvo.esm', 'nvoflightpilot.esp', 'nvocombatcore.dll', 'nvocombatcore.pdb',
    'nvoflightphysics.ini', 'nvoflightpreview.ini'}]
assert len(protected) == 6
for f in protected:
    assert sha(Path(f['path'])) == f['sha256'], f'Baseline changed: {f["path"]}'

family_rows = [
    ('kinetic_single', 'Bullets, AP, HP and slugs', 'ballistic_trajectory',
     ['kinetic_penetration', 'transmitted_blunt'],
     ['exact_ammo_construction', 'mass_kg', 'diameter_m', 'supported_contact_velocity_mps'],
     'Limited named pilot flight active; damage replacement absent',
     'Known .308 AP/HP identity does not establish variant construction or penetration'),
    ('kinetic_multiple', 'Shotgun pellets / multiple kinetic carriers', 'per_carrier_ballistic_trajectory',
     ['kinetic_penetration', 'transmitted_blunt'],
     ['mass_kg_per_pellet', 'live_carrier_identity', 'supported_contact_velocity_mps'],
     'Previous separate-carrier observations; full application not verified',
     'No total-cartridge mass per pellet and no same-frame merging'),
    ('laser', 'Laser, Tri-beam and laser-like pulses', 'verified_beam_or_pulse',
     ['thermal_ablation'], ['pulse_dose_nvo_units', 'range_delivery_curve', 'component_identity'],
     'Tri-beam carriers observed in 2B4; NVO laser transport/damage replacement absent',
     'No bullet drag/gravity/mass and no repeated visual-callback damage'),
    ('plasma', 'Plasma and Multiplas', 'finite_carrier_keep_supported_native_transport',
     ['plasma_thermal_ablation', 'optional_authored_impact'],
     ['payload_dose_nvo_units', 'travel_decay_curve', 'component_identity'],
     'Multiplas creations and one actor context observed in 2B4; replacement absent',
     'Do not convert travel speed into bullet energy or assume an explosion'),
    ('flame', 'Flame / continuous heat', 'verified_exposure_intervals',
     ['external_heat', 'separate_optional_burn'],
     ['dose_rate_nvo_units_per_game_second', 'exposure_game_seconds', 'interval_identity'],
     'Timed-exposure adapter/application not verified',
     'No FPS scaling or duplicate emitter/direct-effect damage'),
    ('explosive', 'Rockets, missiles, grenades and mines', 'family_specific_carrier_fuse_and_blast',
     ['optional_direct_impact', 'blast', 'verified_fragments_only', 'authored_secondary_effects'],
     ['explosion_identity', 'victim_application_identity', 'blast_exposure_profile', 'verified_parent_if_linked'],
     'Blast observations exist; parent/component application ownership not verified',
     'Impact and blast remain distinct; do not create extra fragments or duplicate engine AoE'),
    ('thrown_piercing', 'Thrown objects, darts and modded bolts', 'explicit_kinetic_or_payload_profile',
     ['piercing', 'cutting', 'blunt', 'conditional_wound_payload'],
     ['exact_profile', 'supported_contact', 'construction_or_payload'],
     'No family authority adapter verified',
     'Wound-carried poison needs penetration; gas/contact exposure needs a different profile'),
    ('electrical', 'Electrical effects', 'authored_pulse_or_exposure',
     ['electrical', 'mechanical_response'], ['dose_profile', 'component_identity', 'anatomy_response'],
     'No family authority adapter verified', 'Robot response is mechanical, not biological bleeding'),
    ('radiation', 'Radiation / radioactive payloads', 'authored_exposure_or_payload',
     ['radiation_dose'], ['dose_profile', 'exposure_route', 'component_identity'],
     'No family authority adapter verified', 'Radiation dose is not automatically a direct HP delta'),
    ('exotic', 'Sonic, alien and other explicitly classified effects', 'explicit_custom_adapter',
     ['authored_supported_channels'], ['exact_profile', 'verified_delivery', 'effect_disposition'],
     'No family authority adapter verified', 'Unknown effect families stay with the engine'),
    ('melee', 'Fists, cutting, piercing and blunt melee', 'verified_melee_contact',
     ['cutting', 'piercing', 'blunt'], ['contact_identity', 'authored_threat', 'proficiency_and_condition'],
     'Fists/Super Sledge observed; punch net HP after reload verified; replacement absent',
     'No invented firearm energy and no extra OnHit DamageAV'),
    ('unknown', 'Unclassified equipment/effects', 'engine_owned', [], [],
     'Existing behaviour retained', 'Never classify by display name alone'),
]
families = {'schema': 1, 'packet': '3M', 'status': 'design_reference_not_runtime_configuration',
            'all_damage_replacement_disabled': True, 'families': []}
for key, label, transport, channels, required, current, rule in family_rows:
    families['families'].append({'id': key, 'label': label, 'planned_transport': transport,
        'planned_channels': channels, 'required_inputs': required, 'current_evidence': current,
        'critical_rule': rule, 'damage_authority_implemented': False,
        'until_supported': 'existing_engine_damage', 'activation_gate': 'family_specific_adapter_and_application_checkpoint'})
write('PROJECTILE-FAMILIES.json', families)

owners = [
    ('direct_health_limb_wear', 'engine', 'nvo_resolver_and_single_application_adapter',
     'Supported scope only; original path if rejected before writes; no replay after partial NVO application'),
    ('health_formula_gmsts', 'user_NVO_records', 'retain_user_NVO_records',
     'Maximum-health tuning remains independent of incident damage; no balance changes here'),
    ('difficulty_health_scaling', 'engine_receiver_based_table', 'proposed_neutral_GMSTs_plus_separate_NVO_presets',
     'Not applied; global neutralization changes unsupported attacks too and needs explicit policy/rollback'),
    ('vats_player_protection', 'existing_engine_or_provider', 'remove_extra_protection_for_supported_NVO_rules',
     'Exact consumer and full VATS path still need tracing; ten difficulty GMSTs do not settle it'),
    ('vanilla_DT_DR_and_minimum_damage_floor', 'engine_and_existing_perks', 'replace_for_admitted_components',
     'Do not calculate custom protection on top of an already-armour-reduced value; trace selected boundary'),
    ('location_multipliers', 'engine_body_part_rules', 'explicit_anatomy_profile',
     'Verified actual hit region only; requested VATS aim is not a substitute'),
    ('critical_health_and_damaging_effects', 'engine_and_perk_effects', 'classified_NVO_disposition',
     'No penetrating effect through a failed penetration decision; unknown damaging effect rejects replacement'),
    ('critical_visual_audio_effects', 'engine_presentation', 'retain_when_side_effect_free',
     'A visual callback is not permission for an extra health application'),
    ('ammo_damage_DT_DR_effects', 'engine_ammo_effects', 'explicit_construction_or_dose_profile_for_admitted_hits',
     'AP/HP/energy charge identities retained; do not apply both native profile and vanilla multiplier'),
    ('ammo_cost_weapon_wear_reload', 'engine', 'retain_except_explicitly_owned_components',
     'Ammo consumption is not projectile mass; future overcharge effects must not duplicate wear'),
    ('weapon_condition_proficiency_perks', 'engine_and_perk_rules', 'per_effect_disposition_required',
     'Preserve intended progression once; unresolved modifiers stay unsupported'),
    ('poison', 'engine_payload_or_effect', 'wound_payload_requires_penetration_other_exposure_separate',
     'Differentiate dart/coating from gas/contact exposure; no generic all-poison penetration rule'),
    ('blast_and_fragments', 'engine', 'separate_identified_components',
     'Never treat blast as another direct projectile; preserve source and victim application identity'),
    ('bleeding_and_burn_ticks', 'engine_or_donor_if_active', 'later_attributed_injury_service',
     'One continuing-effect owner; audit actual donor loaders before activation'),
    ('baron_caps_callback', 'ALTRichKidHit_and_two_registration_sites', 'retire_without_replacement_now',
     'Approved design; compiled callback and saved-session retirement pending; do not port mechanic'),
    ('flight_gravity_drag', 'limited_NVO_bullet_pilot_and_engine_other_families', 'family_specific_flight_owner',
     'Fix admission-before-substitution; no bullet flight applied to lasers/plasma/flame by type alone'),
    ('diagnostics', 'NVO_observers', 'observation_only',
     'Logging limits/failure cannot determine damage admission, identity or output'),
]
write('MODIFIER-OWNERSHIP.json', {'schema': 1, 'status': 'design_only', 'runtime_changes': False,
    'modifiers': [{'id': key, 'current_owner': current, 'planned_disposition': future, 'constraint': rule}
                  for key, current, future, rule in owners]})

donor_path = ROOT / 'source/combat/step3a/NVO-Flight-Pilot.json'
donor = read(donor_path)
profile_rows = []
for p in donor['profiles']:
    fi = p['flight_inputs']
    mass = fi['mass_grain'] * 0.00006479891
    diameter = fi['diameter_in'] * 0.0254
    assert math.isclose(mass, p['preview_only']['mass_kg'], rel_tol=1e-12)
    assert math.isclose(diameter, p['preview_only']['diameter_m'], rel_tol=1e-12)
    profile_rows.append({'id': p['id'], 'family': 'kinetic_single', 'match': p['match'],
        'enabled': False, 'mass_kg': mass, 'diameter_m': diameter,
        'construction': None, 'material_response_curve': None, 'injury_conversion_curve': None,
        'impact_velocity_mps': None, 'runtime_unit_calibration': 'pending',
        'contact_authority': 'pending', 'provenance': p['donor_source'],
        'note': 'Source-backed donor tuning; not an activated armour/damage profile'})
for family, parameters in (
    ('laser', {'pulse_dose_nvo_units': None, 'range_delivery_curve': None}),
    ('plasma', {'payload_dose_nvo_units': None, 'travel_decay_curve': None}),
    ('flame', {'dose_rate_nvo_units_per_game_second': None, 'exposure_interval_adapter': None}),
    ('explosive', {'blast_exposure_profile': None, 'component_identity_adapter': None}),
):
    profile_rows.append({'id': f'{family}-template', 'family': family, 'enabled': False,
        'match': None, 'material_response_curve': None, 'injury_conversion_curve': None,
        **parameters, 'note': 'Intentionally incomplete; must reject runtime activation'})
write('PROFILES.reference.json', {'schema': 1, 'status': 'reference_only_no_installed_reader',
    'damage_replacement': False, 'units': {'mass': 'kg', 'length': 'm', 'velocity': 'm/s',
    'kinetic_energy': 'J', 'fictional_energy_payload': 'authored_NVO_dose_units', 'time': 'simulated_game_seconds'},
    'source': {'path': str(donor_path.relative_to(ROOT)), 'sha256': sha(donor_path),
               'donor_archive': read(ROOT / 'source/combat/step3a/PROVENANCE.json')['archive']},
    'profiles': profile_rows})

# Extract deployed source and text references, never rewrite the plugin.
esm = GAME / 'Data/NVO.esm'
names = {'ALTRichKidHit', 'ALTBackRichKidUDF', 'ALTQscript'}
scripts, references, descriptions = [], [], []
for kind, form, flags, payload in records(esm.read_bytes()):
    parts = dict(fields(payload))
    edid = parts.get('EDID', b'').rstrip(b'\0').decode('cp1252')
    source = parts.get('SCTX', b'').rstrip(b'\0').decode('cp1252')
    if kind == 'SCPT' and edid in names:
        scripts.append({'editor_id': edid, 'file_local_form': f'{form:08X}',
            'source': source, 'compiled_bytes': len(parts.get('SCDA', b'')),
            'compiled_sha256': hashlib.sha256(parts.get('SCDA', b'')).hexdigest(),
            'retirement_applied': False})
    if source and ('ALTRichKidHit' in source or 'Brahmin Baron' in source):
        references.append({'editor_id': edid, 'file_local_form': f'{form:08X}',
            'lines': [{'number': i, 'text': line} for i, line in enumerate(source.splitlines(), 1)
                      if 'ALTRichKidHit' in line or 'Brahmin Baron' in line]})
    for tag in ('FULL', 'DESC'):
        text = parts.get(tag, b'').rstrip(b'\0').decode('cp1252', errors='replace')
        if 'Brahmin Baron' in text or (('RichKid' in edid or 'Baron' in edid) and text):
            descriptions.append({'type': kind, 'editor_id': edid, 'file_local_form': f'{form:08X}',
                                 'field': tag, 'text': text})
assert {s['editor_id'] for s in scripts} == names
write('CURRENT-BARON-RECORDS.json', {'esm_sha256': sha(esm),
    'id_note': 'File-local master prefix, not runtime load-order FormID; use original Editor ID in GECK',
    'compiled_runtime_retirement': False, 'scripts': scripts,
    'source_references': references, 'descriptions': descriptions})

source_paths = [
    'native/NVOCombatCore/src/FlightPreview.cpp', 'native/NVOCombatCore/src/FlightImpactModel.inl',
    'native/NVOCombatCore/include/HitTransaction.hpp', 'native/NVOCombatCore/include/CurrentHit.hpp',
    'native/NVOCombatCore/config/NVOFlightPhysics.ini', 'native/NVOCombatCore/config/NVOFlightPreview.ini',
    'source/combat/step3a/NVO-Flight-Pilot.json', 'source/combat/step3a/PROVENANCE.json',
    'source/combat/step2/REVIEW-7-reload-melee-energy.md',
    'source/combat/review/ULTRA-317-FINDINGS.json', 'source/combat/step3h/CONTRACT.md',
    'source/combat/step3k/CONTRACT.md', 'source/combat/step3l/ENGINE-TRACE.md',
]
write('DECISIONS.json', {'date': '2026-09-16', 'packet': '3M',
    'approved_by_user': ['prepare_armour_input_and_modifier_contract',
                         'retire_baron_caps_damage_not_migrate',
                         'plasma_laser_and_other_projectiles_required_in_final_system'],
    'queued_later': ['consistent_review_of_all_backgrounds', 'choose_baron_replacement_benefit'],
    'proposed_not_activated': ['neutral_difficulty_damage_GMSTs', 'resource_AI_recovery_difficulty_presets'],
    'runtime_changes': [], 'next_requires_user_go_ahead': '3N disabled resolver plus complete Baron retirement scripts'})

rows_html = '\n'.join('<tr><td>' + html.escape(f['label']) + '</td><td>'
                      + html.escape(f['critical_rule']) + '</td></tr>' for f in families['families'])
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NVO · Packet 3M — Armour &amp; projectile rules</title>
<style>body{max-width:1040px;margin:42px auto;padding:0 24px;background:#111d19;color:#e2e9df;font:17px/1.6 system-ui}h1{font-size:34px}h2{font-size:23px;color:#cee0b0}a{color:#c2df9e}table{border-collapse:collapse;width:100%}th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #46584c}th{color:#cee0b0}.note{background:#203126;border-left:3px solid #b0cb85;padding:16px}small{color:#b6c3b6}</style>
<p><small>NVO COMBAT · PACKET 3M · DESIGN / REFERENCE</small></p>
<h1>Armour rules for every attack family</h1>
<p>Prepared: inputs, coverage/material response, ownership of modifiers and safe unsupported handling. <strong>Nothing is installed or enabled by this packet.</strong></p>
<div class="note">No GECK compilation or gameplay test now. Native320 stays installed. The Brahmin Baron ability is marked for retirement but remains in the compiled ESM until the script packet is compiled and saved.</div>
<h2>Your decisions</h2><ul><li>Remove the Baron’s caps-based damage and instant-kill callback. Choose a replacement later.</li><li>Review all starting backgrounds for consistency with NVO in the later background pass.</li><li>Include lasers, plasma, flame, explosives and unusual projectiles with their own rules. Current pilot flight covers classified bullets; other families keep existing engine behaviour until their adapters pass.</li></ul>
<h2>Projectile and attack rules</h2><table><tr><th>Family</th><th>Required distinction</th></tr>''' + rows_html + '''</table>
<h2>What the resolver must know</h2><p>The actual hit region, armour coverage/material/condition, source and target, exact ammunition and component identity, and trustworthy family-specific impact data. Unknown inputs retain engine behaviour. A helmet protects its mapped head region independently of body armour. Robots receive mechanical injuries.</p>
<p>Two kinetic examples reuse the existing source-backed BallistX mass data. They remain disabled until units, contact data and material response are supported. Energy-weapon doses and armour thresholds are intentionally unset; no fake values have been installed.</p>
<h2>Next packet, with your approval</h2><p><strong>3N: implement a disabled pure resolver and prepare complete Baron retirement scripts.</strong> Offline fixtures check calculations and rejection rules without changing game health. Copy-button scripts will let you compile the original GECK records and retire the legacy ability. Full damage activation comes after targeted review and supported-path checks.</p>
<p><a href="README.md">Packet notes</a> · <a href="CONTRACT.md">Full contract</a> · <a href="BRAHMIN-RETIREMENT.md">Baron removal scope</a> · <a href="PROJECTILE-FAMILIES.json">Family coverage</a> · <a href="MODIFIER-OWNERSHIP.json">Modifier ownership</a></p>
<p><small>Reversal: none required. Workspace documents and reference data only; no game launch, build, install or settings change.</small></p></html>'''
(PACKET / 'START-HERE.html').write_text(page, encoding='utf-8')

# Structural checks of this packet, not game testing or solver validation.
assert len({f['id'] for f in families['families']}) == len(families['families'])
assert all(not f['damage_authority_implemented'] for f in families['families'])
assert all(not p['enabled'] for p in profile_rows)
assert len(scripts) == 3 and all(s['compiled_bytes'] > 0 for s in scripts)
write('PACKET-RESULT.json', {'packet': '3M', 'status': 'prepared_design_reference',
    'installed_native_version': 320, 'damage_replacement': False, 'pre_damage_gate': 'HOLD',
    'runtime_changes': False, 'native_compilation': False, 'gameplay_test': False,
    'baron_retired_in_runtime': False, 'family_contracts': len(families['families']),
    'reference_profiles': len(profile_rows), 'installed_baseline_verified': protected,
    'source_pins': [{'path': p, 'sha256': sha(ROOT / p)} for p in source_paths],
    'checks': ['six_installed_baseline_hashes_match_3L', 'all_damage_authority_flags_false',
               'all_reference_profiles_disabled', 'unique_family_ids',
               'donor_unit_conversions_match_3A', 'three_original_Baron_scripts_found_with_compiled_data'],
    'next': 'ask_before_3N_disabled_resolver_and_Baron_retirement_scripts'})

files = ['README.md', 'CONTRACT.md', 'BRAHMIN-RETIREMENT.md', 'PROJECTILE-FAMILIES.json',
         'MODIFIER-OWNERSHIP.json', 'PROFILES.reference.json', 'CURRENT-BARON-RECORDS.json',
         'DECISIONS.json', 'PACKET-RESULT.json', 'START-HERE.html']
RELEASE.mkdir(exist_ok=True)
for name in files:
    shutil.copy2(PACKET / name, RELEASE / name)
(RELEASE / 'MANIFEST.json').write_text(json.dumps({'packet': '3M', 'install_files': [],
    'files': [{'name': name, 'sha256': sha(RELEASE / name)} for name in files]}, indent=2) + '\n', encoding='utf-8')

status = '''
## Current checkpoint: Packet 3M armour/projectile contract prepared; native320 unchanged

2026-09-16: user approved continuing from3L. Prepared source/combat/step3m and release/NVO-Combat-Packet-3M-Armour-Contract: required hit/armour/physical inputs, family-specific channels, modifier owners, admission/exact-once/fallback and targeted gates. Twelve attack-family entries explicitly distinguish final scope from implemented support. Laser/plasma/flame/explosive authority is NOT implemented; existing engine behaviour remains. Prior2B4 Tri-beam/Multiplas observations reused without retesting. Two kinetic mass/diameter examples reuse3A BallistX5.4 provenance; energy doses/material thresholds unset. Units70/metre/contact/first-segment/region/admission gates still open. No new NVSE command or runtime JSON reader exists.

User decision: RETIRE BrahminBaron caps-damage/instant-kill ability, do not migrate it. Choose replacement later; review all starts for NVO consistency later. Actual3M installed ESM unchanged and callback still ACTIVE if registered. CURRENT-BARON-RECORDS.json extracts three current original scripts and description/source references. Next implementation must neutralize callback, remove registrations in ALTBackRichKidUDF+ALTQscript, handle existing saves/registrations, update descriptions, preserve variables/IDs/wealth/equipment/location. User compiles originals; no fake closure before saved compiled audit. 317-02 owner decision resolved, runtime retirement pending.

Difficulty neutralization/presets remain proposed, no GMST/INI changes. Contract notes global neutralization also affects unsupported attacks; cannot claim identical fallback after such a future change. VATS player protection/criticals/DT-DR/ammo effects each need one owner. Health formula preserved. Medical detail later; powerful familiar medicines, permadeath design with no save restrictions.

No native source/game edits/build/install/launch/GECK/test in3M. Six installed baseline assets hash-match3L. Damage replacementOFF and pre-damageHOLD. Structural reference checks only. NEXT PROPOSED3N: implement disabled pure resolver with meaningful offline fixtures and provide complete copy-button original Baron retirement scripts. ASK before preparing3N. Reuse Ultra317; targeted delta review before activation, no repeatfullaudit or oldstress/miss tests.

'''
for rel in ('STATUS.md', 'source/combat/README.md'):
    path = ROOT / rel
    original = path.read_bytes()
    marker = b'## Current checkpoint: Packet 3M armour/projectile contract prepared; native320 unchanged'
    if marker not in original:
        end = original.index(b'\n') + 1
        path.write_bytes(original[:end] + status.replace('\n', '\r\n').encode('utf-8') + original[end:])
print(json.dumps({'release': str(RELEASE), 'families': len(family_rows), 'profiles': len(profile_rows),
                  'baron_scripts': [s['editor_id'] for s in scripts],
                  'baron_descriptions': descriptions, 'runtime_changes': False}))

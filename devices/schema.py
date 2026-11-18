"""Device identity and source-checked, language-independent hardware facts."""
import re
import string
import struct
import zlib

from io_utils import digest, localized, read_json, require, safe_path

SECTIONS = ('Controller', 'Connectivity', 'Inputs', 'Outputs', 'Power', 'Accessories')
KINDS = {'integer': int, 'number': (int, float), 'string': str, 'boolean': bool, 'strings': list}


def normalize(text):
    return ' '.join(text.replace('**', '').replace('`', '').split())


def value_text(fact):
    if fact['status'] == 'unknown':
        return 'unknown'
    value = fact['value']
    return ', '.join(value) if isinstance(value, list) else str(value)


def validate_fact(root, identity, fact):
    require(isinstance(fact, dict) and {'kind', 'value', 'status', 'label', 'section'} <= fact.keys(), f'{identity}: incomplete typed fact')
    require(fact['section'] in SECTIONS, f'{identity}: invalid fact section')
    localized(fact['label'], identity + '/label')
    require(fact['kind'] in KINDS, f'{identity}: unsupported fact type')
    require(fact['status'] in ('documented', 'measured', 'unknown'), f'{identity}: invalid fact status')
    if fact['status'] == 'unknown':
        require(fact['value'] is None, f'{identity}: unknown facts cannot assert a value')
        localized(fact.get('reason'), identity + '/reason')
        return
    value = fact['value']
    require(isinstance(value, KINDS[fact['kind']]), f'{identity}: value/type mismatch')
    require(not isinstance(value, str) or bool(value.strip()), f'{identity}: empty fact value')
    if fact['kind'] in ('integer', 'number'):
        require(type(value) is not bool and value >= 0, f'{identity}: invalid numeric fact')
        require(isinstance(fact.get('unit'), str) and fact['unit'], f'{identity}: numeric unit required')
    if fact['kind'] == 'strings':
        require(value and all(isinstance(item, str) and item for item in value), f'{identity}: nonempty string values required')
    source = fact.get('source', {})
    require(isinstance(source, dict) and {'path', 'template'} <= source.keys(), f'{identity}: source assertion required')
    tokens = list(string.Formatter().parse(source['template']))
    require([field for _, field, _, _ in tokens if field is not None] == ['value'] and all(not spec and not conversion for _, _, spec, conversion in tokens), f'{identity}: source assertion must use only {{value}}')
    text = normalize(safe_path(root, source['path']).read_text())
    for item in value if isinstance(value, list) else [value]:
        assertion = normalize(source['template'].format(value=item))
        require(assertion in text, f'{identity}: value contradicts cited source assertion: {assertion}')


def render_text(device, text, locale):
    fields = {key: value_text(fact) + (' ' + fact['unit'] if fact.get('unit') and fact['status'] != 'unknown' else '') for key, fact in device['facts'].items()}
    return text[locale].format_map(fields)


def validate(root, device):
    did = device['id']
    require(device.get('schema_version') == 3, f'{did}: unsupported device schema_version')
    require(isinstance(device.get('variants'), dict), f'{did}: device schema_version 3 requires variants object')
    require('targets' not in device and 'specs' not in device, f'{did}: Target indexes and translated facts must be derived')
    require(isinstance(device.get('name'), str) and device['name'], f'{did}: name required')
    require(device.get('maintenance') and device.get('maturity') in ('experimental', 'stable', 'deprecated'), f'{did}: separate owner/maturity required')
    require(isinstance(device.get('facts'), dict) and device['facts'], f'{did}: typed facts required')
    for key, fact in device['facts'].items():
        require(re.fullmatch(r'[a-z][a-z0-9_]*', key), f'{did}: invalid fact id')
        validate_fact(root, f'{did}/{key}', fact)
    require(set(f['section'] for f in device['facts'].values()) == set(SECTIONS), f'{did}: missing specification section')
    for field in ('overview', 'scenarios', 'physical_description'):
        localized(device.get(field), f'{did}/{field}')
        fields = []
        for locale in ('en', 'zh_CN'):
            parsed = list(string.Formatter().parse(device[field][locale]))
            require(all(not spec and not conversion for _, _, spec, conversion in parsed), f'{did}/{field}: unsupported template format')
            names = {name for _, name, _, _ in parsed if name is not None}
            require(names <= device['facts'].keys(), f'{did}/{field}: unknown fact placeholder')
            fields.append(names)
        require(fields[0] == fields[1], f'{did}/{field}: bilingual fact references differ')
    require(isinstance(device.get('revision'), str) and device['revision'], f'{did}: explicit revision required')
    require(isinstance(device.get('unknowns'), list) and isinstance(device.get('conflicts'), list), f'{did}: explicit unknowns/conflicts required')
    for item in device['unknowns']:
        localized(item, f'{did}/unknown')
    for conflict in device['conflicts']:
        localized(conflict['resolution'], f'{did}/conflict')
        safe_path(root, conflict['source'])
    require(device.get('references'), f'{did}: references required')
    for ref in device['references']:
        safe_path(root, ref)
    require(all(f['status'] == 'unknown' or f['source']['path'] in device['references'] for f in device['facts'].values()), f'{did}: fact source outside reference closure')
    variants = device.get('variants', {})
    require(isinstance(variants, dict), f'{did}: variants must be an object')
    for name, variant in variants.items():
        require(re.fullmatch(r'[a-z][a-z0-9_-]*', name) and isinstance(variant, dict), f'{did}: invalid hardware variant')
        localized(variant.get('label'), f'{did}/{name}/label')
        require(variant.get('source') in device['references'], f'{did}/{name}: variant source outside reference closure')
        facts = variant.get('facts')
        require(isinstance(facts, dict) and facts and 'compatible_revisions' in facts, f'{did}/{name}: variant facts/revision compatibility required')
        require(isinstance(facts['compatible_revisions'], dict) and facts['compatible_revisions'].get('kind') == 'strings', f'{did}/{name}: revision compatibility must be a sourced list or unknown')
        for key, fact in facts.items():
            require(re.fullmatch(r'[a-z][a-z0-9_]*', key), f'{did}/{name}: invalid fact id')
            validate_fact(root, f'{did}/{name}/{key}', fact)
            require(fact['status'] == 'unknown' or fact['source']['path'] in device['references'], f'{did}/{name}: fact source outside reference closure')
    require(isinstance(device.get('vendor_sources'), list) and all(url.startswith('https://') for url in device['vendor_sources']), f'{did}: invalid vendor sources')
    acceptance = read_json(safe_path(root, f'devices/{did}/tests/acceptance.json'))
    require(acceptance.get('schema_version') == 2 and acceptance.get('device') == did, f'{did}: invalid acceptance schema')
    require(isinstance(acceptance.get('cases'), list) and acceptance['cases'], f'{did}: physical acceptance cases required')
    identities = set()
    for case in acceptance['cases']:
        require(case.get('id') and case['id'] not in identities and case.get('procedure') and case.get('expected') and case.get('source'), f'{did}: incomplete/duplicate acceptance case')
        identities.add(case['id'])
        safe_path(root, case['source'])
    assets = read_json(safe_path(root, device['assets']))
    require(assets.get('schema_version') == 1 and assets.get('device') == did and isinstance(assets.get('assets'), list), f'{did}: invalid asset manifest')
    for asset in assets['assets']:
        require({'path', 'source', 'license', 'sha256', 'revision', 'width', 'height', 'alpha'} <= asset.keys(), f'{did}: incomplete asset')
        image = safe_path(root, asset['path'])
        require(asset['license'] not in ('', 'unknown') and asset['source'] and asset['revision'] == device['revision'] != 'unknown', f'{did}: asset provenance/revision required')
        require(digest(image) == asset['sha256'], f'{did}: asset hash mismatch')
        require(image.suffix.lower() == '.png', f'{did}: unsupported image validator (PNG required)')
        raw = image.read_bytes()
        require(len(raw) >= 33 and raw[:8] == b'\x89PNG\r\n\x1a\n' and raw[12:16] == b'IHDR', f'{did}: invalid PNG')
        offset, chunks = 8, []
        while offset < len(raw):
            require(offset + 12 <= len(raw), f'{did}: truncated PNG')
            length = struct.unpack('>I', raw[offset:offset+4])[0]
            end = offset + 8 + length
            require(end + 4 <= len(raw) and zlib.crc32(raw[offset+4:end]) == struct.unpack('>I', raw[end:end+4])[0], f'{did}: invalid PNG checksum/length')
            chunks.append(raw[offset+4:offset+8]); offset = end + 4
        require(chunks[-1:] == [b'IEND'] and b'IDAT' in chunks, f'{did}: incomplete PNG')
        width, height = struct.unpack('>II', raw[16:24])
        require((width, height) == (asset['width'], asset['height']) and width > 0 and height > 0, f'{did}: image dimensions mismatch')
        require(type(asset['alpha']) is bool and (raw[25] in (4, 6)) == asset['alpha'], f'{did}: PNG alpha claim mismatch')

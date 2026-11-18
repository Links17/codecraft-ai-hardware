"""Deterministic English engineering views; README files alone are bilingual."""
import json
from pathlib import Path
import re

from io_utils import object_digest, read_json, require

BEGIN = '<!-- CODECRAFT_INDEX_START -->'
END = '<!-- CODECRAFT_INDEX_END -->'


def paired(path, en, zh):
    path = Path(path)
    require(path.name == 'README.md', 'Only README.md may have a translated document')
    cn = path.with_name(path.stem + '.zh_CN.md')
    return {str(path): f'<p align="right"><strong>English</strong> · <a href="{cn.name}">简体中文</a></p>\n\n'+en.rstrip()+'\n',
            str(cn): f'<p align="right"><a href="{path.name}">English</a> · <strong>简体中文</strong></p>\n\n'+zh.rstrip()+'\n'}


def matrix(catalog):
    return {'include': [{'id': target['id'], 'device': target['device'], 'platform': target['platform'],
                         'toolchain': target['toolchain']['version'], 'chip': target['toolchain'].get('target', ''),
                         **catalog.platforms[target['platform']]['ci']} for target in catalog.targets.values()]}


def views(c):
    outputs = {}
    stamp = object_digest([c.devices, c.platforms, c.targets, c.capabilities])
    rows = ['| Device | Target | Implementations | Build + project | Device |', '| --- | --- | --- | --- | --- |']
    overview = ['# Device discovery', '', 'Generated from Device Overviews; edit the owning records.', '']
    sources = ['# Vendor source index','','Generated references. Read primary sources before relying on facts.','']
    compatibility = []
    for did, device in c.devices.items():
        tids = c.device_targets(did)
        targets = [c.targets[tid] for tid in tids]
        caps = sorted({b['id'] for t in targets for b in t['interfaces']})
        states = {tid: c.support(tid) for tid in tids}
        levels = ', '.join(state['level'] for state in states.values())
        physical = ', '.join(state['device'] for state in states.values())
        records = sorted({path for state in states.values() for path in state['records']})
        rows.append(f'| [{device["name"]}](devices/{did}/AGENTS.md) | {", ".join(tids)} | {", ".join(caps)} | {levels} | {physical} |')
        text = lambda field: c.device_schema.render_text(device, device[field], 'en')
        overview += [f'## [{device["name"]}]({did}/AGENTS.md)','',text('overview'),'',text('scenarios'),'']
        intro = 'Generated from device.json. Edit typed facts and regenerate; never edit this view.'
        body = [f'# {device["name"]}','',intro,'','## Overview','',text('overview'),'',text('scenarios'),'',text('physical_description'),'',f'Revision: {device["revision"]}','', '## Specs','']
        for section in c.device_schema.SECTIONS:
            body += [f'### {section}','']
            for fact in device['facts'].values():
                if fact['section'] != section:
                    continue
                value = c.device_schema.value_text(fact)
                if fact.get('unit') and fact['status'] != 'unknown':
                    value += ' '+fact['unit']
                detail = fact['reason']['en'] if fact['status'] == 'unknown' else f'[{fact["status"]}](../../{fact["source"]["path"]})'
                body += [f'- {fact["label"]["en"]}: **{value}** — {detail}']
            body += ['']
        if device.get('variants'):
            body += ['## Hardware variants', '', 'Panel/assembly choices do not identify a physical PCB revision.', '']
            for name, variant in device['variants'].items():
                body += [f'### {name}: {variant["label"]["en"]}', '', f'[Source](../../{variant["source"]})', '']
                for fact in variant['facts'].values():
                    detail = fact['reason']['en'] if fact['status'] == 'unknown' else f'[{fact["status"]}](../../{fact["source"]["path"]})'
                    body += [f'- {fact["label"]["en"]}: **{c.device_schema.value_text(fact)}** — {detail}']
                body += ['']
        body += ['## Targets',''] + [f'- [{tid}](../../{c.targets[tid]["path"]}/README.md)' for tid in tids]
        body += ['', '## Evidence', '', f'Build/project: {levels}. Device: {physical}. Maintenance: {device["maintenance"]}. Maturity: {device["maturity"]}.', '']
        body += ['- '+item['en'] for item in device['unknowns']]
        body += ['', '## Source conflicts','']
        body += [f'- {item["resolution"]["en"]} [Source](../../{item["source"]})' for item in device['conflicts']] or ['No additional resolved conflict recorded.']
        body += ['', '## Assets','', '[Manifest](assets/manifest.json)', '']
        assets = read_json(c.root/device['assets'])['assets']
        body += [f'- [{Path(asset["path"]).name}](../../{asset["path"]})' for asset in assets] or ['No verified redistributable image is registered.']
        body += ['', '## References',''] + [f'- [{Path(ref).name}](../../{ref})' for ref in [*device['references'],*records]]
        body += ['', '## Vendor links',''] + [f'- [Source {i+1}]({url})' for i,url in enumerate(device['vendor_sources'])]
        outputs[f'devices/{did}/AGENTS.md'] = '\n'.join(body).rstrip()+'\n'
        sources += [f'## {device["name"]}','', f'[References](../devices/{did}/reference/README.md)','']+[f'- [Source {i+1}]({url})' for i,url in enumerate(device['vendor_sources'])]+['']
        for target in targets:
            for binding in target['interfaces']:
                compatibility.append({'target':target['id'],'interface':binding['id'],
                                      'operations':binding['operations'],'configuration':binding['configuration'],'resources':binding['resources'],
                                      'verification':states[target['id']]['interfaces'][binding['id']]})
    outputs['devices/AGENTS.md'] = '\n'.join(overview).rstrip()+'\n'
    outputs['docs/vendor-sources.md'] = '\n'.join(sources).rstrip()+'\n'
    outputs['docs/inventory.md'] = '# Native interface matrix\n\nGenerated implementations and scoped evidence.\n\n'+'\n'.join(rows).replace('(devices/','(../devices/')+'\n'
    links = ['\nPlatforms: '+', '.join(f'[{pid}](platforms/{pid}/AGENTS.md)' for pid in c.platforms), '\nCloud Skill Capabilities: [contracts](capabilities/AGENTS.md)']
    links += [f'- [{cid}](capabilities/{cid}/AGENTS.md) · {cap["version"]} · '+', '.join(p['skill']['id'] for p in c.cloud().providers.values() if p['capability']==cid)+' · API execution: not_run' for cid,cap in c.capabilities.items()]
    block = BEGIN+f'\n<!-- source_sha256: {stamp} -->\n\n'+'\n'.join(rows+links)+'\n'+END
    current = (c.root/'AGENTS.md').read_text()
    if BEGIN not in current or END not in current:
        raise ValueError('AGENTS.md: missing generated markers')
    outputs['AGENTS.md'] = re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END), lambda _:block, current, flags=re.S)
    outputs['platforms/interface-matrix.json'] = json.dumps({'schema_version':2,'bindings':compatibility},ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    outputs['capabilities/matrix.json'] = json.dumps({'schema_version':2,**c.cloud().describe()},ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    outputs['.github/target-matrix.json'] = json.dumps(matrix(c),ensure_ascii=False,indent=2)+'\n'
    return outputs


def generate(catalog, check=False):
    changed = []
    for relative, text in views(catalog).items():
        path = catalog.root/relative
        if not path.exists() or path.read_text() != text:
            changed.append(relative)
            if not check:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(text)
    return changed
